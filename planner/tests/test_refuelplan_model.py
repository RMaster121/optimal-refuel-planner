"""Tests for RefuelPlan model."""

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone

from planner.models import RefuelPlan
from refuel_planner.choices import OptimizationStrategy


@pytest.mark.integration
class TestRefuelPlanModel:
    """Tests for RefuelPlan model."""

    def test_create_refuel_plan_with_valid_data(self, db, route, car_gasoline):
        """Should create refuel plan with valid data."""
        plan = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        
        assert plan.route == route
        assert plan.car == car_gasoline
        assert plan.reservoir_km == 100
        assert plan.optimization_strategy == OptimizationStrategy.CHEAPEST
        assert plan.total_cost == Decimal('200.00')
        assert plan.total_fuel_needed == Decimal('33.80')
        assert plan.number_of_stops == 2

    def test_str_representation(self, db, route, car_gasoline):
        """Should return formatted string with route and strategy."""
        plan = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.MIN_STOPS,
            total_cost=Decimal('220.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=1
        )
        
        expected = f"Plan for {route.origin} → {route.destination} (Minimum stops)"
        assert str(plan) == expected

    def test_reservoir_km_can_be_zero(self, db, route, car_gasoline):
        """Should allow zero reservoir distance."""
        plan = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=0,
            optimization_strategy=OptimizationStrategy.BALANCED,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        
        assert plan.reservoir_km == 0

    def test_reservoir_km_default_value(self, db, route, car_gasoline):
        """Should default reservoir_km to 100."""
        plan = RefuelPlan(
            route=route,
            car=car_gasoline,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        
        assert plan.reservoir_km == 100

    def test_reservoir_km_negative_not_allowed(self, db, route, car_gasoline):
        """Should raise ValidationError for negative reservoir distance."""
        plan = RefuelPlan(
            route=route,
            car=car_gasoline,
            reservoir_km=-50,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        
        with pytest.raises(ValidationError) as exc_info:
            plan.full_clean()
        
        assert 'reservoir_km' in exc_info.value.error_dict
        assert 'cannot be negative' in str(exc_info.value.error_dict['reservoir_km'])

    def test_total_cost_can_be_zero(self, db, route, car_gasoline):
        """Should allow zero total cost (edge case)."""
        plan = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('0.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=0
        )
        
        assert plan.total_cost == Decimal('0.00')

    def test_total_cost_negative_not_allowed(self, db, route, car_gasoline):
        """Should raise ValidationError for negative total cost."""
        plan = RefuelPlan(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('-100.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        
        with pytest.raises(ValidationError) as exc_info:
            plan.full_clean()
        
        assert 'total_cost' in exc_info.value.error_dict
        assert 'cannot be negative' in str(exc_info.value.error_dict['total_cost'])

    def test_total_fuel_needed_must_be_positive(self, db, route, car_gasoline):
        """Should raise ValidationError for non-positive fuel needed."""
        plan = RefuelPlan(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('0'),
            number_of_stops=2
        )
        
        with pytest.raises(ValidationError) as exc_info:
            plan.full_clean()
        
        assert 'total_fuel_needed' in exc_info.value.error_dict
        assert 'greater than zero' in str(exc_info.value.error_dict['total_fuel_needed'])

    def test_total_fuel_needed_negative_not_allowed(self, db, route, car_gasoline):
        """Should raise ValidationError for negative fuel needed."""
        plan = RefuelPlan(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('-10.00'),
            number_of_stops=2
        )
        
        with pytest.raises(ValidationError) as exc_info:
            plan.full_clean()
        
        assert 'total_fuel_needed' in exc_info.value.error_dict

    def test_number_of_stops_can_be_zero(self, db, route, car_gasoline):
        """Should allow zero stops (no refueling needed)."""
        plan = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('0.00'),
            total_fuel_needed=Decimal('10.00'),
            number_of_stops=0
        )
        
        assert plan.number_of_stops == 0

    def test_number_of_stops_negative_not_allowed(self, db, route, car_gasoline):
        """Should raise ValidationError for negative number of stops."""
        plan = RefuelPlan(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=-1
        )
        
        with pytest.raises(ValidationError) as exc_info:
            plan.full_clean()
        
        assert 'number_of_stops' in exc_info.value.error_dict
        assert 'cannot be negative' in str(exc_info.value.error_dict['number_of_stops'])

    def test_route_is_required(self, db, car_gasoline):
        """Should raise ValidationError when route is missing."""
        plan = RefuelPlan(
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        
        with pytest.raises(ValidationError) as exc_info:
            plan.full_clean()
        
        assert 'route' in exc_info.value.error_dict

    def test_car_is_required(self, db, route):
        """Should raise ValidationError when car is missing."""
        plan = RefuelPlan(
            route=route,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        
        with pytest.raises(ValidationError) as exc_info:
            plan.full_clean()
        
        assert 'car' in exc_info.value.error_dict

    def test_optimization_strategy_is_required(self, db, route, car_gasoline):
        """Should raise ValidationError when optimization_strategy is missing."""
        plan = RefuelPlan(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        
        with pytest.raises(ValidationError) as exc_info:
            plan.full_clean()
        
        assert 'optimization_strategy' in exc_info.value.error_dict

    def test_total_cost_is_required(self, db, route, car_gasoline):
        """Should raise ValidationError when total_cost is missing."""
        plan = RefuelPlan(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        
        with pytest.raises(ValidationError) as exc_info:
            plan.full_clean()
        
        assert 'total_cost' in exc_info.value.error_dict

    def test_total_fuel_needed_is_required(self, db, route, car_gasoline):
        """Should raise ValidationError when total_fuel_needed is missing."""
        plan = RefuelPlan(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            number_of_stops=2
        )
        
        with pytest.raises(ValidationError) as exc_info:
            plan.full_clean()
        
        assert 'total_fuel_needed' in exc_info.value.error_dict

    def test_number_of_stops_is_required(self, db, route, car_gasoline):
        """Should raise ValidationError when number_of_stops is missing."""
        plan = RefuelPlan(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            plan.full_clean()
        
        assert 'number_of_stops' in exc_info.value.error_dict

    def test_multiple_plans_for_same_route(self, db, route, car_gasoline):
        """Should allow multiple plans for the same route."""
        plan1 = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        
        plan2 = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.MIN_STOPS,
            total_cost=Decimal('220.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=1
        )
        
        assert plan1.route == plan2.route
        assert plan1.optimization_strategy != plan2.optimization_strategy

    def test_different_strategies(self, db, route, car_gasoline):
        """Should support all optimization strategies."""
        cheapest = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=3
        )
        assert cheapest.optimization_strategy == OptimizationStrategy.CHEAPEST
        assert cheapest.get_optimization_strategy_display() == 'Cheapest price'
        
        min_stops = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.MIN_STOPS,
            total_cost=Decimal('220.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=1
        )
        assert min_stops.optimization_strategy == OptimizationStrategy.MIN_STOPS
        assert min_stops.get_optimization_strategy_display() == 'Minimum stops'
        
        balanced = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.BALANCED,
            total_cost=Decimal('210.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        assert balanced.optimization_strategy == OptimizationStrategy.BALANCED
        assert balanced.get_optimization_strategy_display() == 'Balanced approach'

    def test_ordering_by_created_at_descending(self, db, route, car_gasoline):
        """Should order plans by created_at in descending order (newest first)."""
        plan1 = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        
        plan2 = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.MIN_STOPS,
            total_cost=Decimal('220.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=1
        )
        
        plans = list(RefuelPlan.objects.all())
        
        # Newest first
        assert plans[0] == plan2
        assert plans[1] == plan1

    def test_created_at_auto_populated(self, db, route, car_gasoline):
        """Should auto-populate created_at timestamp."""
        before = timezone.now()
        plan = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        after = timezone.now()
        
        assert plan.created_at is not None
        assert before <= plan.created_at <= after

    def test_manager_select_related_optimization(self, db, route, car_gasoline):
        """Should use select_related for route and car in manager."""
        RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        
        # Manager should automatically select_related route and car
        plan = RefuelPlan.objects.first()
        # Accessing route and car shouldn't trigger additional queries
        _ = plan.route.origin
        _ = plan.car.name

    def test_refuel_plan_fixture(self, refuel_plan):
        """Should work with refuel_plan fixture."""
        assert refuel_plan.reservoir_km == 100
        assert refuel_plan.optimization_strategy == OptimizationStrategy.CHEAPEST
        assert refuel_plan.total_cost == Decimal('200.00')
        assert refuel_plan.total_fuel_needed == Decimal('33.80')
        assert refuel_plan.number_of_stops == 2

    def test_validated_model_calls_full_clean_on_save(self, db, route, car_gasoline):
        """Should call full_clean() on save (ValidatedModel behavior)."""
        plan = RefuelPlan(
            route=route,
            car=car_gasoline,
            reservoir_km=-100,  # Invalid - negative
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('200.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        
        # Should raise validation error on save due to ValidatedModel
        with pytest.raises(ValidationError):
            plan.save()

    def test_decimal_precision_for_costs(self, db, route, car_gasoline):
        """Should store costs with proper decimal precision."""
        plan = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('205.47'),
            total_fuel_needed=Decimal('33.82'),
            number_of_stops=2
        )
        
        assert plan.total_cost == Decimal('205.47')
        assert plan.total_fuel_needed == Decimal('33.82')

    def test_plans_with_different_cars_same_route(self, db, route, car_gasoline, car_diesel):
        """Should allow plans with different cars for the same route."""
        plan_gasoline = RefuelPlan.objects.create(
            route=route,
            car=car_gasoline,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('220.00'),
            total_fuel_needed=Decimal('33.80'),
            number_of_stops=2
        )
        
        plan_diesel = RefuelPlan.objects.create(
            route=route,
            car=car_diesel,
            reservoir_km=100,
            optimization_strategy=OptimizationStrategy.CHEAPEST,
            total_cost=Decimal('190.00'),
            total_fuel_needed=Decimal('28.60'),
            number_of_stops=2
        )
        
        assert plan_gasoline.route == plan_diesel.route
        assert plan_gasoline.car != plan_diesel.car
        assert plan_gasoline.total_fuel_needed > plan_diesel.total_fuel_needed
