"""
Validation utilities for scraped fuel price data.

Validates:
- Country names and codes
- Fuel types
- Price values and ranges
- Timestamps
"""

from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from django.utils import timezone

from .base import ScrapedFuelPrice
from .exceptions import ValidationException
from refuel_planner.choices import FuelType


class FuelPriceValidator:
    """
    Validates scraped fuel price data before database insertion.
    
    This validator performs multi-stage validation to ensure data quality:
    - Country validation (name and code format)
    - Fuel type validation (against FuelType enum)
    - Price validation (range and format)
    - Timestamp validation (timezone-aware, not future, recent)
    
    Example:
        validator = FuelPriceValidator()
        is_valid, errors = validator.validate(scraped_data)
        if is_valid:
            # Proceed with database insertion
        else:
            # Log or handle validation errors
    """
    
    # Validation thresholds
    MIN_PRICE_EUR = Decimal('0.10')
    MAX_PRICE_EUR = Decimal('10.00')
    MAX_AGE_DAYS = 7
    
    # Valid fuel types from Django choices
    VALID_FUEL_TYPES = {ft.value for ft in FuelType}
    
    def __init__(self):
        """Initialize validator."""
        self.errors: List[str] = []
    
    def validate(self, data: ScrapedFuelPrice) -> Tuple[bool, List[str]]:
        """
        Validate a single scraped fuel price record.
        
        Performs comprehensive validation across all fields and returns
        both a boolean result and detailed error messages.
        
        Args:
            data: ScrapedFuelPrice object to validate
            
        Returns:
            Tuple of (is_valid, error_messages):
                - is_valid: True if all validations pass, False otherwise
                - error_messages: List of validation error descriptions
                
        Example:
            >>> validator = FuelPriceValidator()
            >>> is_valid, errors = validator.validate(data)
            >>> if not is_valid:
            ...     for error in errors:
            ...         print(f"Validation error: {error}")
        """
        self.errors = []
        
        self._validate_country(data)
        self._validate_fuel_type(data)
        self._validate_price(data)
        self._validate_timestamp(data)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors.copy()
    
    def _validate_country(self, data: ScrapedFuelPrice):
        """
        Validate country name and code.
        
        Checks:
        - Country name is not empty
        - Country code (if present) is exactly 2 characters
        - Country code (if present) contains only letters
        
        Args:
            data: ScrapedFuelPrice object
        """
        if not data.country_name or not data.country_name.strip():
            self.errors.append("Country name is empty")
        
        if data.country_code:
            if len(data.country_code) != 2:
                self.errors.append(
                    f"Invalid country code length: '{data.country_code}' "
                    f"(expected 2 characters)"
                )
            
            if not data.country_code.isalpha():
                self.errors.append(
                    f"Country code must be alphabetic: '{data.country_code}'"
                )
            
            if not data.country_code.isupper():
                self.errors.append(
                    f"Country code must be uppercase: '{data.country_code}'"
                )
    
    def _validate_fuel_type(self, data: ScrapedFuelPrice):
        """
        Validate fuel type against FuelType enum.
        
        Ensures the fuel type matches one of the supported types
        defined in the FuelType Django choices.
        
        Args:
            data: ScrapedFuelPrice object
        """
        if not data.fuel_type:
            self.errors.append("Fuel type is empty")
            return
        
        if data.fuel_type not in self.VALID_FUEL_TYPES:
            self.errors.append(
                f"Invalid fuel type: '{data.fuel_type}'. "
                f"Must be one of: {', '.join(self.VALID_FUEL_TYPES)}"
            )
    
    def _validate_price(self, data: ScrapedFuelPrice):
        """
        Validate price value and range.
        
        Checks:
        - Price can be converted to Decimal
        - Price is positive (> 0)
        - Price is within reasonable range (MIN_PRICE_EUR to MAX_PRICE_EUR)
        
        Note: None/null prices are acceptable (missing data) and not validated.
        
        Args:
            data: ScrapedFuelPrice object
        """
        # None/null is acceptable (missing data)
        if data.price_eur is None:
            return
        
        try:
            price = Decimal(str(data.price_eur))
            
            if price <= 0:
                self.errors.append(
                    f"Price must be positive: {price} EUR"
                )
            
            if price < self.MIN_PRICE_EUR or price > self.MAX_PRICE_EUR:
                self.errors.append(
                    f"Price out of reasonable range "
                    f"({self.MIN_PRICE_EUR}-{self.MAX_PRICE_EUR} EUR): {price} EUR"
                )
        
        except (ValueError, InvalidOperation) as e:
            self.errors.append(
                f"Invalid price format: '{data.price_eur}' - {e}"
            )
    
    def _validate_timestamp(self, data: ScrapedFuelPrice):
        """
        Validate scraped timestamp.
        
        Checks:
        - Timestamp is present
        - Timestamp is timezone-aware
        - Timestamp is not in the future
        - Timestamp is recent (within MAX_AGE_DAYS)
        
        Args:
            data: ScrapedFuelPrice object
        """
        if not data.scraped_at:
            self.errors.append("Scraped timestamp is missing")
            return
        
        # Must be timezone-aware
        if data.scraped_at.tzinfo is None:
            self.errors.append("Scraped timestamp must be timezone-aware")
        
        # Cannot be future
        now = timezone.now()
        if data.scraped_at > now:
            self.errors.append(
                f"Scraped timestamp is in the future: {data.scraped_at}"
            )
        
        # Should be recent
        max_age = timedelta(days=self.MAX_AGE_DAYS)
        if now - data.scraped_at > max_age:
            self.errors.append(
                f"Scraped timestamp is too old (>{self.MAX_AGE_DAYS} days): "
                f"{data.scraped_at}"
            )
    
    def validate_batch(
        self,
        data_list: List[ScrapedFuelPrice]
    ) -> Tuple[List[ScrapedFuelPrice], List[Tuple[ScrapedFuelPrice, List[str]]]]:
        """
        Validate a batch of scraped data.
        
        Processes multiple ScrapedFuelPrice objects and separates them into
        valid and invalid records with their respective error messages.
        
        Args:
            data_list: List of ScrapedFuelPrice objects to validate
            
        Returns:
            Tuple of (valid_records, invalid_records_with_errors):
                - valid_records: List of ScrapedFuelPrice objects that passed validation
                - invalid_records_with_errors: List of tuples containing
                  (ScrapedFuelPrice, error_messages) for failed validations
                  
        Example:
            >>> validator = FuelPriceValidator()
            >>> valid, invalid = validator.validate_batch(scraped_data)
            >>> print(f"Valid: {len(valid)}, Invalid: {len(invalid)}")
            >>> for data, errors in invalid:
            ...     print(f"{data.country_name}: {errors}")
        """
        valid = []
        invalid = []
        
        for data in data_list:
            is_valid, errors = self.validate(data)
            
            if is_valid:
                valid.append(data)
            else:
                invalid.append((data, errors))
        
        return valid, invalid