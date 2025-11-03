"""Tests for the PlannerService."""

from decimal import Decimal

import pytest
from django.utils import timezone

from fuel_prices.models import FuelPrice
from planner.exceptions import PlanningError
from planner.models import RefuelPlan, RefuelStop
from planner.services.planner_service import PlannerService
from refuel_planner.choices import OptimizationStrategy


@pytest.mark.django_db
class TestPlannerServiceCreate:
    """Test cases for creating refuel plans via service."""

    def test_create_plan_success(
        self, 
        route, 
        car_gasoline, 
        fuel_price_pl_gasoline,
        fuel_price_de_gasoline
    ):
        """Test successfully creating a complete refuel plan."""
        service = PlannerService(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            strategy=OptimizationStrategy.MIN_STOPS
        )
        
        plan = service.create_plan()
        
        assert plan.id is not None
        assert plan.route == route
        assert plan.car == car_gasoline
        assert plan.reservoir_km == 100
        assert plan.optimization_strategy == OptimizationStrategy.MIN_STOPS
        assert plan.total_cost >= Decimal('0')
        assert plan.total_fuel_needed >= Decimal('0')
        assert plan.number_of_stops >= 0
        assert RefuelPlan.objects.filter(id=plan.id).exists()

    def test_create_plan_missing_fuel_price_data(self, route, car_gasoline, country_poland):
        """Test error when fuel price data is missing for route countries."""
        FuelPrice.objects.create(
            country=country_poland,
            fuel_type='gasoline',
            price_per_liter=Decimal('1.450'),
            scraped_at=timezone.now()
        )
        
        service = PlannerService(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            strategy=OptimizationStrategy.MIN_STOPS
        )
        
        with pytest.raises(PlanningError, match="Missing fuel price data"):
            service.create_plan()

    def test_create_plan_creates_database_records(
        self,
        route,
        car_gasoline,
        fuel_price_pl_gasoline,
        fuel_price_de_gasoline
    ):
        """Test RefuelPlan and RefuelStop records are created correctly."""
        service = PlannerService(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            strategy=OptimizationStrategy.MIN_STOPS
        )
        
        initial_plan_count = RefuelPlan.objects.count()
        
        plan = service.create_plan()
        
        assert RefuelPlan.objects.count() == initial_plan_count + 1
        assert RefuelStop.objects.filter(plan=plan).count() == plan.number_of_stops
        
        if plan.number_of_stops > 0:
            stops = RefuelStop.objects.filter(plan=plan).order_by('stop_number')
            
            for i, stop in enumerate(stops, start=1):
                assert stop.stop_number == i
                assert stop.distance_from_start_km >= Decimal('0')
                assert stop.fuel_to_add_liters > Decimal('0')
                assert stop.total_cost > Decimal('0')

    def test_create_plan_multiple_plans_same_route(
        self,
        route,
        car_gasoline,
        fuel_price_pl_gasoline,
        fuel_price_de_gasoline
    ):
        """Test creating multiple plans for the same route with different settings."""
        service1 = PlannerService(
            route=route,
            car=car_gasoline,
            reservoir_km=50,
            strategy=OptimizationStrategy.MIN_STOPS
        )
        
        service2 = PlannerService(
            route=route,
            car=car_gasoline,
            reservoir_km=150,
            strategy=OptimizationStrategy.MIN_STOPS
        )
        
        plan1 = service1.create_plan()
        plan2 = service2.create_plan()
        
        assert plan1.id != plan2.id
        assert RefuelPlan.objects.filter(route=route).count() == 2
        assert plan1.reservoir_km == 50
        assert plan2.reservoir_km == 150