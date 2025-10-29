import pytest
from decimal import Decimal
from django.utils import timezone
from rest_framework import status

from fuel_prices.models import Country, FuelPrice
from refuel_planner.choices import FuelType


@pytest.mark.django_db
class TestFuelPriceList:
    """Test cases for listing fuel prices."""
    
    def test_list_fuel_prices_unauthenticated(self, api_client, fuel_price_pl_gasoline, fuel_price_de_gasoline):
        """Test unauthenticated users can list fuel prices (public endpoint)."""
        response = api_client.get('/api/fuel-prices/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert response.data['count'] == 2
    
    def test_list_fuel_prices_authenticated(self, authenticated_client, fuel_price_pl_gasoline):
        """Test authenticated users can also list fuel prices."""
        response = authenticated_client.get('/api/fuel-prices/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
    
    def test_list_fuel_prices_includes_country_info(self, api_client, fuel_price_pl_gasoline):
        """Test that country_code and country_name are included in response."""
        response = api_client.get('/api/fuel-prices/')
        
        assert response.status_code == status.HTTP_200_OK
        price_data = response.data['results'][0]
        assert 'country_code' in price_data
        assert 'country_name' in price_data
        assert price_data['country_code'] == 'PL'
        assert price_data['country_name'] == 'Poland'
    
    def test_list_fuel_prices_ordering(self, api_client, country_poland, country_germany):
        """Test fuel prices are ordered by scraped_at desc, then country."""
        old_time = timezone.now() - timezone.timedelta(days=1)
        
        FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('1.45'),
            scraped_at=old_time
        )
        
        new_price = FuelPrice.objects.create(
            country=country_germany,
            fuel_type=FuelType.DIESEL,
            price_per_liter=Decimal('1.65'),
            scraped_at=timezone.now()
        )
        
        response = api_client.get('/api/fuel-prices/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['id'] == new_price.id


@pytest.mark.django_db
class TestFuelPriceFiltering:
    """Test cases for filtering fuel prices."""
    
    def test_filter_by_country_code(self, api_client, fuel_price_pl_gasoline, fuel_price_de_gasoline):
        """Test filtering fuel prices by country code."""
        response = api_client.get('/api/fuel-prices/?country__code=PL')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['country_code'] == 'PL'
    
    def test_filter_by_fuel_type(self, api_client, fuel_price_pl_gasoline, fuel_price_pl_diesel):
        """Test filtering fuel prices by fuel type."""
        response = api_client.get(f'/api/fuel-prices/?fuel_type={FuelType.GASOLINE}')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['fuel_type'] == FuelType.GASOLINE
    
    def test_filter_combined(self, api_client, country_poland):
        """Test combined filtering by country and fuel type."""
        FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('1.45'),
            scraped_at=timezone.now()
        )
        FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.DIESEL,
            price_per_liter=Decimal('1.50'),
            scraped_at=timezone.now()
        )
        
        response = api_client.get(f'/api/fuel-prices/?country__code=PL&fuel_type={FuelType.DIESEL}')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['fuel_type'] == FuelType.DIESEL
    
    def test_search_by_country_name(self, api_client, fuel_price_pl_gasoline, fuel_price_de_gasoline):
        """Test searching fuel prices by country name."""
        response = api_client.get('/api/fuel-prices/?search=Poland')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['country_name'] == 'Poland'


