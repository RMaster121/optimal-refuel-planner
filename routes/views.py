"""Views for the Route API."""

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter
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


@extend_schema(tags=["Routes"])
@extend_schema_view(
    list=extend_schema(
        summary="List user's routes",
        description="Retrieve a paginated list of routes uploaded by the authenticated user.",
        parameters=[
            OpenApiParameter(name="search", description="Search by origin or destination", required=False),
            OpenApiParameter(name="ordering", description="Order by: created_at, total_distance_km", required=False),
            OpenApiParameter(name="page", description="Page number", required=False, type=int),
            OpenApiParameter(name="page_size", description="Number of results per page (max 100)", required=False, type=int),
        ],
        responses={200: RouteSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Upload GPX route",
        description="Upload a GPX file to create a new route. The system will parse waypoints and identify countries along the route.",
        request=RouteCreateSerializer,
        responses={
            201: RouteSerializer,
            400: OpenApiResponse(description="Invalid GPX file or data"),
        },
    ),
    retrieve=extend_schema(
        summary="Get route details",
        description="Retrieve detailed information about a specific route including waypoints and countries.",
        responses={
            200: RouteSerializer,
            404: OpenApiResponse(description="Route not found"),
        },
    ),
    update=extend_schema(
        summary="Update route",
        description="Fully update route information. Note: Not recommended for GPX-based routes. Create a new route instead.",
        request=RouteSerializer,
        responses={
            200: RouteSerializer,
            400: OpenApiResponse(description="Invalid route data"),
            404: OpenApiResponse(description="Route not found"),
        },
    ),
    partial_update=extend_schema(
        summary="Partially update route",
        description="Update specific route fields.",
        request=RouteSerializer,
        responses={
            200: RouteSerializer,
            400: OpenApiResponse(description="Invalid route data"),
            404: OpenApiResponse(description="Route not found"),
        },
    ),
    destroy=extend_schema(
        summary="Delete route",
        description="Permanently delete a route and all associated data.",
        responses={
            204: OpenApiResponse(description="Route successfully deleted"),
            404: OpenApiResponse(description="Route not found"),
        },
    ),
)
class RouteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user routes.
    
    All endpoints require authentication. Users can only access their own routes.
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