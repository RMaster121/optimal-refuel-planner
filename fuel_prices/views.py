"""API views for fuel price data access and management.

This module provides REST API endpoints for accessing and managing fuel price
data through Django REST Framework ViewSets. It includes public read-only
endpoints for browsing historical fuel prices and admin-only endpoints for
data management.

The API supports filtering by country code and fuel type, searching by country
name, and ordering by various fields. Results are paginated for performance.
"""
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.pagination import PageNumberPagination

from fuel_prices.models import FuelPrice
from fuel_prices.serializers import FuelPriceSerializer


class FuelPricePagination(PageNumberPagination):
    """Pagination configuration for fuel price listings.
    
    Provides configurable page size for fuel price API responses with
    reasonable defaults to balance performance and usability.
    
    Attributes:
        page_size (int): Default number of items per page (20).
        page_size_query_param (str): Query parameter name for custom page size.
        max_page_size (int): Maximum allowed items per page (100).
    
    Example:
        Request with custom page size:
        
        GET /api/fuel-prices/?page_size=50
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(tags=["Fuel Prices"])
@extend_schema_view(
    list=extend_schema(
        summary="List fuel prices",
        description="Retrieve a paginated list of fuel prices. Publicly accessible for browsing current prices across European countries.",
        parameters=[
            OpenApiParameter(name="country__code", description="Filter by ISO country code (e.g., PL, DE, FR)", required=False),
            OpenApiParameter(name="fuel_type", description="Filter by fuel type (gasoline, diesel, lpg)", required=False),
            OpenApiParameter(name="search", description="Search by country name", required=False),
            OpenApiParameter(name="ordering", description="Order by: country__code, price_per_liter, scraped_at (prefix with '-' for descending)", required=False),
            OpenApiParameter(name="page", description="Page number", required=False, type=int),
            OpenApiParameter(name="page_size", description="Number of results per page (max 100)", required=False, type=int),
        ],
        responses={200: FuelPriceSerializer(many=True)},
        examples=[
            OpenApiExample(
                "List Latest Prices",
                description="Example: Get latest fuel prices for Poland ordered by scrape date",
                value={
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "country_code": "PL",
                            "country_name": "Poland",
                            "fuel_type": "gasoline",
                            "price_per_liter": "1.45",
                            "scraped_at": "2024-01-15T10:30:00Z",
                        }
                    ],
                },
                response_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Get fuel price details",
        description="Retrieve detailed information about a specific fuel price entry. Publicly accessible.",
        responses={
            200: FuelPriceSerializer,
            404: OpenApiResponse(description="Fuel price not found"),
        },
    ),
    create=extend_schema(
        summary="Create fuel price entry (Admin only)",
        description="Add a new fuel price entry. Requires administrator privileges.",
        request=FuelPriceSerializer,
        responses={
            201: FuelPriceSerializer,
            400: OpenApiResponse(description="Invalid fuel price data"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Admin privileges required"),
        },
        examples=[
            OpenApiExample(
                "Create Fuel Price",
                value={
                    "country_code": "DE",
                    "fuel_type": "diesel",
                    "price_per_liter": "1.55",
                },
                request_only=True,
            ),
        ],
    ),
    update=extend_schema(
        summary="Update fuel price entry (Admin only)",
        description="Fully update a fuel price entry. Requires administrator privileges.",
        request=FuelPriceSerializer,
        responses={
            200: FuelPriceSerializer,
            400: OpenApiResponse(description="Invalid fuel price data"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Admin privileges required"),
            404: OpenApiResponse(description="Fuel price not found"),
        },
    ),
    partial_update=extend_schema(
        summary="Partially update fuel price (Admin only)",
        description="Update specific fields of a fuel price entry. Requires administrator privileges.",
        request=FuelPriceSerializer,
        responses={
            200: FuelPriceSerializer,
            400: OpenApiResponse(description="Invalid fuel price data"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Admin privileges required"),
            404: OpenApiResponse(description="Fuel price not found"),
        },
    ),
    destroy=extend_schema(
        summary="Delete fuel price entry (Admin only)",
        description="Permanently delete a fuel price entry. Requires administrator privileges.",
        responses={
            204: OpenApiResponse(description="Fuel price successfully deleted"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Admin privileges required"),
            404: OpenApiResponse(description="Fuel price not found"),
        },
    ),
)
class FuelPriceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing fuel price data with public read and admin write access.
    
    Provides comprehensive API endpoints for accessing historical fuel price data.
    Read operations (list, retrieve) are publicly accessible to allow users to
    browse current fuel prices. Write operations (create, update, delete) are
    restricted to administrators for data integrity.
    
    The API automatically optimizes queries by prefetching related country data
    using the custom FuelPriceManager.
    """
    queryset = FuelPrice.objects.all()
    serializer_class = FuelPriceSerializer
    pagination_class = FuelPricePagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['country__code', 'fuel_type']
    search_fields = ['country__name']
    ordering_fields = ['country__code', 'price_per_liter', 'scraped_at']
    ordering = ['-scraped_at', 'country__code', 'fuel_type']
    
    def get_permissions(self):
        """Return appropriate permission classes based on the action.
        
        Public access is granted for read-only operations (list, retrieve),
        while write operations require administrator privileges.
        
        Returns:
            list: List of permission class instances for the current action.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]