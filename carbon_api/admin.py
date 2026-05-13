from django.contrib import admin
from .models import Overview, Emissions, Sequestration, Interventions, CarbonBudget, Scenarios


class DynamicAdmin(admin.ModelAdmin):
    """Auto-populate list_display from all model fields."""

    def get_list_display(self, request):
        return [f.name for f in self.model._meta.get_fields() if hasattr(f, "column")]

    def get_search_fields(self, request):
        return ["vlcode"]


@admin.register(Overview)
class OverviewAdmin(DynamicAdmin):
    search_fields = ["vlcode", "village_name", "district", "state"]


@admin.register(Emissions)
class EmissionsAdmin(DynamicAdmin):
    pass


@admin.register(Sequestration)
class SequestrationAdmin(DynamicAdmin):
    pass


@admin.register(Interventions)
class InterventionsAdmin(DynamicAdmin):
    pass


@admin.register(CarbonBudget)
class CarbonBudgetAdmin(DynamicAdmin):
    pass


@admin.register(Scenarios)
class ScenariosAdmin(DynamicAdmin):
    pass