@pytest.mark.django_db
class TestFuelPriceRetrieve:
    """Test cases for retrieving a single fuel price."""
    
    def test_retrieve_fuel_price_unauthenticated(self, api_client, fuel_price_pl_gasoline):
        """Test unauthenticated users can retrieve specific fuel price."""
        response = api_client.get(f'/api/fuel-prices/{fuel_price_pl_gasoline.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == fuel_price_pl_gasoline.id
        assert response.data['country_code'] == 'PL'
        assert 'scraped_at' in response.data
    
    def test_retrieve_nonexistent_fuel_price(self, api_client):
        """Test retrieving non-existent fuel price."""
        response = api_client.get('/api/fuel-prices/99999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestFuelPriceCreate:
    """Test cases for creating fuel prices."""
    
    def test_create_fuel_price_admin(self, admin_client, country_poland):
        """Test admin can create fuel price."""
        price_data = {
            'country_code': 'PL',
            'fuel_type': FuelType.GASOLINE,
            'price_per_liter': '1.45'
        }
        
        response = admin_client.post('/api/fuel-prices/', price_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['country_code'] == 'PL'
        assert response.data['fuel_type'] == FuelType.GASOLINE
        assert Decimal(response.data['price_per_liter']) == Decimal('1.45')
        assert 'scraped_at' in response.data
        
        assert FuelPrice.objects.filter(country__code='PL', fuel_type=FuelType.GASOLINE).exists()
    
    def test_create_fuel_price_unauthenticated(self, api_client, country_poland):
        """Test unauthenticated users cannot create fuel prices."""
        price_data = {
            'country_code': 'PL',
            'fuel_type': FuelType.GASOLINE,
            'price_per_liter': '1.45'
        }
        
        response = api_client.post('/api/fuel-prices/', price_data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_fuel_price_regular_user(self, authenticated_client, country_poland):
        """Test regular authenticated users cannot create fuel prices."""
        price_data = {
            'country_code': 'PL',
            'fuel_type': FuelType.GASOLINE,
            'price_per_liter': '1.45'
        }
        
        response = authenticated_client.post('/api/fuel-prices/', price_data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_fuel_price_invalid_country(self, admin_client):
        """Test creating fuel price with non-existent country."""
        price_data = {
            'country_code': 'XX',
            'fuel_type': FuelType.GASOLINE,
            'price_per_liter': '1.45'
        }
        
        response = admin_client.post('/api/fuel-prices/', price_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'country_code' in response.data
    
    def test_create_fuel_price_invalid_fuel_type(self, admin_client, country_poland):
        """Test creating fuel price with invalid fuel type."""
        price_data = {
            'country_code': 'PL',
            'fuel_type': 'kerosene',
            'price_per_liter': '1.45'
        }
        
        response = admin_client.post('/api/fuel-prices/', price_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'fuel_type' in response.data
    
    def test_create_fuel_price_negative(self, admin_client, country_poland):
        """Test creating fuel price with negative value."""
        price_data = {
            'country_code': 'PL',
            'fuel_type': FuelType.GASOLINE,
            'price_per_liter': '-1.45'
        }
        
        response = admin_client.post('/api/fuel-prices/', price_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'price_per_liter' in response.data
    
    def test_create_fuel_price_too_low(self, admin_client, country_poland):
        """Test creating fuel price below minimum threshold."""
        price_data = {
            'country_code': 'PL',
            'fuel_type': FuelType.GASOLINE,
            'price_per_liter': '0.30'
        }
        
        response = admin_client.post('/api/fuel-prices/', price_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'price_per_liter' in response.data
    
    def test_create_fuel_price_too_high(self, admin_client, country_poland):
        """Test creating fuel price above maximum threshold."""
        price_data = {
            'country_code': 'PL',
            'fuel_type': FuelType.GASOLINE,
            'price_per_liter': '5.00'
        }
        
        response = admin_client.post('/api/fuel-prices/', price_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'price_per_liter' in response.data
    
    def test_create_fuel_price_missing_fields(self, admin_client):
        """Test creating fuel price with missing required fields."""
        price_data = {
            'country_code': 'PL'
        }
        
        response = admin_client.post('/api/fuel-prices/', price_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'fuel_type' in response.data or 'price_per_liter' in response.data


@pytest.mark.django_db
class TestFuelPriceUpdate:
    """Test cases for updating fuel prices."""
    
    def test_update_fuel_price_admin(self, admin_client, fuel_price_pl_gasoline):
        """Test admin can update fuel price."""
        update_data = {
            'price_per_liter': '1.55'
        }
        
        response = admin_client.patch(
            f'/api/fuel-prices/{fuel_price_pl_gasoline.id}/',
            update_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data['price_per_liter']) == Decimal('1.55')
    
    def test_update_fuel_price_unauthenticated(self, api_client, fuel_price_pl_gasoline):
        """Test unauthenticated users cannot update fuel prices."""
        update_data = {'price_per_liter': '1.55'}
        
        response = api_client.patch(
            f'/api/fuel-prices/{fuel_price_pl_gasoline.id}/',
            update_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_fuel_price_regular_user(self, authenticated_client, fuel_price_pl_gasoline):
        """Test regular users cannot update fuel prices."""
        update_data = {'price_per_liter': '1.55'}
        
        response = authenticated_client.patch(
            f'/api/fuel-prices/{fuel_price_pl_gasoline.id}/',
            update_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestFuelPriceDelete:
    """Test cases for deleting fuel prices."""
    
    def test_delete_fuel_price_admin(self, admin_client, fuel_price_pl_gasoline):
        """Test admin can delete fuel price."""
        price_id = fuel_price_pl_gasoline.id
        
        response = admin_client.delete(f'/api/fuel-prices/{price_id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not FuelPrice.objects.filter(id=price_id).exists()
    
    def test_delete_fuel_price_unauthenticated(self, api_client, fuel_price_pl_gasoline):
        """Test unauthenticated users cannot delete fuel prices."""
        response = api_client.delete(f'/api/fuel-prices/{fuel_price_pl_gasoline.id}/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert FuelPrice.objects.filter(id=fuel_price_pl_gasoline.id).exists()
    
    def test_delete_fuel_price_regular_user(self, authenticated_client, fuel_price_pl_gasoline):
        """Test regular users cannot delete fuel prices."""
        response = authenticated_client.delete(f'/api/fuel-prices/{fuel_price_pl_gasoline.id}/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert FuelPrice.objects.filter(id=fuel_price_pl_gasoline.id).exists()


@pytest.mark.django_db
class TestFuelPricePagination:
    """Test cases for fuel price pagination."""
    
    def test_fuel_price_pagination(self, api_client, country_poland):
        """Test pagination for fuel price listing."""
        for i in range(25):
            FuelPrice.objects.create(
                country=country_poland,
                fuel_type=FuelType.GASOLINE if i % 2 == 0 else FuelType.DIESEL,
                price_per_liter=Decimal('1.45') + Decimal(str(i * 0.01)),
                scraped_at=timezone.now() - timezone.timedelta(days=i)
            )
        
        response = api_client.get('/api/fuel-prices/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 25
        assert len(response.data['results']) == 20
        assert response.data['next'] is not None