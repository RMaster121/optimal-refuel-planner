"""URL configuration for the Refuel Planner API."""

from rest_framework.routers import DefaultRouter

from planner.views import RefuelPlanViewSet

router = DefaultRouter()
router.register(r'', RefuelPlanViewSet, basename='refuelplan')

urlpatterns = router.urls