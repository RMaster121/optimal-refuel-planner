"""Views for the Car API."""
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from cars.models import Car
from cars.serializers import CarSerializer


class CarPagination(PageNumberPagination):
    """Custom pagination for car listings."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(tags=["Cars"])
@extend_schema_view(
    list=extend_schema(
        summary="List user's cars",
        description="Retrieve a paginated list of cars owned by the authenticated user.",
        parameters=[
            OpenApiParameter(name="fuel_type", description="Filter by fuel type (gasoline, diesel, lpg, electric)", required=False),
            OpenApiParameter(name="search", description="Search by car name", required=False),
            OpenApiParameter(name="ordering", description="Order by: name, created_at, fuel_type", required=False),
            OpenApiParameter(name="page", description="Page number", required=False, type=int),
            OpenApiParameter(name="page_size", description="Number of results per page (max 100)", required=False, type=int),
        ],
        responses={200: CarSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Create new car",
        description="Add a new car to the user's profile with fuel consumption details.",
        request=CarSerializer,
        responses={
            201: CarSerializer,
            400: OpenApiResponse(description="Invalid car data"),
        },
        examples=[
            OpenApiExample(
                "Car Example",
                value={
                    "name": "Tesla Model 3",
                    "fuel_type": "electric",
                    "fuel_consumption_per_100km": "15.5",
                },
                request_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Get car details",
        description="Retrieve detailed information about a specific car.",
        responses={
            200: CarSerializer,
            404: OpenApiResponse(description="Car not found"),
        },
    ),
    update=extend_schema(
        summary="Update car",
        description="Fully update a car's information.",
        request=CarSerializer,
        responses={
            200: CarSerializer,
            400: OpenApiResponse(description="Invalid car data"),
            404: OpenApiResponse(description="Car not found"),
        },
    ),
    partial_update=extend_schema(
        summary="Partially update car",
        description="Update specific fields of a car.",
        request=CarSerializer,
        responses={
            200: CarSerializer,
            400: OpenApiResponse(description="Invalid car data"),
            404: OpenApiResponse(description="Car not found"),
        },
    ),
    destroy=extend_schema(
        summary="Delete car",
        description="Permanently delete a car from the user's profile.",
        responses={
            204: OpenApiResponse(description="Car successfully deleted"),
            404: OpenApiResponse(description="Car not found"),
        },
    ),
)
class CarViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user car profiles.
    
    All endpoints require authentication. Users can only access their own cars.
    Returns 404 for cars belonging to other users to prevent data leakage.
    """
    serializer_class = CarSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CarPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['fuel_type']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'fuel_type']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter cars to show only those belonging to the authenticated user."""
        return Car.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Automatically set the car owner to the authenticated user."""
        serializer.save(user=self.request.user)