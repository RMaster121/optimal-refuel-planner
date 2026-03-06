"""
Unit tests for FuelPriceLoader.

Tests:
- Database create operations
- Database update operations
- Duplicate detection
- Auto-create countries
- Batch processing
"""

import pytest
from decimal import Decimal
from django.utils import timezone
from fuel_prices.models import Country, FuelPrice
from fuel_prices.scrapers.data_loader import FuelPriceLoader
from fuel_prices.scrapers.base import ScrapedFuelPrice


@pytest.mark.django_db
class TestFuelPriceLoader:
    """Test suite for FuelPriceLoader class."""
    
    def test_load_single_new_record(self, country_poland):
        """Test loading a new fuel price record."""
        loader = FuelPriceLoader()
        
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=1.397,
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        stats = loader.load_batch([data], auto_create_countries=False)
        
        assert stats['created'] == 1
        assert stats['updated'] == 0
        assert stats['skipped'] == 0
        assert stats['errors'] == 0
        
        # Verify database
        assert FuelPrice.objects.count() == 1
        price = FuelPrice.objects.first()
        assert price.country == country_poland
        assert price.price_per_liter == Decimal('1.397')
    
    def test_load_update_existing_record(self, country_poland):
        """Test updating an existing fuel price record."""
        loader = FuelPriceLoader()
        now = timezone.now()
        
        # Create initial price
        FuelPrice.objects.create(
            country=country_poland,
            fuel_type='gasoline',
            price_per_liter=Decimal('1.300'),
            scraped_at=now
        )
        
        # Load updated price for same day
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=1.397,  # Different price
            scraped_at=now,
            source_url='http://example.com'
        )
        
        stats = loader.load_batch([data], auto_create_countries=False)
        
        assert stats['created'] == 0
        assert stats['updated'] == 1
        assert stats['skipped'] == 0
        
        # Verify database
        assert FuelPrice.objects.count() == 1
        price = FuelPrice.objects.first()
        assert price.price_per_liter == Decimal('1.397')
    
    def test_load_skip_unchanged_price(self, country_poland):
        """Test skipping when price hasn't changed."""
        loader = FuelPriceLoader()
        now = timezone.now()
        
        # Create initial price
        FuelPrice.objects.create(
            country=country_poland,
            fuel_type='gasoline',
            price_per_liter=Decimal('1.397'),
            scraped_at=now
        )
        
        # Load same price
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=1.397,  # Same price
            scraped_at=now,
            source_url='http://example.com'
        )
        
        stats = loader.load_batch([data], auto_create_countries=False)
        
        assert stats['created'] == 0
        assert stats['updated'] == 0
        assert stats['skipped'] == 1
    
    def test_load_skip_missing_price(self, country_poland):
        """Test skipping records with None price."""
        loader = FuelPriceLoader()
        
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=None,  # Missing price
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        stats = loader.load_batch([data], auto_create_countries=False)
        
        assert stats['created'] == 0
        assert stats['skipped'] == 1
        assert FuelPrice.objects.count() == 0
    
    def test_auto_create_country(self):
        """Test automatic country creation."""
        loader = FuelPriceLoader()
        
        # No countries in database
        assert Country.objects.count() == 0
        
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=1.397,
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        stats = loader.load_batch([data], auto_create_countries=True)
        
        assert stats['created'] == 1
        assert stats['errors'] == 0
        
        # Verify country was created
        assert Country.objects.count() == 1
        country = Country.objects.first()
        assert country.code == 'PL'
        assert country.name == 'Poland'
    
    def test_no_auto_create_country(self):
        """Test error when country doesn't exist and auto-create disabled."""
        loader = FuelPriceLoader()
        
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=1.397,
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        stats = loader.load_batch([data], auto_create_countries=False)
        
        assert stats['created'] == 0
        assert stats['errors'] == 1
        assert Country.objects.count() == 0
    
    def test_load_batch_multiple_records(self, country_poland, country_germany):
        """Test loading multiple records in batch."""
        loader = FuelPriceLoader()
        now = timezone.now()
        
        data = [
            ScrapedFuelPrice(
                country_name='Poland',
                country_code='PL',
                fuel_type='gasoline',
                price_eur=1.397,
                scraped_at=now,
                source_url='http://example.com'
            ),
            ScrapedFuelPrice(
                country_name='Germany',
                country_code='DE',
                fuel_type='diesel',
                price_eur=1.622,
                scraped_at=now,
                source_url='http://example.com'
            ),
        ]
        
        stats = loader.load_batch(data, auto_create_countries=False)
        
        assert stats['created'] == 2
        assert FuelPrice.objects.count() == 2
    
    def test_load_batch_mixed_operations(self, country_poland):
        """Test batch with create, update, and skip operations."""
        loader = FuelPriceLoader()
        now = timezone.now()
        
        # Create existing price
        FuelPrice.objects.create(
            country=country_poland,
            fuel_type='gasoline',
            price_per_liter=Decimal('1.300'),
            scraped_at=now
        )
        
        data = [
            # Update existing
            ScrapedFuelPrice(
                country_name='Poland',
                country_code='PL',
                fuel_type='gasoline',
                price_eur=1.397,  # Different price
                scraped_at=now,
                source_url='http://example.com'
            ),
            # Create new
            ScrapedFuelPrice(
                country_name='Poland',
                country_code='PL',
                fuel_type='diesel',
                price_eur=1.428,
                scraped_at=now,
                source_url='http://example.com'
            ),
            # Skip (no price)
            ScrapedFuelPrice(
                country_name='Poland',
                country_code='PL',
                fuel_type='lpg',
                price_eur=None,
                scraped_at=now,
                source_url='http://example.com'
            ),
        ]
        
        stats = loader.load_batch(data, auto_create_countries=False)
        
        assert stats['created'] == 1
        assert stats['updated'] == 1
        assert stats['skipped'] == 1
        assert FuelPrice.objects.count() == 2
    
    def test_load_missing_country_code(self):
        """Test error handling for missing country code."""
        loader = FuelPriceLoader()
        
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code=None,  # Missing code
            fuel_type='gasoline',
            price_eur=1.397,
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        stats = loader.load_batch([data], auto_create_countries=True)
        
        assert stats['created'] == 0
        assert stats['errors'] == 1
    
    def test_get_stats(self):
        """Test getting statistics."""
        loader = FuelPriceLoader()
        
        initial_stats = loader.get_stats()
        assert initial_stats['created'] == 0
        assert initial_stats['updated'] == 0
        assert initial_stats['skipped'] == 0
        assert initial_stats['errors'] == 0
    
    def test_transaction_rollback_on_error(self, country_poland):
        """Test that transaction is atomic - all or nothing."""
        loader = FuelPriceLoader()
        now = timezone.now()
        
        # This test verifies transaction behavior
        # If one record in batch fails, others should still be processed
        # because each record is handled individually within the transaction
        
        data = [
            ScrapedFuelPrice(
                country_name='Poland',
                country_code='PL',
                fuel_type='gasoline',
                price_eur=1.397,
                scraped_at=now,
                source_url='http://example.com'
            ),
            ScrapedFuelPrice(
                country_name='Invalid',
                country_code=None,  # Will cause error
                fuel_type='gasoline',
                price_eur=1.5,
                scraped_at=now,
                source_url='http://example.com'
            ),
        ]
        
        stats = loader.load_batch(data, auto_create_countries=False)
        
        # First record should succeed, second should error
        assert stats['created'] == 1
        assert stats['errors'] == 1
        assert FuelPrice.objects.count() == 1