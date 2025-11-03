"""Views for the Refuel Planner API."""

from django_filters.rest_framework import DjangoFilterBackend
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


class RefuelPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing refuel plans.
    
    Provides operations:
    - list: GET /api/refuel-plans/ - List user's plans
    - create: POST /api/refuel-plans/ - Create new plan
    - retrieve: GET /api/refuel-plans/{id}/ - Get plan details
    - destroy: DELETE /api/refuel-plans/{id}/ - Delete plan
    
    All endpoints require authentication. Users can only access their own plans.
    
    Create Plan:
    POST /api/refuel-plans/
    Body: {
        "route": <route_id>,
        "car": <car_id>,
        "reservoir_km": 100,  (optional, default: 100)
        "optimization_strategy": "min_stops"  (optional, default: min_stops)
    }
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