from rest_framework.routers import DefaultRouter

from fuel_prices.views import FuelPriceViewSet

router = DefaultRouter()
router.register(r'', FuelPriceViewSet, basename='fuel-price')

urlpatterns = router.urls