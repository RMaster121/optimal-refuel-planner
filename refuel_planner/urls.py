from django.contrib import admin
from django.urls import include, path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for load balancers and monitoring."""
    return Response({"status": "healthy"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/auth/", include("users.urls")),
    path("api/cars/", include("cars.urls")),
    path("api/routes/", include("routes.urls")),
    path("api/fuel-prices/", include("fuel_prices.urls")),
    path("api/refuel-plans/", include("planner.urls")),
]