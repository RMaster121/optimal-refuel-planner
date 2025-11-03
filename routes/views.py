"""Views for the Route API."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from routes.models import Route
from routes.serializers import RouteSerializer, RouteCreateSerializer


class RoutePagination(PageNumberPagination):
    """Custom pagination for route listings."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class RouteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user routes.
    
    Provides complete CRUD operations:
    - list: GET /api/routes/ - List user's routes
    - create: POST /api/routes/ - Upload GPX file to create route
    - retrieve: GET /api/routes/{id}/ - Get route details
    - update: PUT /api/routes/{id}/ - Full update (not recommended for GPX routes)
    - partial_update: PATCH /api/routes/{id}/ - Partial update
    - destroy: DELETE /api/routes/{id}/ - Delete route
    
    All endpoints require authentication. Users can only access their own routes.
    
    GPX Upload:
    POST /api/routes/
    Content-Type: multipart/form-data
    Body: {
        "gpx_file": <file>,
        "waypoint_interval_km": 50  (optional, default: 50)
    }
    """
    permission_classes = [IsAuthenticated]
    pagination_class = RoutePagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['origin', 'destination']
    ordering_fields = ['created_at', 'total_distance_km']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter routes to show only those belonging to the authenticated user."""
        return Route.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Use different serializers for create vs read operations."""
        if self.action == 'create':
            return RouteCreateSerializer
        return RouteSerializer
    
    def perform_create(self, serializer):
        """Automatically set the route owner to the authenticated user."""
        serializer.save(user=self.request.user)