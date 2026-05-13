from django.db import connection, transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CarbonBudget, Emissions, Interventions, Overview, Scenarios, Sequestration
from .serializers import (
    CarbonBudgetSerializer,
    EmissionsSerializer,
    InterventionsSerializer,
    OverviewSerializer,
    ScenariosSerializer,
    SequestrationSerializer,
    get_live_columns,
)


def _safe_identifier(name: str) -> bool:
    return bool(name) and name.replace("_", "").isalnum()


def _live_columns(table: str):
    return get_live_columns(table)


class DynamicModelViewSet(viewsets.ViewSet):
    """
    Fully dynamic ViewSet backed by raw SQL + live PRAGMA introspection.

    Endpoints per resource:
      GET    /           list all rows
      POST   /           create row
      GET    /<vlcode>/  retrieve one row
      PUT    /<vlcode>/  full replace
      PATCH  /<vlcode>/  partial update
      DELETE /<vlcode>/  delete

      GET    /schema/         live column list
      POST   /add-field/      { "field_name": "x" }   → adds REAL column
      POST   /remove-field/   { "field_name": "x" }   → drops column
    """

    queryset = None          # set in subclass
    serializer_class = None  # set in subclass

    # ------------------------------------------------------------------ helpers

    @property
    def _table(self):
        return self.queryset.model._meta.db_table

    def _get_serializer(self, *args, **kwargs):
        fields = self.request.query_params.get("fields")
        if fields:
            kwargs["fields"] = fields
        return self.serializer_class(*args, **kwargs)

    def _fetch_all(self):
        cols = _live_columns(self._table)
        col_list = ", ".join('"' + c + '"' for c in cols)
        with connection.cursor() as cur:
            cur.execute(f'SELECT {col_list} FROM "{self._table}"')
            rows = cur.fetchall()
        return [dict(zip(cols, row)) for row in rows]

    def _fetch_one(self, vlcode):
        cols = _live_columns(self._table)
        col_list = ", ".join('"' + c + '"' for c in cols)
        with connection.cursor() as cur:
            cur.execute(
                f'SELECT {col_list} FROM "{self._table}" WHERE vlcode = %s',
                [vlcode],
            )
            row = cur.fetchone()
        return dict(zip(cols, row)) if row else None

    def _exists(self, vlcode):
        with connection.cursor() as cur:
            cur.execute(f'SELECT 1 FROM "{self._table}" WHERE vlcode = %s', [vlcode])
            return cur.fetchone() is not None

    # ------------------------------------------------------------------ CRUD

    def list(self, request):
        rows = self._fetch_all()
        serializer = self._get_serializer(rows, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        row = self._fetch_one(pk)
        if row is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(self._get_serializer(row).data)

    def create(self, request):
        cols = _live_columns(self._table)
        data = {k: v for k, v in request.data.items() if k in cols}
        if "vlcode" not in data:
            return Response({"error": "vlcode is required"}, status=status.HTTP_400_BAD_REQUEST)
        if self._exists(data["vlcode"]):
            return Response({"error": "vlcode already exists"}, status=status.HTTP_400_BAD_REQUEST)
        keys = list(data.keys())
        placeholders = ", ".join("%s" for _ in keys)
        col_list = ", ".join('"' + k + '"' for k in keys)
        with connection.cursor() as cur:
            cur.execute(
                f'INSERT INTO "{self._table}" ({col_list}) VALUES ({placeholders})',
                list(data.values()),
            )
        return Response(self._fetch_one(data["vlcode"]), status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return self._do_update(request, pk, partial=False)

    def partial_update(self, request, pk=None):
        return self._do_update(request, pk, partial=True)

    def _do_update(self, request, pk, partial):
        if not self._exists(pk):
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        cols = _live_columns(self._table)
        data = {k: v for k, v in request.data.items() if k in cols and k != "vlcode"}
        if not data and not partial:
            return Response({"error": "No valid fields provided"}, status=status.HTTP_400_BAD_REQUEST)
        if not data:
            return Response(self._fetch_one(pk))
        set_clause = ", ".join('"' + k + '" = %s' for k in data)
        with connection.cursor() as cur:
            cur.execute(
                f'UPDATE "{self._table}" SET {set_clause} WHERE vlcode = %s',
                list(data.values()) + [pk],
            )
        return Response(self._fetch_one(pk))

    def destroy(self, request, pk=None):
        if not self._exists(pk):
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        with connection.cursor() as cur:
            cur.execute(f'DELETE FROM "{self._table}" WHERE vlcode = %s', [pk])
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ------------------------------------------------------------------ schema actions

    @action(detail=False, methods=["get"])
    def schema(self, request):
        with connection.cursor() as cur:
            cur.execute(f'PRAGMA table_info("{self._table}")')
            cols = [
                {"name": row[1], "type": row[2], "not_null": bool(row[3]), "pk": bool(row[5])}
                for row in cur.fetchall()
            ]
        return Response({"table": self._table, "columns": cols})

    @action(detail=False, methods=["post"], url_path="add-field")
    def add_field(self, request):
        field_name = request.data.get("field_name", "").strip()
        if not _safe_identifier(field_name):
            return Response(
                {"error": "field_name must be non-empty alphanumeric/underscore"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if field_name in _live_columns(self._table):
            return Response(
                {"error": f"Column '{field_name}' already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        field_type = request.data.get("field_type", "REAL").upper()
        if field_type not in ("REAL", "TEXT", "INTEGER"):
            field_type = "REAL"
        with connection.cursor() as cur:
            cur.execute(f'ALTER TABLE "{self._table}" ADD COLUMN "{field_name}" {field_type}')
        return Response(
            {"message": f"Column '{field_name}' ({field_type}) added to '{self._table}'"},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="remove-field")
    def remove_field(self, request):
        field_name = request.data.get("field_name", "").strip()
        if not _safe_identifier(field_name):
            return Response(
                {"error": "field_name must be non-empty alphanumeric/underscore"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if field_name == "vlcode":
            return Response(
                {"error": "Cannot remove primary key column 'vlcode'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if field_name not in _live_columns(self._table):
            return Response(
                {"error": f"Column '{field_name}' does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with connection.cursor() as cur:
            cur.execute(f'ALTER TABLE "{self._table}" DROP COLUMN "{field_name}"')
        return Response({"message": f"Column '{field_name}' removed from '{self._table}'"})


# ------------------------------------------------------------------ concrete viewsets

class OverviewViewSet(DynamicModelViewSet):
    queryset = Overview.objects.all()
    serializer_class = OverviewSerializer


class EmissionsViewSet(DynamicModelViewSet):
    queryset = Emissions.objects.all()
    serializer_class = EmissionsSerializer


class SequestrationViewSet(DynamicModelViewSet):
    queryset = Sequestration.objects.all()
    serializer_class = SequestrationSerializer


class InterventionsViewSet(DynamicModelViewSet):
    queryset = Interventions.objects.all()
    serializer_class = InterventionsSerializer


class CarbonBudgetViewSet(DynamicModelViewSet):
    queryset = CarbonBudget.objects.all()
    serializer_class = CarbonBudgetSerializer


class ScenariosViewSet(DynamicModelViewSet):
    queryset = Scenarios.objects.all()
    serializer_class = ScenariosSerializer
