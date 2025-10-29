from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.pagination import PageNumberPagination

from fuel_prices.models import FuelPrice
from fuel_prices.serializers import FuelPriceSerializer


class FuelPricePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class FuelPriceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing fuel prices.
    
    Public access: list, retrieve
    Admin-only: create, update, delete
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
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]