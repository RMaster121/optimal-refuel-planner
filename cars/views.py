"""Views for the Car API."""
from django_filters.rest_framework import DjangoFilterBackend
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


class CarViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user car profiles.
    
    Provides complete CRUD operations:
    - list: GET /api/cars/ - List user's cars
    - create: POST /api/cars/ - Create new car
    - retrieve: GET /api/cars/{id}/ - Get car details
    - update: PUT /api/cars/{id}/ - Full update
    - partial_update: PATCH /api/cars/{id}/ - Partial update
    - destroy: DELETE /api/cars/{id}/ - Delete car
    
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