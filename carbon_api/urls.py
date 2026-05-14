from rest_framework.routers import DefaultRouter
from .views import (
    OverviewViewSet,
    EmissionsViewSet,
    SequestrationViewSet,
    InterventionsViewSet,
    CarbonBudgetViewSet,
    ScenariosViewSet,
    AdminUserViewSet,
)

router = DefaultRouter()
router.register(r"overview", OverviewViewSet, basename="overview")
router.register(r"emissions", EmissionsViewSet, basename="emissions")
router.register(r"sequestration", SequestrationViewSet, basename="sequestration")
router.register(r"interventions", InterventionsViewSet, basename="interventions")
router.register(r"carbon-budget", CarbonBudgetViewSet, basename="carbon-budget")
router.register(r"scenarios", ScenariosViewSet, basename="scenarios")
router.register(r"admin-users", AdminUserViewSet, basename="admin-users")

urlpatterns = router.urls
