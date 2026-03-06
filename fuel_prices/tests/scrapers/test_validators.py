"""
Unit tests for FuelPriceValidator.

Tests:
- Country validation
- Fuel type validation
- Price validation
- Timestamp validation
- Batch validation
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from fuel_prices.scrapers.validators import FuelPriceValidator
from fuel_prices.scrapers.base import ScrapedFuelPrice


class TestFuelPriceValidator:
    """Test suite for FuelPriceValidator class."""
   
    def test_validate_valid_data(self, scraped_fuel_price_data):
        """Test validation of completely valid data."""
        validator = FuelPriceValidator()
        is_valid, errors = validator.validate(scraped_fuel_price_data)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_country_name_empty(self):
        """Test validation fails for empty country name."""
        validator = FuelPriceValidator()
        data = ScrapedFuelPrice(
            country_name='',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=1.5,
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any('Country name is empty' in e for e in errors)
    
    def test_validate_country_code_length(self):
        """Test validation fails for invalid country code length."""
        validator = FuelPriceValidator()
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='POL',  # 3 chars instead of 2
            fuel_type='gasoline',
            price_eur=1.5,
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any('Invalid country code length' in e for e in errors)
    
    def test_validate_country_code_non_alpha(self):
        """Test validation fails for non-alphabetic country code."""
        validator = FuelPriceValidator()
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='P1',  # Contains digit
            fuel_type='gasoline',
            price_eur=1.5,
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any('must be alphabetic' in e for e in errors)
    
    def test_validate_country_code_not_uppercase(self):
        """Test validation fails for lowercase country code."""
        validator = FuelPriceValidator()
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='pl',  # Should be uppercase
            fuel_type='gasoline',
            price_eur=1.5,
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any('must be uppercase' in e for e in errors)
    
    def test_validate_fuel_type_empty(self):
        """Test validation fails for empty fuel type."""
        validator = FuelPriceValidator()
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='',
            price_eur=1.5,
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any('Fuel type is empty' in e for e in errors)
    
    def test_validate_fuel_type_invalid(self):
        """Test validation fails for invalid fuel type."""
        validator = FuelPriceValidator()
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='kerosene',  # Not in FuelType choices
            price_eur=1.5,
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any('Invalid fuel type' in e for e in errors)
    
    def test_validate_price_none_is_valid(self):
        """Test that None price is valid (missing data)."""
        validator = FuelPriceValidator()
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=None,  # Missing price is OK
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        is_valid, errors = validator.validate(data)
        assert is_valid is True
    
    def test_validate_price_negative(self):
        """Test validation fails for negative price."""
        validator = FuelPriceValidator()
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=-1.5,
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any('must be positive' in e for e in errors)
    
    def test_validate_price_too_low(self):
        """Test validation fails for price below minimum."""
        validator = FuelPriceValidator()
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=0.05,  # Below MIN_PRICE_EUR (0.10)
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any('out of reasonable range' in e for e in errors)
    
    def test_validate_price_too_high(self):
        """Test validation fails for price above maximum."""
        validator = FuelPriceValidator()
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=15.0,  # Above MAX_PRICE_EUR (10.00)
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any('out of reasonable range' in e for e in errors)
    
    def test_validate_timestamp_missing(self):
        """Test validation fails for missing timestamp."""
        validator = FuelPriceValidator()
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=1.5,
            scraped_at=None,
            source_url='http://example.com'
        )
        
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any('timestamp is missing' in e for e in errors)
    
    def test_validate_timestamp_future(self):
        """Test validation fails for future timestamp."""
        validator = FuelPriceValidator()
        future_time = timezone.now() + timedelta(days=1)
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=1.5,
            scraped_at=future_time,
            source_url='http://example.com'
        )
        
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any('in the future' in e for e in errors)
    
    def test_validate_timestamp_too_old(self):
        """Test validation fails for very old timestamp."""
        validator = FuelPriceValidator()
        old_time = timezone.now() - timedelta(days=10)
        data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=1.5,
            scraped_at=old_time,
            source_url='http://example.com'
        )
        
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any('too old' in e for e in errors)
    
    def test_validate_batch_all_valid(self, scraped_fuel_price_batch):
        """Test batch validation with all valid data."""
        validator = FuelPriceValidator()
        valid, invalid = validator.validate_batch(scraped_fuel_price_batch)
        
        assert len(valid) == 3
        assert len(invalid) == 0
    
    def test_validate_batch_mixed(self):
        """Test batch validation with mix of valid and invalid data."""
        validator = FuelPriceValidator()
        
        valid_data = ScrapedFuelPrice(
            country_name='Poland',
            country_code='PL',
            fuel_type='gasoline',
            price_eur=1.5,
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        invalid_data = ScrapedFuelPrice(
            country_name='',  # Invalid: empty
            country_code='PL',
            fuel_type='gasoline',
            price_eur=1.5,
            scraped_at=timezone.now(),
            source_url='http://example.com'
        )
        
        valid, invalid = validator.validate_batch([valid_data, invalid_data])
        
        assert len(valid) == 1
        assert len(invalid) == 1
        assert invalid[0][0] == invalid_data
        assert len(invalid[0][1]) > 0  # Has error messages
    
    def test_validate_multiple_errors(self):
        """Test that multiple validation errors are collected."""
        validator = FuelPriceValidator()
        data = ScrapedFuelPrice(
            country_name='',  # Error 1
            country_code='INVALID',  # Error 2
            fuel_type='invalid_type',  # Error 3
            price_eur=-1.0,  # Error 4
            scraped_at=None,  # Error 5
            source_url='http://example.com'
        )
        
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert len(errors) >= 5  # Should have multiple errors