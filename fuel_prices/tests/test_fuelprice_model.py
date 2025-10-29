"""Tests for FuelPrice model."""

from django.core.exceptions import ValidationError

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from fuel_prices.models import Country, FuelPrice
from refuel_planner.choices import FuelType


@pytest.mark.integration
class TestFuelPriceModel:
    """Tests for FuelPrice model."""

    def test_create_fuel_price_with_valid_data(self, db, country_poland):
        """Should create fuel price with valid data."""
        scraped_time = timezone.now()
        fuel_price = FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.50'),
            scraped_at=scraped_time
        )
        
        assert fuel_price.country == country_poland
        assert fuel_price.fuel_type == FuelType.GASOLINE
        assert fuel_price.price_per_liter == Decimal('6.50')
        assert fuel_price.scraped_at == scraped_time

    def test_str_representation(self, db, country_poland):
        """Should return formatted string with country code, fuel type, and price."""
        fuel_price = FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.DIESEL,
            price_per_liter=Decimal('6.80'),
            scraped_at=timezone.now()
        )
        
        assert str(fuel_price) == 'PL Diesel - 6.80'

    def test_country_code_property(self, db, country_poland):
        """Should return country code via property."""
        fuel_price = FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.50'),
            scraped_at=timezone.now()
        )
        
        assert fuel_price.country_code == 'PL'

    def test_country_name_property(self, db, country_poland):
        """Should return country name via property."""
        fuel_price = FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.50'),
            scraped_at=timezone.now()
        )
        
        assert fuel_price.country_name == 'Poland'

    def test_price_must_be_positive(self, db, country_poland):
        """Should raise ValidationError for non-positive price."""
        fuel_price = FuelPrice(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('0'),
            scraped_at=timezone.now()
        )
        
        with pytest.raises(ValidationError) as exc_info:
            fuel_price.full_clean()
        
        assert 'price_per_liter' in exc_info.value.error_dict
        assert 'greater than zero' in str(exc_info.value.error_dict['price_per_liter'])

    def test_negative_price_not_allowed(self, db, country_poland):
        """Should raise ValidationError for negative price."""
        fuel_price = FuelPrice(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('-5.50'),
            scraped_at=timezone.now()
        )
        
        with pytest.raises(ValidationError) as exc_info:
            fuel_price.full_clean()
        
        assert 'price_per_liter' in exc_info.value.error_dict

    def test_country_is_required(self, db):
        """Should raise ValidationError when country is missing."""
        fuel_price = FuelPrice(
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.50'),
            scraped_at=timezone.now()
        )
        
        with pytest.raises(ValidationError) as exc_info:
            fuel_price.full_clean()
        
        assert 'country' in exc_info.value.error_dict

    def test_fuel_type_is_required(self, db, country_poland):
        """Should raise ValidationError when fuel_type is missing."""
        fuel_price = FuelPrice(
            country=country_poland,
            price_per_liter=Decimal('6.50'),
            scraped_at=timezone.now()
        )
        
        with pytest.raises(ValidationError) as exc_info:
            fuel_price.full_clean()
        
        assert 'fuel_type' in exc_info.value.error_dict

    def test_price_per_liter_is_required(self, db, country_poland):
        """Should raise ValidationError when price_per_liter is missing."""
        fuel_price = FuelPrice(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            scraped_at=timezone.now()
        )
        
        with pytest.raises(ValidationError) as exc_info:
            fuel_price.full_clean()
        
        assert 'price_per_liter' in exc_info.value.error_dict

    def test_scraped_at_is_required(self, db, country_poland):
        """Should raise ValidationError when scraped_at is missing."""
        fuel_price = FuelPrice(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.50')
        )
        
        with pytest.raises(ValidationError) as exc_info:
            fuel_price.full_clean()
        
        assert 'scraped_at' in exc_info.value.error_dict

    def test_unique_constraint_per_day(self, db, country_poland):
        """Should enforce unique constraint on (country, fuel_type, date)."""
        from datetime import datetime
        
        fixed_datetime = timezone.make_aware(datetime(2024, 1, 15, 10, 0, 0))
        same_day_later = timezone.make_aware(datetime(2024, 1, 15, 14, 0, 0))
        
        FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.50'),
            scraped_at=fixed_datetime
        )
        
        with pytest.raises(ValidationError) as exc_info:
            FuelPrice.objects.create(
                country=country_poland,
                fuel_type=FuelType.GASOLINE,
                price_per_liter=Decimal('7.00'),
                scraped_at=same_day_later
            )
        
        assert 'Only one price per country, fuel type, and day is allowed' in str(exc_info.value)
    
    def test_allows_prices_on_different_days(self, db, country_poland):
        """Should allow multiple prices for same country and fuel type on different days."""
        from datetime import datetime
        
        day1 = timezone.make_aware(datetime(2024, 1, 15, 10, 0, 0))
        day2 = timezone.make_aware(datetime(2024, 1, 16, 10, 0, 0))
        
        FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.50'),
            scraped_at=day1
        )
        
        FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('7.00'),
            scraped_at=day2
        )
        
        assert FuelPrice.objects.filter(
            country=country_poland,
            fuel_type=FuelType.GASOLINE
        ).count() == 2

    def test_different_fuel_types_for_same_country(self, db, country_poland):
        """Should allow different fuel types for the same country."""
        gasoline = FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.50'),
            scraped_at=timezone.now()
        )
        
        diesel = FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.DIESEL,
            price_per_liter=Decimal('6.80'),
            scraped_at=timezone.now()
        )
        
        assert gasoline.country == diesel.country
        assert gasoline.fuel_type != diesel.fuel_type

    def test_same_fuel_type_for_different_countries(self, db, country_poland, country_germany):
        """Should allow same fuel type for different countries."""
        pl_gasoline = FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.50'),
            scraped_at=timezone.now()
        )
        
        de_gasoline = FuelPrice.objects.create(
            country=country_germany,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('7.20'),
            scraped_at=timezone.now()
        )
        
        assert pl_gasoline.fuel_type == de_gasoline.fuel_type
        assert pl_gasoline.country != de_gasoline.country

    def test_ordering_by_most_recent_first(self, db, country_poland, country_germany):
        """Should order by scraped_at descending, then country name, then fuel type."""
        from datetime import datetime
        
        day1 = timezone.make_aware(datetime(2024, 1, 15, 10, 0, 0))
        day2 = timezone.make_aware(datetime(2024, 1, 16, 10, 0, 0))
        day3 = timezone.make_aware(datetime(2024, 1, 17, 10, 0, 0))
        
        FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.50'),
            scraped_at=day1
        )
        
        FuelPrice.objects.create(
            country=country_germany,
            fuel_type=FuelType.DIESEL,
            price_per_liter=Decimal('7.00'),
            scraped_at=day2
        )
        
        FuelPrice.objects.create(
            country=country_germany,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('7.20'),
            scraped_at=day3
        )
        
        prices = list(FuelPrice.objects.all())
        
        assert prices[0].country.name == 'Germany'
        assert prices[0].fuel_type == FuelType.GASOLINE
        assert prices[0].scraped_at == day3
        
        assert prices[1].country.name == 'Germany'
        assert prices[1].fuel_type == FuelType.DIESEL
        assert prices[1].scraped_at == day2
        
        assert prices[2].country.name == 'Poland'
        assert prices[2].fuel_type == FuelType.GASOLINE
        assert prices[2].scraped_at == day1

    def test_timestamps_auto_populated(self, db, country_poland):
        """Should auto-populate created_at and updated_at."""
        before = timezone.now()
        fuel_price = FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.50'),
            scraped_at=timezone.now()
        )
        after = timezone.now()
        
        assert fuel_price.created_at is not None
        assert fuel_price.updated_at is not None
        assert before <= fuel_price.created_at <= after
        assert before <= fuel_price.updated_at <= after

    def test_manager_select_related_optimization(self, db, country_poland):
        """Should use select_related for country in manager."""
        FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.50'),
            scraped_at=timezone.now()
        )
        
        # Using the manager should automatically select_related country
        with self.assertNumQueries(1):
            fuel_price = FuelPrice.objects.first()
            # Accessing country shouldn't trigger another query
            _ = fuel_price.country.name

    def test_fuel_type_choices(self, db, country_poland):
        """Should only allow valid fuel type choices."""
        # Valid choices
        gasoline = FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.50'),
            scraped_at=timezone.now()
        )
        assert gasoline.fuel_type == FuelType.GASOLINE
        
        diesel = FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.DIESEL,
            price_per_liter=Decimal('6.80'),
            scraped_at=timezone.now()
        )
        assert diesel.fuel_type == FuelType.DIESEL

    def test_fuel_price_fixtures(self, fuel_price_pl_gasoline, fuel_price_de_gasoline, fuel_price_pl_diesel):
        """Should work with fuel price fixtures."""
        assert fuel_price_pl_gasoline.country.code == 'PL'
        assert fuel_price_pl_gasoline.fuel_type == FuelType.GASOLINE
        assert fuel_price_pl_gasoline.price_per_liter == Decimal('6.50')
        
        assert fuel_price_de_gasoline.country.code == 'DE'
        assert fuel_price_de_gasoline.fuel_type == FuelType.GASOLINE
        assert fuel_price_de_gasoline.price_per_liter == Decimal('7.20')
        
        assert fuel_price_pl_diesel.country.code == 'PL'
        assert fuel_price_pl_diesel.fuel_type == FuelType.DIESEL
        assert fuel_price_pl_diesel.price_per_liter == Decimal('6.80')

    def test_get_fuel_type_display(self, db, country_poland):
        """Should return human-readable fuel type display."""
        gasoline = FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.50'),
            scraped_at=timezone.now()
        )
        
        assert gasoline.get_fuel_type_display() == 'Gasoline'
        
        diesel = FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.DIESEL,
            price_per_liter=Decimal('6.80'),
            scraped_at=timezone.now()
        )
        
        assert diesel.get_fuel_type_display() == 'Diesel'

    def test_price_decimal_precision(self, db, country_poland):
        """Should store price with 3 decimal places precision."""
        fuel_price = FuelPrice.objects.create(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('6.123'),
            scraped_at=timezone.now()
        )
        
        assert fuel_price.price_per_liter == Decimal('6.123')

    def test_validated_model_calls_full_clean_on_save(self, db, country_poland):
        """Should call full_clean() on save (ValidatedModel behavior)."""
        fuel_price = FuelPrice(
            country=country_poland,
            fuel_type=FuelType.GASOLINE,
            price_per_liter=Decimal('0'),  # Invalid - not positive
            scraped_at=timezone.now()
        )
        
        # Should raise validation error on save due to ValidatedModel
        with pytest.raises(ValidationError):
            fuel_price.save()

    def assertNumQueries(self, num):
        """Helper to assert number of queries (pytest compatible)."""
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        
        class QueryAssertion:
            def __init__(self, num_queries):
                self.num_queries = num_queries
                self.context = None
            
            def __enter__(self):
                self.context = CaptureQueriesContext(connection)
                self.context.__enter__()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.context.__exit__(exc_type, exc_val, exc_tb)
                if exc_type is None:
                    executed = len(self.context.captured_queries)
                    assert executed == self.num_queries, \
                        f"Expected {self.num_queries} queries, got {executed}"
        
        return QueryAssertion(num)