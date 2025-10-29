"""URL configuration for the Car API."""

from rest_framework.routers import DefaultRouter

from cars.views import CarViewSet

router = DefaultRouter()
router.register(r'', CarViewSet, basename='car')

urlpatterns = router.urls