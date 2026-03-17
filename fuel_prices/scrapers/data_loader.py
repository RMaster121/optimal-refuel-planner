"""
Loads scraped and validated fuel price data into the database.
"""

from decimal import Decimal
from typing import List, Dict, Optional
from django.db import transaction
from django.utils import timezone
import logging

from fuel_prices.models import Country, FuelPrice
from .base import ScrapedFuelPrice
from .exceptions import ValidationException


class FuelPriceLoader:
    """
    Loads scraped fuel price data into the database.
    
    This loader handles the conversion of validated ScrapedFuelPrice objects
    into Django model instances, with support for:
    - Automatic Country creation when missing
    - Duplicate detection (one price per country/fuel/day)
    - Update vs. create logic based on existing records
    - Transaction safety with atomic operations
    - Detailed statistics tracking
    
    Example:
        loader = FuelPriceLoader()
        stats = loader.load_batch(validated_data, auto_create_countries=True)
        print(f"Created: {stats['created']}, Updated: {stats['updated']}")
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize fuel price loader.
        
        Args:
            logger: Optional logger instance for logging operations.
                    If None, creates a logger for this module.
        """
        self.logger = logger or logging.getLogger(__name__)
        self.stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
        }
    
    @transaction.atomic
    def load_batch(
        self,
        scraped_data: List[ScrapedFuelPrice],
        auto_create_countries: bool = True
    ) -> Dict[str, int]:
        """
        Load a batch of scraped fuel prices into database.
        
        This method processes all scraped data within a single database transaction,
        ensuring atomicity. If any error occurs, the entire batch is rolled back.
        
        Args:
            scraped_data: List of validated ScrapedFuelPrice objects
            auto_create_countries: If True, automatically create Country records
                                  for unmapped countries. If False, skip records
                                  with missing countries.
            
        Returns:
            Statistics dict with counts:
                - created: Number of new FuelPrice records created
                - updated: Number of existing FuelPrice records updated
                - skipped: Number of records skipped (missing price or country)
                - errors: Number of records that failed to load
                
        Example:
            >>> loader = FuelPriceLoader()
            >>> stats = loader.load_batch(data, auto_create_countries=True)
            >>> print(f"{stats['created']} prices created")
        """
        self.stats = {k: 0 for k in self.stats}  # Reset stats
        
        for data in scraped_data:
            try:
                with transaction.atomic():
                    self._load_single(data, auto_create_countries)
            except Exception as e:
                self.logger.error(
                    f"Failed to load {data.country_name} {data.fuel_type}: {e}",
                   exc_info=True
                )
                self.stats['errors'] += 1
        
        self._log_summary()
        return self.stats.copy()
    
    def _load_single(
        self,
        data: ScrapedFuelPrice,
        auto_create_countries: bool
    ):
        """
        Load a single fuel price record.
        
        Handles:
        - Skipping records with no price data
        - Getting or creating Country records
        - Checking for existing records on the same day
        - Creating new records or updating existing ones
        
        Args:
            data: ScrapedFuelPrice object to load
            auto_create_countries: Whether to auto-create missing countries
        """
        # Skip if no price (missing data)
        if data.price_eur is None:
            self.logger.debug(
                f"Skipping {data.country_name} {data.fuel_type}: No price data"
            )
            self.stats['skipped'] += 1
            return
        
        # Get or create Country
        country = self._get_or_create_country(data, auto_create_countries)
        if not country:
            self.logger.warning(
                f"Country not found and auto-create disabled: {data.country_name}"
            )
            self.stats['errors'] += 1
            return
        
        # Check for existing record today
        today = data.scraped_at.date()
        existing = FuelPrice.objects.filter(
            country=country,
            fuel_type=data.fuel_type,
            scraped_at__date=today
        ).first()
        
        price_decimal = Decimal(str(data.price_eur))
        
        if existing:
            # Update if price changed
            if existing.price_per_liter != price_decimal:
                old_price = existing.price_per_liter
                existing.price_per_liter = price_decimal
                existing.scraped_at = data.scraped_at
                existing.save()
                
                self.logger.info(
                    f"Updated {country.code} {data.fuel_type}: "
                    f"{old_price} → {price_decimal} EUR"
                )
                self.stats['updated'] += 1
            else:
                self.logger.debug(
                    f"Skipped {country.code} {data.fuel_type}: Price unchanged"
                )
                self.stats['skipped'] += 1
        else:
            # Create new record
            FuelPrice.objects.create(
                country=country,
                fuel_type=data.fuel_type,
                price_per_liter=price_decimal,
                scraped_at=data.scraped_at
            )
            
            self.logger.info(
                f"Created {country.code} {data.fuel_type}: {price_decimal} EUR"
            )
            self.stats['created'] += 1
    
    def _get_or_create_country(
        self,
        data: ScrapedFuelPrice,
        auto_create: bool
    ) -> Optional[Country]:
        """
        Get or create Country record.
        
        Attempts to retrieve an existing Country by code. If not found
        and auto_create is True, creates a new Country record.
        
        Args:
            data: ScrapedFuelPrice object containing country info
            auto_create: Whether to create missing Country records
            
        Returns:
            Country instance if found/created, None if not found and
            auto_create is False or if country_code is missing
        """
        if not data.country_code:
            self.logger.error(
                f"Cannot create/find country without code: {data.country_name}"
            )
            return None
        
        try:
            country = Country.objects.get(code=data.country_code)
            return country
            
        except Country.DoesNotExist:
            if auto_create:
                country = Country.objects.create(
                    code=data.country_code,
                    name=data.country_name
                )
                self.logger.info(
                    f"Auto-created country: {country.name} ({country.code})"
                )
                return country
            else:
                return None
    
    def _log_summary(self):
        """
        Log summary of load operation.
        
        Provides a high-level overview of the batch load results,
        including counts of created, updated, skipped, and error records.
        """
        total = sum(self.stats.values())
        self.logger.info(
            f"Load complete: {total} total | "
            f"{self.stats['created']} created | "
            f"{self.stats['updated']} updated | "
            f"{self.stats['skipped']} skipped | "
            f"{self.stats['errors']} errors"
        )
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get current statistics.
        
        Returns:
            Dictionary with operation counts (created, updated, skipped, errors)
        """
        return self.stats.copy()