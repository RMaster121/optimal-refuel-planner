"""Shared pytest fixtures for the OptimalRefuelPlanner project."""

import pytest
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from fuel_prices.models import Country, FuelPrice
from cars.models import Car
from routes.models import Route
from planner.models import RefuelPlan, RefuelStop
from refuel_planner.choices import FuelType, OptimizationStrategy

User = get_user_model()


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def api_client():
    """Return an API client instance for making API requests."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client with a logged-in user."""
    api_client.force_authenticate(user=user)
    return api_client


# ============================================================================
# USER FIXTURES
# ============================================================================


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def another_user(db):
    """Create another test user for multi-user scenarios."""
    return User.objects.create_user(
        username='anotheruser',
        email='another@example.com',
        password='testpass123'
    )


@pytest.fixture
def user_data():
    """Return sample user registration data for testing registration endpoints."""
    return {
        'email': 'testuser@example.com',
        'password': 'SecurePassword123!',
        'password2': 'SecurePassword123!',
        'first_name': 'Test',
        'last_name': 'User'
    }


@pytest.fixture
def create_user(db):
    """Factory fixture to create users with custom email and password."""
    def _create_user(email='user@example.com', password='TestPass123!'):
        return User.objects.create_user(
            username=email.split('@')[0],
            email=email,
            password=password
        )
    return _create_user


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing admin-only endpoints."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return an authenticated API client with admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


# ============================================================================
# COUNTRY FIXTURES
# ============================================================================

@pytest.fixture
def country_poland(db):
    """Create Poland test country."""
    return Country.objects.create(
        code='PL',
        name='Poland'
    )


@pytest.fixture
def country_germany(db):
    """Create Germany test country."""
    return Country.objects.create(
        code='DE',
        name='Germany'
    )


# ============================================================================
# FUEL PRICE FIXTURES
# ============================================================================

@pytest.fixture
def fuel_price_pl_gasoline(db, country_poland):
    """Create fuel price for Poland, gasoline."""
    return FuelPrice.objects.create(
        country=country_poland,
        fuel_type=FuelType.GASOLINE,
        price_per_liter=Decimal('6.50'),
        scraped_at=timezone.now()
    )


@pytest.fixture
def fuel_price_de_gasoline(db, country_germany):
    """Create fuel price for Germany, gasoline."""
    return FuelPrice.objects.create(
        country=country_germany,
        fuel_type=FuelType.GASOLINE,
        price_per_liter=Decimal('7.20'),
        scraped_at=timezone.now()
    )


@pytest.fixture
def fuel_price_pl_diesel(db, country_poland):
    """Create fuel price for Poland, diesel."""
    return FuelPrice.objects.create(
        country=country_poland,
        fuel_type=FuelType.DIESEL,
        price_per_liter=Decimal('6.80'),
        scraped_at=timezone.now()
    )


# ============================================================================
# CAR FIXTURES
# ============================================================================

@pytest.fixture
def car_gasoline(db, user):
    """Create a test car with gasoline fuel type."""
    return Car.objects.create(
        user=user,
        name='Toyota Corolla',
        fuel_type=FuelType.GASOLINE,
        avg_consumption=Decimal('6.5'),
        tank_capacity=Decimal('50.0')
    )


@pytest.fixture
def car_diesel(db, user):
    """Create a test car with diesel fuel type."""
    return Car.objects.create(
        user=user,
        name='VW Passat',
        fuel_type=FuelType.DIESEL,
        avg_consumption=Decimal('5.5'),
        tank_capacity=Decimal('60.0')
    )


# ============================================================================
# ROUTE FIXTURES
# ============================================================================

@pytest.fixture
def route(db, user):
    """Create a test route."""
    return Route.objects.create(
        user=user,
        google_maps_url='https://maps.google.com/test',
        origin='Warsaw, Poland',
        destination='Berlin, Germany',
        total_distance_km=Decimal('520.00'),
        waypoints=[
            {'lat': 52.2297, 'lng': 21.0122, 'country_code': 'PL', 'distance_from_start': 0},
            {'lat': 52.5200, 'lng': 13.4050, 'country_code': 'DE', 'distance_from_start': 520}
        ],
        countries=['PL', 'DE']
    )


# ============================================================================
# REFUEL PLAN FIXTURES
# ============================================================================

@pytest.fixture
def refuel_plan(db, route, car_gasoline):
    """Create a test refuel plan."""
    return RefuelPlan.objects.create(
        route=route,
        car=car_gasoline,
        reservoir_km=100,
        optimization_strategy=OptimizationStrategy.CHEAPEST,
        total_cost=Decimal('200.00'),
        total_fuel_needed=Decimal('33.80'),
        number_of_stops=2
    )


@pytest.fixture
def refuel_stop(db, refuel_plan, country_poland, fuel_price_pl_gasoline):
    """Create a test refuel stop."""
    return RefuelStop.objects.create(
        plan=refuel_plan,
        stop_number=1,
        country=country_poland,
        fuel_price=fuel_price_pl_gasoline,
        distance_from_start_km=Decimal('250.00'),
        fuel_to_add_liters=Decimal('30.00'),
        total_cost=Decimal('195.00'),
        latitude=Decimal('52.2297'),
        longitude=Decimal('21.0122')
    )