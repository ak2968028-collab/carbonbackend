from django.db import connection
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import AdminUser, CarbonBudget, Emissions, Interventions, Overview, Scenarios, Sequestration


def get_live_columns(table_name):
    """Return list of column names currently in the SQLite table."""
    with connection.cursor() as cursor:
        cursor.execute(f'PRAGMA table_info("{table_name}")')
        return [row[1] for row in cursor.fetchall()]


class LiveTableSerializer(serializers.Serializer):
    """
    Fully dynamic serializer: reads actual DB columns at runtime via PRAGMA.
    Supports any columns added or dropped with ALTER TABLE — no model changes needed.
    Accepts ?fields=a,b to restrict output.
    """

    def __init__(self, *args, **kwargs):
        restrict_fields = kwargs.pop("fields", None)
        super().__init__(*args, **kwargs)

        table = self.Meta.model._meta.db_table
        live_cols = get_live_columns(table)

        if restrict_fields:
            allowed = set(restrict_fields.split(","))
            live_cols = [c for c in live_cols if c in allowed]

        for col in live_cols:
            self.fields[col] = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    def to_representation(self, instance):
        table = self.Meta.model._meta.db_table
        live_cols = get_live_columns(table)
        restrict = getattr(self, "_restrict_fields", None)
        if restrict:
            live_cols = [c for c in live_cols if c in restrict]
        result = {}
        for col in live_cols:
            # instance may be a model object or a dict (from values())
            if isinstance(instance, dict):
                result[col] = instance.get(col)
            else:
                result[col] = getattr(instance, col, None)
        return result

    def to_internal_value(self, data):
        table = self.Meta.model._meta.db_table
        live_cols = get_live_columns(table)
        validated = {}
        for col in live_cols:
            if col in data:
                validated[col] = data[col] if data[col] not in ("", None) else None
        return validated

    class Meta:
        model = None


class OverviewSerializer(LiveTableSerializer):
    class Meta:
        model = Overview


class EmissionsSerializer(LiveTableSerializer):
    class Meta:
        model = Emissions


class SequestrationSerializer(LiveTableSerializer):
    class Meta:
        model = Sequestration


class InterventionsSerializer(LiveTableSerializer):
    class Meta:
        model = Interventions


class CarbonBudgetSerializer(LiveTableSerializer):
    class Meta:
        model = CarbonBudget


class ScenariosSerializer(LiveTableSerializer):
    class Meta:
        model = Scenarios


class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = AdminUser
        fields = (
            "id",
            "username",
            "email",
            "password",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if not password:
            raise serializers.ValidationError({"password": "Password is required"})
        user = self.Meta.model(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
