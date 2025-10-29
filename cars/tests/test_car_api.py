"""Test cases for Car CRUD API endpoints."""

import pytest
from decimal import Decimal
from rest_framework import status

from cars.models import Car
from refuel_planner.choices import FuelType


@pytest.mark.django_db
class TestCarList:
    """Test cases for listing cars."""
    
    def test_list_cars_authenticated(self, authenticated_client, user, car_gasoline, car_diesel):
        """Test authenticated user can list their own cars."""
        response = authenticated_client.get('/api/cars/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert response.data['count'] == 2
        
        car_names = [car['name'] for car in response.data['results']]
        assert 'Toyota Corolla' in car_names
        assert 'VW Passat' in car_names
    
    def test_list_cars_unauthenticated(self, api_client):
        """Test unauthenticated user cannot list cars."""
        response = api_client.get('/api/cars/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_cars_only_own_cars(self, authenticated_client, user, another_user, car_gasoline):
        """Test user only sees their own cars, not other users' cars."""
        Car.objects.create(
            user=another_user,
            name='Another User Car',
            fuel_type=FuelType.DIESEL,
            avg_consumption=Decimal('7.0'),
            tank_capacity=Decimal('55.0')
        )
        
        response = authenticated_client.get('/api/cars/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['name'] == 'Toyota Corolla'
    
    def test_list_cars_includes_max_range(self, authenticated_client, car_gasoline):
        """Test that max_range_km is included in the response."""
        response = authenticated_client.get('/api/cars/')
        
        assert response.status_code == status.HTTP_200_OK
        car_data = response.data['results'][0]
        assert 'max_range_km' in car_data
        
        expected_range = (Decimal('50.0') / Decimal('6.5')) * Decimal('100')
        assert Decimal(str(car_data['max_range_km'])) == expected_range.quantize(Decimal('0.01'))
    
    def test_list_cars_pagination(self, authenticated_client, user):
        """Test pagination for car listing."""
        for i in range(12):
            Car.objects.create(
                user=user,
                name=f'Car {i}',
                fuel_type=FuelType.GASOLINE,
                avg_consumption=Decimal('6.0'),
                tank_capacity=Decimal('50.0')
            )
        
        response = authenticated_client.get('/api/cars/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 12
        assert len(response.data['results']) == 10
        assert response.data['next'] is not None
    
    def test_list_cars_search_by_name(self, authenticated_client, user, car_gasoline):
        """Test searching cars by name."""
        response = authenticated_client.get('/api/cars/?search=Toyota')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['name'] == 'Toyota Corolla'
    
    def test_list_cars_filter_by_fuel_type(self, authenticated_client, user, car_gasoline, car_diesel):
        """Test filtering cars by fuel type."""
        response = authenticated_client.get(f'/api/cars/?fuel_type={FuelType.GASOLINE}')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['fuel_type'] == FuelType.GASOLINE
    
    def test_list_cars_ordering(self, authenticated_client, user):
        """Test ordering cars by name."""
        Car.objects.create(
            user=user,
            name='Audi A4',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.0'),
            tank_capacity=Decimal('50.0')
        )
        Car.objects.create(
            user=user,
            name='BMW X5',
            fuel_type=FuelType.DIESEL,
            avg_consumption=Decimal('8.0'),
            tank_capacity=Decimal('70.0')
        )
        
        response = authenticated_client.get('/api/cars/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['name'] == 'Audi A4'
        assert response.data['results'][1]['name'] == 'BMW X5'


@pytest.mark.django_db
class TestCarCreate:
    """Test cases for creating cars."""
    
    def test_create_car_success(self, authenticated_client, user):
        """Test successful car creation."""
        car_data = {
            'name': 'Tesla Model 3',
            'fuel_type': FuelType.DIESEL,
            'avg_consumption': '5.5',
            'tank_capacity': '60.0'
        }
        
        response = authenticated_client.post('/api/cars/', car_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Tesla Model 3'
        assert response.data['fuel_type'] == FuelType.DIESEL
        assert Decimal(response.data['avg_consumption']) == Decimal('5.5')
        assert Decimal(response.data['tank_capacity']) == Decimal('60.0')
        assert 'max_range_km' in response.data
        assert 'id' in response.data
        
        assert Car.objects.filter(user=user, name='Tesla Model 3').exists()
    
    def test_create_car_unauthenticated(self, api_client):
        """Test unauthenticated user cannot create cars."""
        car_data = {
            'name': 'Test Car',
            'fuel_type': FuelType.GASOLINE,
            'avg_consumption': '6.0',
            'tank_capacity': '50.0'
        }
        
        response = api_client.post('/api/cars/', car_data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_car_duplicate_name(self, authenticated_client, user, car_gasoline):
        """Test creating car with duplicate name for same user."""
        car_data = {
            'name': 'Toyota Corolla',
            'fuel_type': FuelType.DIESEL,
            'avg_consumption': '5.0',
            'tank_capacity': '55.0'
        }
        
        response = authenticated_client.post('/api/cars/', car_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
    
    def test_create_car_same_name_different_user(self, authenticated_client, another_user, car_gasoline):
        """Test different users can have cars with the same name."""
        login_response = authenticated_client.post('/api/auth/login/', {
            'email': another_user.email,
            'password': 'testpass123'
        }, format='json')
        
        another_client = authenticated_client.__class__()
        another_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_response.data["access"]}')
        
        car_data = {
            'name': 'Toyota Corolla',
            'fuel_type': FuelType.DIESEL,
            'avg_consumption': '5.0',
            'tank_capacity': '55.0'
        }
        
        response = another_client.post('/api/cars/', car_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Toyota Corolla'
    
    def test_create_car_invalid_consumption_negative(self, authenticated_client):
        """Test creating car with negative consumption."""
        car_data = {
            'name': 'Test Car',
            'fuel_type': FuelType.GASOLINE,
            'avg_consumption': '-5.0',
            'tank_capacity': '50.0'
        }
        
        response = authenticated_client.post('/api/cars/', car_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'avg_consumption' in response.data
    
    def test_create_car_invalid_consumption_too_low(self, authenticated_client):
        """Test creating car with unreasonably low consumption."""
        car_data = {
            'name': 'Test Car',
            'fuel_type': FuelType.GASOLINE,
            'avg_consumption': '0.5',
            'tank_capacity': '50.0'
        }
        
        response = authenticated_client.post('/api/cars/', car_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'avg_consumption' in response.data
    
    def test_create_car_invalid_consumption_too_high(self, authenticated_client):
        """Test creating car with unreasonably high consumption."""
        car_data = {
            'name': 'Test Car',
            'fuel_type': FuelType.GASOLINE,
            'avg_consumption': '35.0',
            'tank_capacity': '50.0'
        }
        
        response = authenticated_client.post('/api/cars/', car_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'avg_consumption' in response.data
    
    def test_create_car_invalid_tank_capacity_negative(self, authenticated_client):
        """Test creating car with negative tank capacity."""
        car_data = {
            'name': 'Test Car',
            'fuel_type': FuelType.GASOLINE,
            'avg_consumption': '6.0',
            'tank_capacity': '-50.0'
        }
        
        response = authenticated_client.post('/api/cars/', car_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'tank_capacity' in response.data
    
    def test_create_car_invalid_tank_capacity_too_low(self, authenticated_client):
        """Test creating car with unreasonably low tank capacity."""
        car_data = {
            'name': 'Test Car',
            'fuel_type': FuelType.GASOLINE,
            'avg_consumption': '6.0',
            'tank_capacity': '10.0'
        }
        
        response = authenticated_client.post('/api/cars/', car_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'tank_capacity' in response.data
    
    def test_create_car_invalid_tank_capacity_too_high(self, authenticated_client):
        """Test creating car with unreasonably high tank capacity."""
        car_data = {
            'name': 'Test Car',
            'fuel_type': FuelType.GASOLINE,
            'avg_consumption': '6.0',
            'tank_capacity': '250.0'
        }
        
        response = authenticated_client.post('/api/cars/', car_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'tank_capacity' in response.data
    
    def test_create_car_missing_name(self, authenticated_client):
        """Test creating car without name."""
        car_data = {
            'fuel_type': FuelType.GASOLINE,
            'avg_consumption': '6.0',
            'tank_capacity': '50.0'
        }
        
        response = authenticated_client.post('/api/cars/', car_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
    
    def test_create_car_empty_name(self, authenticated_client):
        """Test creating car with empty name."""
        car_data = {
            'name': '   ',
            'fuel_type': FuelType.GASOLINE,
            'avg_consumption': '6.0',
            'tank_capacity': '50.0'
        }
        
        response = authenticated_client.post('/api/cars/', car_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data


@pytest.mark.django_db
class TestCarRetrieve:
    """Test cases for retrieving a single car."""
    
    def test_retrieve_car_success(self, authenticated_client, car_gasoline):
        """Test retrieving own car details."""
        response = authenticated_client.get(f'/api/cars/{car_gasoline.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == car_gasoline.id
        assert response.data['name'] == 'Toyota Corolla'
        assert 'max_range_km' in response.data
        assert 'created_at' in response.data
        assert 'updated_at' in response.data
    
    def test_retrieve_car_unauthenticated(self, api_client, car_gasoline):
        """Test unauthenticated user cannot retrieve car."""
        response = api_client.get(f'/api/cars/{car_gasoline.id}/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_retrieve_other_user_car(self, authenticated_client, another_user):
        """Test user cannot retrieve another user's car (404)."""
        other_car = Car.objects.create(
            user=another_user,
            name='Another User Car',
            fuel_type=FuelType.DIESEL,
            avg_consumption=Decimal('7.0'),
            tank_capacity=Decimal('55.0')
        )
        
        response = authenticated_client.get(f'/api/cars/{other_car.id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_retrieve_nonexistent_car(self, authenticated_client):
        """Test retrieving non-existent car."""
        response = authenticated_client.get('/api/cars/99999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCarUpdate:
    """Test cases for updating cars."""
    
    def test_full_update_car_success(self, authenticated_client, car_gasoline):
        """Test full update (PUT) of car."""
        update_data = {
            'name': 'Updated Toyota',
            'fuel_type': FuelType.DIESEL,
            'avg_consumption': '5.0',
            'tank_capacity': '55.0'
        }
        
        response = authenticated_client.put(
            f'/api/cars/{car_gasoline.id}/',
            update_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Toyota'
        assert response.data['fuel_type'] == FuelType.DIESEL
        assert Decimal(response.data['avg_consumption']) == Decimal('5.0')
        
        car_gasoline.refresh_from_db()
        assert car_gasoline.name == 'Updated Toyota'
        assert car_gasoline.fuel_type == FuelType.DIESEL
    
    def test_partial_update_car_success(self, authenticated_client, car_gasoline):
        """Test partial update (PATCH) of car."""
        update_data = {
            'avg_consumption': '7.0'
        }
        
        response = authenticated_client.patch(
            f'/api/cars/{car_gasoline.id}/',
            update_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data['avg_consumption']) == Decimal('7.0')
        assert response.data['name'] == 'Toyota Corolla'
        
        car_gasoline.refresh_from_db()
        assert car_gasoline.avg_consumption == Decimal('7.0')
    
    def test_update_car_unauthenticated(self, api_client, car_gasoline):
        """Test unauthenticated user cannot update car."""
        update_data = {'name': 'Updated'}
        
        response = api_client.patch(
            f'/api/cars/{car_gasoline.id}/',
            update_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_other_user_car(self, authenticated_client, another_user):
        """Test user cannot update another user's car (404)."""
        other_car = Car.objects.create(
            user=another_user,
            name='Another User Car',
            fuel_type=FuelType.DIESEL,
            avg_consumption=Decimal('7.0'),
            tank_capacity=Decimal('55.0')
        )
        
        update_data = {'name': 'Hacked'}
        
        response = authenticated_client.patch(
            f'/api/cars/{other_car.id}/',
            update_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        other_car.refresh_from_db()
        assert other_car.name == 'Another User Car'
    
    def test_update_car_duplicate_name(self, authenticated_client, user, car_gasoline, car_diesel):
        """Test updating car to duplicate name."""
        update_data = {'name': 'VW Passat'}
        
        response = authenticated_client.patch(
            f'/api/cars/{car_gasoline.id}/',
            update_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
    
    def test_update_car_validation_error(self, authenticated_client, car_gasoline):
        """Test updating car with invalid data."""
        update_data = {'avg_consumption': '35.0'}
        
        response = authenticated_client.patch(
            f'/api/cars/{car_gasoline.id}/',
            update_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'avg_consumption' in response.data


@pytest.mark.django_db
class TestCarDelete:
    """Test cases for deleting cars."""
    
    def test_delete_car_success(self, authenticated_client, user, car_gasoline):
        """Test successful car deletion."""
        car_id = car_gasoline.id
        
        response = authenticated_client.delete(f'/api/cars/{car_id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Car.objects.filter(id=car_id).exists()
    
    def test_delete_car_unauthenticated(self, api_client, car_gasoline):
        """Test unauthenticated user cannot delete car."""
        response = api_client.delete(f'/api/cars/{car_gasoline.id}/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Car.objects.filter(id=car_gasoline.id).exists()
    
    def test_delete_other_user_car(self, authenticated_client, another_user):
        """Test user cannot delete another user's car (404)."""
        other_car = Car.objects.create(
            user=another_user,
            name='Another User Car',
            fuel_type=FuelType.DIESEL,
            avg_consumption=Decimal('7.0'),
            tank_capacity=Decimal('55.0')
        )
        
        response = authenticated_client.delete(f'/api/cars/{other_car.id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Car.objects.filter(id=other_car.id).exists()
    
    def test_delete_nonexistent_car(self, authenticated_client):
        """Test deleting non-existent car."""
        response = authenticated_client.delete('/api/cars/99999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCarMaxRange:
    """Test cases for computed max_range_km field."""
    
    def test_max_range_calculation(self, authenticated_client, user):
        """Test that max_range_km is correctly calculated."""
        car = Car.objects.create(
            user=user,
            name='Test Car',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('8.0'),
            tank_capacity=Decimal('64.0')
        )
        
        response = authenticated_client.get(f'/api/cars/{car.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        
        expected_range = (Decimal('64.0') / Decimal('8.0')) * Decimal('100')
        assert Decimal(str(response.data['max_range_km'])) == expected_range
    
    def test_max_range_read_only(self, authenticated_client, car_gasoline):
        """Test that max_range_km cannot be set via API."""
        update_data = {
            'max_range_km': '9999.99'
        }
        
        response = authenticated_client.patch(
            f'/api/cars/{car_gasoline.id}/',
            update_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        expected_range = (car_gasoline.tank_capacity / car_gasoline.avg_consumption) * Decimal('100')
        assert Decimal(str(response.data['max_range_km'])) == expected_range.quantize(Decimal('0.01'))