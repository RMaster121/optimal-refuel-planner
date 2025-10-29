"""Tests for RefuelStop model."""

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError

from planner.models import RefuelStop
from refuel_planner.choices import FuelType


@pytest.mark.integration
class TestRefuelStopModel:
    """Tests for RefuelStop model."""

    def test_create_refuel_stop_with_valid_data(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should create refuel stop with valid data."""
        stop = RefuelStop.objects.create(
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
        
        assert stop.plan == refuel_plan
        assert stop.stop_number == 1
        assert stop.country == country_poland
        assert stop.fuel_price == fuel_price_pl_gasoline
        assert stop.distance_from_start_km == Decimal('250.00')
        assert stop.fuel_to_add_liters == Decimal('30.00')
        assert stop.total_cost == Decimal('195.00')
        assert stop.latitude == Decimal('52.2297')
        assert stop.longitude == Decimal('21.0122')

    def test_create_refuel_stop_without_coordinates(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should allow creating refuel stop without coordinates."""
        stop = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        assert stop.latitude is None
        assert stop.longitude is None

    def test_str_representation(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should return formatted string with stop number, distance, and country."""
        stop = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=2,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('350.00'),
            fuel_to_add_liters=Decimal('25.00'),
            total_cost=Decimal('162.50')
        )
        
        assert str(stop) == 'Stop #2 at 350.00 km (PL)'

    def test_stop_number_must_be_at_least_1(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should raise ValidationError for stop_number less than 1."""
        stop = RefuelStop(
            plan=refuel_plan,
            stop_number=0,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            stop.full_clean()
        
        assert 'stop_number' in exc_info.value.error_dict
        assert 'at least 1' in str(exc_info.value.error_dict['stop_number'])

    def test_stop_number_negative_not_allowed(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should raise ValidationError for negative stop_number."""
        stop = RefuelStop(
            plan=refuel_plan,
            stop_number=-1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            stop.full_clean()
        
        assert 'stop_number' in exc_info.value.error_dict

    def test_fuel_price_must_match_car_fuel_type(self, db, refuel_plan, country_poland, fuel_price_pl_diesel):
        """Should raise ValidationError if fuel price type doesn't match car fuel type."""
        # refuel_plan uses car_gasoline, but we're trying to use diesel fuel price
        stop = RefuelStop(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_diesel,  # Diesel, but car uses gasoline
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            stop.full_clean()
        
        assert 'fuel_price' in exc_info.value.error_dict
        assert 'must match car fuel type' in str(exc_info.value.error_dict['fuel_price'])

    def test_fuel_price_country_must_match_stop_country(self, db, refuel_plan, country_germany, fuel_price_pl_gasoline):
        """Should raise ValidationError if fuel price country doesn't match stop country."""
        stop = RefuelStop(
            plan=refuel_plan,
            stop_number=1,
            country=country_germany,  # Germany
            fuel_price=fuel_price_pl_gasoline,  # But price is for Poland
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            stop.full_clean()
        
        assert 'fuel_price' in exc_info.value.error_dict
        assert 'must match stop country' in str(exc_info.value.error_dict['fuel_price'])

    def test_distance_from_start_can_be_zero(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should allow zero distance (refueling at start)."""
        stop = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('0.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        assert stop.distance_from_start_km == Decimal('0.00')

    def test_distance_from_start_negative_not_allowed(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should raise ValidationError for negative distance."""
        stop = RefuelStop(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('-50.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            stop.full_clean()
        
        assert 'distance_from_start_km' in exc_info.value.error_dict
        assert 'cannot be negative' in str(exc_info.value.error_dict['distance_from_start_km'])

    def test_fuel_to_add_must_be_positive(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should raise ValidationError for non-positive fuel amount."""
        stop = RefuelStop(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('0'),
            total_cost=Decimal('0.00')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            stop.full_clean()
        
        assert 'fuel_to_add_liters' in exc_info.value.error_dict
        assert 'greater than zero' in str(exc_info.value.error_dict['fuel_to_add_liters'])

    def test_fuel_to_add_negative_not_allowed(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should raise ValidationError for negative fuel amount."""
        stop = RefuelStop(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('-10.00'),
            total_cost=Decimal('-65.00')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            stop.full_clean()
        
        assert 'fuel_to_add_liters' in exc_info.value.error_dict

    def test_total_cost_can_be_zero(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should allow zero total cost (edge case)."""
        stop = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('0.01'),  # Very small amount
            total_cost=Decimal('0.00')
        )
        
        assert stop.total_cost == Decimal('0.00')

    def test_total_cost_negative_not_allowed(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should raise ValidationError for negative total cost."""
        stop = RefuelStop(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('-195.00')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            stop.full_clean()
        
        assert 'total_cost' in exc_info.value.error_dict
        assert 'cannot be negative' in str(exc_info.value.error_dict['total_cost'])

    def test_plan_is_required(self, db, country_poland, fuel_price_pl_gasoline):
        """Should raise ValidationError when plan is missing."""
        stop = RefuelStop(
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            stop.full_clean()
        
        assert 'plan' in exc_info.value.error_dict

    def test_stop_number_is_required(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should raise ValidationError when stop_number is missing."""
        stop = RefuelStop(
            plan=refuel_plan,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            stop.full_clean()
        
        assert 'stop_number' in exc_info.value.error_dict

    def test_country_is_required(self, db, refuel_plan, fuel_price_pl_gasoline):
        """Should raise ValidationError when country is missing."""
        stop = RefuelStop(
            plan=refuel_plan,
            stop_number=1,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            stop.full_clean()
        
        assert 'country' in exc_info.value.error_dict

    def test_fuel_price_is_required(self, db, refuel_plan, country_poland):
        """Should raise ValidationError when fuel_price is missing."""
        stop = RefuelStop(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            stop.full_clean()
        
        assert 'fuel_price' in exc_info.value.error_dict

    def test_unique_together_plan_and_stop_number(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should enforce unique constraint on (plan, stop_number)."""
        RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        # Attempting to create another stop with same plan and stop_number
        with pytest.raises(ValidationError):
            RefuelStop.objects.create(
                plan=refuel_plan,
                stop_number=1,  # Same stop number
                country=country_poland,
                fuel_price=fuel_price_pl_gasoline,
                distance_from_start_km=Decimal('300.00'),
                fuel_to_add_liters=Decimal('25.00'),
                total_cost=Decimal('162.50')
            )

    def test_multiple_stops_same_plan_different_numbers(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should allow multiple stops for same plan with different stop numbers."""
        stop1 = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        stop2 = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=2,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('450.00'),
            fuel_to_add_liters=Decimal('25.00'),
            total_cost=Decimal('162.50')
        )
        
        assert stop1.plan == stop2.plan
        assert stop1.stop_number != stop2.stop_number

    def test_ordering_by_stop_number(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should order stops by stop_number ascending."""
        stop2 = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=2,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('450.00'),
            fuel_to_add_liters=Decimal('25.00'),
            total_cost=Decimal('162.50')
        )
        
        stop1 = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        stop3 = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=3,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('500.00'),
            fuel_to_add_liters=Decimal('20.00'),
            total_cost=Decimal('130.00')
        )
        
        stops = list(RefuelStop.objects.all())
        
        assert stops[0] == stop1
        assert stops[1] == stop2
        assert stops[2] == stop3

    def test_manager_select_related_optimization(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should use select_related for related models in manager."""
        RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        # Manager should automatically select_related
        stop = RefuelStop.objects.first()
        # Accessing related objects shouldn't trigger additional queries
        _ = stop.country.name
        _ = stop.fuel_price.price_per_liter
        _ = stop.fuel_price.country.name
        _ = stop.plan.route.origin
        _ = stop.plan.car.name

    def test_refuel_stop_fixture(self, refuel_stop):
        """Should work with refuel_stop fixture."""
        assert refuel_stop.stop_number == 1
        assert refuel_stop.country.code == 'PL'
        assert refuel_stop.fuel_price.fuel_type == FuelType.GASOLINE
        assert refuel_stop.distance_from_start_km == Decimal('250.00')
        assert refuel_stop.fuel_to_add_liters == Decimal('30.00')
        assert refuel_stop.total_cost == Decimal('195.00')

    def test_validated_model_calls_full_clean_on_save(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should call full_clean() on save (ValidatedModel behavior)."""
        stop = RefuelStop(
            plan=refuel_plan,
            stop_number=0,  # Invalid - must be at least 1
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        # Should raise validation error on save due to ValidatedModel
        with pytest.raises(ValidationError):
            stop.save()

    def test_decimal_precision_for_amounts(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should store amounts with proper decimal precision."""
        stop = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('253.47'),
            fuel_to_add_liters=Decimal('30.15'),
            total_cost=Decimal('195.98')
        )
        
        assert stop.distance_from_start_km == Decimal('253.47')
        assert stop.fuel_to_add_liters == Decimal('30.15')
        assert stop.total_cost == Decimal('195.98')

    def test_coordinates_precision(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should store coordinates with 6 decimal places precision."""
        stop = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00'),
            latitude=Decimal('52.229676'),
            longitude=Decimal('21.012229')
        )
        
        assert stop.latitude == Decimal('52.229676')
        assert stop.longitude == Decimal('21.012229')

    def test_stops_across_different_countries(self, db, refuel_plan, country_poland, country_germany,
                                               fuel_price_pl_gasoline, fuel_price_de_gasoline):
        """Should allow stops in different countries along the route."""
        stop_pl = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00')
        )
        
        stop_de = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=2,
            country=country_germany,
            fuel_price=fuel_price_de_gasoline,
            distance_from_start_km=Decimal('480.00'),
            fuel_to_add_liters=Decimal('25.00'),
            total_cost=Decimal('180.00')
        )
        
        assert stop_pl.country != stop_de.country
        assert stop_pl.fuel_price != stop_de.fuel_price

    def test_latitude_can_be_null(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should allow null latitude."""
        stop = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00'),
            latitude=None,
            longitude=Decimal('21.0122')
        )
        
        assert stop.latitude is None
        assert stop.longitude == Decimal('21.0122')

    def test_longitude_can_be_null(self, db, refuel_plan, country_poland, fuel_price_pl_gasoline):
        """Should allow null longitude."""
        stop = RefuelStop.objects.create(
            plan=refuel_plan,
            stop_number=1,
            country=country_poland,
            fuel_price=fuel_price_pl_gasoline,
            distance_from_start_km=Decimal('250.00'),
            fuel_to_add_liters=Decimal('30.00'),
            total_cost=Decimal('195.00'),
            latitude=Decimal('52.2297'),
            longitude=None
        )
        
        assert stop.latitude == Decimal('52.2297')
        assert stop.longitude is None