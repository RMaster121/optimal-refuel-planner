"""Views for the Refuel Planner API."""

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from planner.models import RefuelPlan
from planner.serializers import RefuelPlanSerializer, CreateRefuelPlanSerializer


class RefuelPlanPagination(PageNumberPagination):
    """Custom pagination for refuel plan listings."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(tags=["Refuel Plans"])
@extend_schema_view(
    list=extend_schema(
        summary="List user's refuel plans",
        description="Retrieve a paginated list of refuel plans created by the authenticated user.",
        parameters=[
            OpenApiParameter(name="optimization_strategy", description="Filter by optimization strategy (min_stops, min_cost)", required=False),
            OpenApiParameter(name="ordering", description="Order by: created_at, total_cost, number_of_stops", required=False),
            OpenApiParameter(name="page", description="Page number", required=False, type=int),
            OpenApiParameter(name="page_size", description="Number of results per page (max 100)", required=False, type=int),
        ],
        responses={200: RefuelPlanSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Create refuel plan",
        description="Generate an optimal refuel plan for a route and car combination. The system calculates the best refueling strategy based on current fuel prices and vehicle consumption.",
        request=CreateRefuelPlanSerializer,
        responses={
            201: RefuelPlanSerializer,
            400: OpenApiResponse(description="Invalid plan data or calculation error"),
        },
        examples=[
            OpenApiExample(
                "Create Refuel Plan",
                value={
                    "route": 1,
                    "car": 1,
                    "reservoir_km": 100,
                    "optimization_strategy": "min_stops",
                },
                request_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Get refuel plan details",
        description="Retrieve detailed information about a specific refuel plan including all refueling stops.",
        responses={
            200: RefuelPlanSerializer,
            404: OpenApiResponse(description="Refuel plan not found"),
        },
    ),
    destroy=extend_schema(
        summary="Delete refuel plan",
        description="Permanently delete a refuel plan and all associated refueling stops.",
        responses={
            204: OpenApiResponse(description="Refuel plan successfully deleted"),
            404: OpenApiResponse(description="Refuel plan not found"),
        },
    ),
)
class RefuelPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing refuel plans.
    
    All endpoints require authentication. Users can only access their own plans.
    Update operations are disabled - create a new plan instead.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = RefuelPlanPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filterset_fields = ['optimization_strategy']
    ordering_fields = ['created_at', 'total_cost', 'number_of_stops']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    
    def get_queryset(self):
        """Filter plans to show only those belonging to the authenticated user."""
        return RefuelPlan.objects.filter(route__user=self.request.user)
    
    def get_serializer_class(self):
        """Use different serializers for create vs read operations."""
        if self.action == 'create':
            return CreateRefuelPlanSerializer
        return RefuelPlanSerializer