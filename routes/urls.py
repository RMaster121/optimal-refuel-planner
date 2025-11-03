"""URL configuration for the Route API."""

from rest_framework.routers import DefaultRouter

from routes.views import RouteViewSet

router = DefaultRouter()
router.register(r'', RouteViewSet, basename='route')

urlpatterns = router.urls