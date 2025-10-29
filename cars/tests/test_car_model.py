"""Tests for Car model."""

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from cars.models import Car
from refuel_planner.choices import FuelType


@pytest.mark.integration
class TestCarModel:
    """Tests for Car model."""

    def test_create_car_with_valid_data(self, db, user):
        """Should create car with valid data."""
        car = Car.objects.create(
            user=user,
            name='Toyota Corolla',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        
        assert car.user == user
        assert car.name == 'Toyota Corolla'
        assert car.fuel_type == FuelType.GASOLINE
        assert car.avg_consumption == Decimal('6.5')
        assert car.tank_capacity == Decimal('50.0')

    def test_str_representation(self, db, user):
        """Should return formatted string with name and fuel type."""
        car = Car.objects.create(
            user=user,
            name='VW Passat',
            fuel_type=FuelType.DIESEL,
            avg_consumption=Decimal('5.5'),
            tank_capacity=Decimal('60.0')
        )
        
        assert str(car) == 'VW Passat (Diesel)'

    def test_max_range_km_property(self, db, user):
        """Should calculate max range correctly."""
        car = Car.objects.create(
            user=user,
            name='Test Car',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('8.0'),  # 8L per 100km
            tank_capacity=Decimal('40.0')    # 40L tank
        )
        
        # (40L / 8L per 100km) * 100km = 500km
        expected_range = Decimal('500.00')
        assert car.max_range_km == expected_range

    def test_max_range_km_with_low_consumption(self, db, user):
        """Should calculate max range for low consumption vehicle."""
        car = Car.objects.create(
            user=user,
            name='Efficient Car',
            fuel_type=FuelType.DIESEL,
            avg_consumption=Decimal('4.5'),
            tank_capacity=Decimal('50.0')
        )
        
        # (50 / 4.5) * 100 = 1111.111... km
        assert car.max_range_km > Decimal('1111')
        assert car.max_range_km < Decimal('1112')

    def test_max_range_km_returns_zero_for_zero_consumption(self, db, user):
        """Should return zero range if consumption is zero (edge case)."""
        car = Car(
            user=user,
            name='Test Car',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('0'),
            tank_capacity=Decimal('50.0')
        )
        
        # This will fail validation, but test the property logic
        assert car.max_range_km == Decimal('0')

    def test_max_range_km_handles_none_values(self, db, user):
        """Should return zero if consumption or capacity is None."""
        car = Car(
            user=user,
            name='Test Car',
            fuel_type=FuelType.GASOLINE
        )
        
        assert car.max_range_km == Decimal('0')

    def test_name_sanitization(self, db, user):
        """Should sanitize car name on validation."""
        car = Car(
            user=user,
            name='  Toyota Corolla  ',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        
        car.full_clean()
        assert car.name == 'Toyota Corolla'  # Whitespace stripped

    def test_name_rejects_script_tags(self, db, user):
        """Should reject name with script tags."""
        car = Car(
            user=user,
            name='<script>alert("XSS")</script>',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            car.full_clean()
        
        assert 'name' in exc_info.value.error_dict

    def test_name_rejects_javascript_protocol(self, db, user):
        """Should reject name with javascript: protocol."""
        car = Car(
            user=user,
            name='javascript:alert(1)',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            car.full_clean()
        
        assert 'name' in exc_info.value.error_dict

    def test_avg_consumption_must_be_positive(self, db, user):
        """Should raise ValidationError for non-positive consumption."""
        car = Car(
            user=user,
            name='Test Car',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('0'),
            tank_capacity=Decimal('50.0')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            car.full_clean()
        
        assert 'avg_consumption' in exc_info.value.error_dict
        assert 'greater than zero' in str(exc_info.value.error_dict['avg_consumption'])

    def test_avg_consumption_negative_not_allowed(self, db, user):
        """Should raise ValidationError for negative consumption."""
        car = Car(
            user=user,
            name='Test Car',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('-5.0'),
            tank_capacity=Decimal('50.0')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            car.full_clean()
        
        assert 'avg_consumption' in exc_info.value.error_dict

    def test_tank_capacity_must_be_positive(self, db, user):
        """Should raise ValidationError for non-positive tank capacity."""
        car = Car(
            user=user,
            name='Test Car',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('0')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            car.full_clean()
        
        assert 'tank_capacity' in exc_info.value.error_dict
        assert 'greater than zero' in str(exc_info.value.error_dict['tank_capacity'])

    def test_tank_capacity_negative_not_allowed(self, db, user):
        """Should raise ValidationError for negative tank capacity."""
        car = Car(
            user=user,
            name='Test Car',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('-50.0')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            car.full_clean()
        
        assert 'tank_capacity' in exc_info.value.error_dict

    def test_user_is_required(self, db):
        """Should raise ValidationError when user is missing."""
        car = Car(
            name='Test Car',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            car.full_clean()
        
        assert 'user' in exc_info.value.error_dict

    def test_name_is_required(self, db, user):
        """Should raise ValidationError when name is missing."""
        car = Car(
            user=user,
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            car.full_clean()
        
        assert 'name' in exc_info.value.error_dict

    def test_fuel_type_is_required(self, db, user):
        """Should raise ValidationError when fuel_type is missing."""
        car = Car(
            user=user,
            name='Test Car',
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            car.full_clean()
        
        assert 'fuel_type' in exc_info.value.error_dict

    def test_unique_together_user_and_name(self, db, user):
        """Should enforce unique constraint on (user, name)."""
        Car.objects.create(
            user=user,
            name='Toyota Corolla',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        
        # Attempting to create another car with same user and name
        with pytest.raises(ValidationError):
            Car.objects.create(
                user=user,
                name='Toyota Corolla',
                fuel_type=FuelType.DIESEL,
                avg_consumption=Decimal('5.5'),
                tank_capacity=Decimal('60.0')
            )

    def test_same_name_different_users_allowed(self, db, user, another_user):
        """Should allow same car name for different users."""
        car1 = Car.objects.create(
            user=user,
            name='Toyota Corolla',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        
        car2 = Car.objects.create(
            user=another_user,
            name='Toyota Corolla',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        
        assert car1.name == car2.name
        assert car1.user != car2.user

    def test_different_names_same_user_allowed(self, db, user):
        """Should allow different car names for the same user."""
        car1 = Car.objects.create(
            user=user,
            name='Toyota Corolla',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        
        car2 = Car.objects.create(
            user=user,
            name='VW Passat',
            fuel_type=FuelType.DIESEL,
            avg_consumption=Decimal('5.5'),
            tank_capacity=Decimal('60.0')
        )
        
        assert car1.user == car2.user
        assert car1.name != car2.name

    def test_ordering_by_name(self, db, user):
        """Should order cars by name."""
        Car.objects.create(
            user=user,
            name='VW Passat',
            fuel_type=FuelType.DIESEL,
            avg_consumption=Decimal('5.5'),
            tank_capacity=Decimal('60.0')
        )
        
        Car.objects.create(
            user=user,
            name='Toyota Corolla',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        
        Car.objects.create(
            user=user,
            name='Audi A4',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('7.0'),
            tank_capacity=Decimal('55.0')
        )
        
        cars = list(Car.objects.all())
        
        assert cars[0].name == 'Audi A4'
        assert cars[1].name == 'Toyota Corolla'
        assert cars[2].name == 'VW Passat'

    def test_timestamps_auto_populated(self, db, user):
        """Should auto-populate created_at and updated_at."""
        before = timezone.now()
        car = Car.objects.create(
            user=user,
            name='Test Car',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        after = timezone.now()
        
        assert car.created_at is not None
        assert car.updated_at is not None
        assert before <= car.created_at <= after
        assert before <= car.updated_at <= after

    def test_fuel_type_choices(self, db, user):
        """Should only allow valid fuel type choices."""
        gasoline_car = Car.objects.create(
            user=user,
            name='Gasoline Car',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        assert gasoline_car.fuel_type == FuelType.GASOLINE
        
        diesel_car = Car.objects.create(
            user=user,
            name='Diesel Car',
            fuel_type=FuelType.DIESEL,
            avg_consumption=Decimal('5.5'),
            tank_capacity=Decimal('60.0')
        )
        assert diesel_car.fuel_type == FuelType.DIESEL

    def test_get_fuel_type_display(self, db, user):
        """Should return human-readable fuel type display."""
        gasoline_car = Car.objects.create(
            user=user,
            name='Gasoline Car',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        assert gasoline_car.get_fuel_type_display() == 'Gasoline'
        
        diesel_car = Car.objects.create(
            user=user,
            name='Diesel Car',
            fuel_type=FuelType.DIESEL,
            avg_consumption=Decimal('5.5'),
            tank_capacity=Decimal('60.0')
        )
        assert diesel_car.get_fuel_type_display() == 'Diesel'

    def test_car_fixtures(self, car_gasoline, car_diesel):
        """Should work with car fixtures."""
        assert car_gasoline.name == 'Toyota Corolla'
        assert car_gasoline.fuel_type == FuelType.GASOLINE
        assert car_gasoline.avg_consumption == Decimal('6.5')
        assert car_gasoline.tank_capacity == Decimal('50.0')
        
        assert car_diesel.name == 'VW Passat'
        assert car_diesel.fuel_type == FuelType.DIESEL
        assert car_diesel.avg_consumption == Decimal('5.5')
        assert car_diesel.tank_capacity == Decimal('60.0')

    def test_validated_model_calls_full_clean_on_save(self, db, user):
        """Should call full_clean() on save (ValidatedModel behavior)."""
        car = Car(
            user=user,
            name='Test Car',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('0'),  # Invalid - not positive
            tank_capacity=Decimal('50.0')
        )
        
        # Should raise validation error on save due to ValidatedModel
        with pytest.raises(ValidationError):
            car.save()

    def test_name_max_length_validation(self, db, user):
        """Should validate max_length for name."""
        long_name = 'A' * 150  # Exceeds max_length of 100
        car = Car(
            user=user,
            name=long_name,
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.0')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            car.full_clean()
        
        assert 'name' in exc_info.value.error_dict

    def test_unicode_in_name(self, db, user):
        """Should accept unicode characters in name."""
        car = Car.objects.create(
            user=user,
            name='Škoda Octavia',
            fuel_type=FuelType.DIESEL,
            avg_consumption=Decimal('5.8'),
            tank_capacity=Decimal('55.0')
        )
        
        assert 'Škoda' in car.name

    def test_decimal_precision_for_consumption(self, db, user):
        """Should store consumption with proper decimal precision."""
        car = Car.objects.create(
            user=user,
            name='Test Car',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.53'),
            tank_capacity=Decimal('50.0')
        )
        
        assert car.avg_consumption == Decimal('6.53')

    def test_decimal_precision_for_tank_capacity(self, db, user):
        """Should store tank capacity with proper decimal precision."""
        car = Car.objects.create(
            user=user,
            name='Test Car',
            fuel_type=FuelType.GASOLINE,
            avg_consumption=Decimal('6.5'),
            tank_capacity=Decimal('50.75')
        )
        
        assert car.tank_capacity == Decimal('50.75')