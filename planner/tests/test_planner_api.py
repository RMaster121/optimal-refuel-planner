"""Tests for Refuel Planner API endpoints."""

from decimal import Decimal

import pytest
from rest_framework import status

from planner.models import RefuelPlan
from refuel_planner.choices import OptimizationStrategy


@pytest.mark.django_db
class TestRefuelPlanCreate:
    """Test cases for creating refuel plans."""

    def test_create_plan_authenticated(
        self,
        authenticated_client,
        route,
        car_gasoline,
        fuel_price_pl_gasoline,
        fuel_price_de_gasoline
    ):
        """Test authenticated user can create refuel plan."""
        plan_data = {
            'route': route.id,
            'car': car_gasoline.id,
            'reservoir_km': 100,
            'optimization_strategy': OptimizationStrategy.MIN_STOPS
        }
        
        response = authenticated_client.post('/api/refuel-plans/', plan_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['route']['id'] == route.id
        assert response.data['car']['id'] == car_gasoline.id
        assert response.data['reservoir_km'] == 100
        assert response.data['optimization_strategy'] == OptimizationStrategy.MIN_STOPS
        assert 'stops' in response.data
        assert 'total_cost' in response.data
        assert RefuelPlan.objects.filter(route=route, car=car_gasoline).exists()

    def test_create_plan_unauthenticated(self, api_client, route, car_gasoline):
        """Test unauthenticated user cannot create refuel plan."""
        plan_data = {
            'route': route.id,
            'car': car_gasoline.id,
            'reservoir_km': 100,
            'optimization_strategy': OptimizationStrategy.MIN_STOPS
        }
        
        response = api_client.post('/api/refuel-plans/', plan_data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_plan_invalid_route_id(
        self,
        authenticated_client,
        car_gasoline,
        fuel_price_pl_gasoline
    ):
        """Test creating plan with non-existent route ID."""
        plan_data = {
            'route': 99999,
            'car': car_gasoline.id,
            'reservoir_km': 100,
            'optimization_strategy': OptimizationStrategy.MIN_STOPS
        }
        
        response = authenticated_client.post('/api/refuel-plans/', plan_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'route' in response.data

    def test_create_plan_invalid_car_id(
        self,
        authenticated_client,
        route,
        fuel_price_pl_gasoline
    ):
        """Test creating plan with non-existent car ID."""
        plan_data = {
            'route': route.id,
            'car': 99999,
            'reservoir_km': 100,
            'optimization_strategy': OptimizationStrategy.MIN_STOPS
        }
        
        response = authenticated_client.post('/api/refuel-plans/', plan_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'car' in response.data

    def test_create_plan_route_belongs_to_other_user(
        self,
        authenticated_client,
        another_user,
        car_gasoline,
        fuel_price_pl_gasoline
    ):
        """Test cannot create plan with another user's route."""
        from routes.models import Route
        
        other_route = Route.objects.create(
            user=another_user,
            origin='Paris, France',
            destination='London, UK',
            total_distance_km=Decimal('450.00'),
            waypoints=[
                {'lat': 48.8566, 'lng': 2.3522, 'country_code': 'FR', 'distance_from_start_km': 0},
                {'lat': 51.5074, 'lng': -0.1278, 'country_code': 'UK', 'distance_from_start_km': 450}
            ],
            countries=['FR', 'UK']
        )
        
        plan_data = {
            'route': other_route.id,
            'car': car_gasoline.id,
            'reservoir_km': 100,
            'optimization_strategy': OptimizationStrategy.MIN_STOPS
        }
        
        response = authenticated_client.post('/api/refuel-plans/', plan_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'route' in response.data

    def test_create_plan_planning_error_returns_400(
        self,
        authenticated_client,
        car_gasoline,
        fuel_price_pl_gasoline
    ):
        """Test planning error returns 400 with error message."""
        from routes.models import Route
        
        # Create route with segment that exceeds car range
        impossible_route = Route.objects.create(
            user=authenticated_client.handler._force_user,
            origin='Start',
            destination='End',
            total_distance_km=Decimal('1000.00'),
            waypoints=[
                {'lat': 52.0, 'lng': 21.0, 'country_code': 'PL', 'distance_from_start_km': 0},
                {'lat': 55.0, 'lng': 28.0, 'country_code': 'PL', 'distance_from_start_km': 1000}
            ],
            countries=['PL']
        )
        
        plan_data = {
            'route': impossible_route.id,
            'car': car_gasoline.id,
            'reservoir_km': 100,
            'optimization_strategy': OptimizationStrategy.MIN_STOPS
        }
        
        response = authenticated_client.post('/api/refuel-plans/', plan_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data or 'detail' in response.data


@pytest.mark.django_db
class TestRefuelPlanList:
    """Test cases for listing refuel plans."""

    def test_list_user_plans(
        self,
        authenticated_client,
        refuel_plan,
        fuel_price_pl_gasoline,
        fuel_price_de_gasoline
    ):
        """Test authenticated user can list their own plans."""
        response = authenticated_client.get('/api/refuel-plans/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert response.data['count'] >= 1
        assert response.data['results'][0]['route']['origin'] == 'Warsaw, Poland'

    def test_list_plans_filters_by_user(
        self,
        authenticated_client,
        refuel_plan,
        another_user,
        car_diesel,
        fuel_price_pl_gasoline
    ):
        """Test users only see their own plans."""
        from routes.models import Route
        
        other_route = Route.objects.create(
            user=another_user,
            origin='Paris, France',
            destination='London, UK',
            total_distance_km=Decimal('450.00'),
            waypoints=[
                {'lat': 48.8566, 'lng': 2.3522, 'country_code': 'FR', 'distance_from_start_km': 0},
                {'lat': 51.5074, 'lng': -0.1278, 'country_code': 'UK', 'distance_from_start_km': 450}
            ],
            countries=['FR', 'UK']
        )
        
        RefuelPlan.objects.create(
            route=other_route,
            car=car_diesel,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.MIN_STOPS,
            total_cost=Decimal('50.00'),
            total_fuel_needed=Decimal('30.00'),
            number_of_stops=1
        )
        
        response = authenticated_client.get('/api/refuel-plans/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_list_plans_unauthenticated(self, api_client):
        """Test unauthenticated user cannot list plans."""
        response = api_client.get('/api/refuel-plans/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestRefuelPlanRetrieve:
    """Test cases for retrieving a single refuel plan."""

    def test_retrieve_plan(self, authenticated_client, refuel_plan):
        """Test retrieving own plan details."""
        response = authenticated_client.get(f'/api/refuel-plans/{refuel_plan.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == refuel_plan.id
        assert 'route' in response.data
        assert 'car' in response.data
        assert 'stops' in response.data
        assert 'total_cost' in response.data

    def test_retrieve_other_user_plan_returns_404(
        self,
        authenticated_client,
        another_user,
        car_diesel,
        fuel_price_pl_gasoline
    ):
        """Test user cannot retrieve another user's plan."""
        from routes.models import Route
        
        other_route = Route.objects.create(
            user=another_user,
            origin='Paris, France',
            destination='London, UK',
            total_distance_km=Decimal('450.00'),
            waypoints=[
                {'lat': 48.8566, 'lng': 2.3522, 'country_code': 'FR', 'distance_from_start_km': 0},
                {'lat': 51.5074, 'lng': -0.1278, 'country_code': 'UK', 'distance_from_start_km': 450}
            ],
            countries=['FR', 'UK']
        )
        
        other_plan = RefuelPlan.objects.create(
            route=other_route,
            car=car_diesel,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.MIN_STOPS,
            total_cost=Decimal('50.00'),
            total_fuel_needed=Decimal('30.00'),
            number_of_stops=1
        )
        
        response = authenticated_client.get(f'/api/refuel-plans/{other_plan.id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestRefuelPlanDelete:
    """Test cases for deleting refuel plans."""

    def test_delete_plan(self, authenticated_client, refuel_plan):
        """Test successful plan deletion."""
        plan_id = refuel_plan.id
        
        response = authenticated_client.delete(f'/api/refuel-plans/{plan_id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not RefuelPlan.objects.filter(id=plan_id).exists()

    def test_delete_plan_unauthenticated(self, api_client, refuel_plan):
        """Test unauthenticated user cannot delete plan."""
        response = api_client.delete(f'/api/refuel-plans/{refuel_plan.id}/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert RefuelPlan.objects.filter(id=refuel_plan.id).exists()