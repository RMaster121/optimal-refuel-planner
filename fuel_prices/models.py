"""Data models for fuel price tracking and country management.

This module provides the core models for managing fuel price data across
different countries. It includes the Country model for maintaining a canonical
list of supported countries, and the FuelPrice model for tracking historical
fuel price data with automatic validation and constraints to ensure data quality.

The models enforce:
- Valid ISO 3166-1 alpha-2 country codes
- Positive fuel prices
- One price entry per country/fuel type/day constraint
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import TruncDate

from refuel_planner.choices import FuelType
from refuel_planner.models import TimestampedModel, ValidatedModel
from refuel_planner.validators import (
    validate_positive_decimal,
    iso_country_code_validator,
)


class Country(ValidatedModel):
    """Canonical list of supported countries to prevent mismatched codes and names.
    
    This model maintains a reference list of countries with their ISO codes
    and names. It ensures consistency across the application by providing
    a single source of truth for country data, preventing mismatches between
    country codes and names in related models like FuelPrice.
    
    Country codes are automatically normalized to uppercase and validated
    against ISO 3166-1 alpha-2 standards.
    
    Attributes:
        code (str): Two-letter ISO 3166-1 alpha-2 country code (e.g., 'PL', 'DE').
            Automatically normalized to uppercase. Must be unique.
        name (str): Human-readable country name (e.g., 'Poland', 'Germany').
            Must be unique.
    
    Example:
        Creating a new country:
        
        >>> country = Country.objects.create(
        ...     code='pl',  # Will be normalized to 'PL'
        ...     name='Poland'
        ... )
        >>> str(country)
        'Poland (PL)'
        >>> country.code
        'PL'
    """

    code = models.CharField(
        max_length=2,
        unique=True,
        help_text="ISO 3166-1 alpha-2 country code (e.g. PL, DE).",
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Human-readable country name.",
    )

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.code.upper()})"

    def clean_fields(self, exclude=None):
        """Normalize country code to uppercase before field validation.
        
        This method is called automatically before individual field validation.
        It ensures the country code is stripped of whitespace and converted
        to uppercase for consistency.
        
        Args:
            exclude: Optional list of field names to exclude from validation.
        """
        if self.code:
            self.code = self.code.strip().upper()
        super().clean_fields(exclude=exclude)

    def clean(self) -> None:
        """Validate country code format and name presence.
        
        Performs model-level validation to ensure:
        - Country code follows ISO 3166-1 alpha-2 format
        - Country name is not blank
        
        Called automatically by ValidatedModel before save.
        
        Raises:
            ValidationError: If country code is invalid or name is blank,
                with error dict mapping field names to error message lists.
        
        Example:
            >>> country = Country(code='xyz', name='')
            >>> country.clean()  # Raises ValidationError with 'code' and 'name' errors
        """
        super().clean()
        errors: dict[str, list[str]] = {}

        if self.code:
            try:
                iso_country_code_validator(self.code)
            except ValidationError as e:
                errors.setdefault("code", []).extend(e.messages)

        if not (self.name or "").strip():
            errors.setdefault("name", []).append("Country name cannot be blank.")

        if errors:
            raise ValidationError(errors)


class FuelPriceManager(models.Manager):
    """Custom manager for FuelPrice model with optimized queries.
    
    This manager automatically optimizes all queries by prefetching
    the related Country data to reduce database queries when accessing
    fuel price records.
    """
    
    def get_queryset(self):
        """Return queryset with country data prefetched.
        
        Optimizes all FuelPrice queries by including related Country
        data in a single database query using select_related.
        
        Returns:
            QuerySet: Optimized queryset with country data prefetched.
        """
        return super().get_queryset().select_related('country')


class FuelPrice(ValidatedModel, TimestampedModel):
    """Historical fuel price records per country and fuel type.
    
    This model tracks fuel prices over time for different countries and
    fuel types. It enforces a unique constraint ensuring only one price
    entry per country/fuel type/day combination to prevent duplicate data.
    
    Prices are stored with high precision (3 decimal places) to accommodate
    various currency formats. The model includes automatic timestamp tracking
    via TimestampedModel and validation via ValidatedModel.
    
    The model uses a custom manager (FuelPriceManager) that automatically
    optimizes queries by prefetching related country data.
    
    Attributes:
        country (Country): Foreign key to Country model. Required.
        fuel_type (str): Type of fuel (gasoline or diesel). Indexed for performance.
        price_per_liter (Decimal): Price per liter with 3 decimal precision.
            Must be positive (>0). Typically in EUR.
        scraped_at (DateTime): Timestamp when price was scraped. Indexed.
            Auto-set to current time if not provided.
        country_code (str): Read-only property returning country's ISO code.
        country_name (str): Read-only property returning country's name.
    
    Example:
        Creating a fuel price entry:
        
        >>> from django.utils import timezone
        >>> country = Country.objects.get(code='PL')
        >>> fuel_price = FuelPrice.objects.create(
        ...     country=country,
        ...     fuel_type=FuelType.GASOLINE,
        ...     price_per_liter=Decimal('1.45'),
        ...     scraped_at=timezone.now()
        ... )
        >>> fuel_price.country_code
        'PL'
        >>> fuel_price.country_name
        'Poland'
    """

    objects = FuelPriceManager()

    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="fuel_prices",
        help_text="Country for which this price applies.",
    )
    fuel_type = models.CharField(
        max_length=10,
        choices=FuelType.choices,
        db_index=True,
        help_text="Fuel variant this price entry refers to.",
    )
    price_per_liter = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        help_text="Fuel price per liter expressed in the specified currency.",
    )
    scraped_at = models.DateTimeField(
        db_index=True,
        help_text="Timestamp when the price was scraped from external source.",
    )

    class Meta:
        ordering = ("-scraped_at", "country__name", "fuel_type")
        indexes = [
            models.Index(fields=['country', 'fuel_type', '-scraped_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                TruncDate('scraped_at'),
                'country',
                'fuel_type',
                name='unique_fuel_price_per_day',
                violation_error_message='Only one price per country, fuel type, and day is allowed.'
            )
        ]

    def __str__(self) -> str:
        return f"{self.country.code.upper()} {self.get_fuel_type_display()} - {self.price_per_liter}"

    @property
    def country_code(self) -> str:
        """Return the ISO country code from the related country.
        
        Convenience property to access the country code without
        explicitly accessing the country relation.
        
        Returns:
            str: Two-letter ISO 3166-1 alpha-2 country code.
        
        Example:
            >>> fuel_price.country_code
            'PL'
        """
        return self.country.code

    @property
    def country_name(self) -> str:
        """Return the human-readable country name from the related country.
        
        Convenience property to access the country name without
        explicitly accessing the country relation.
        
        Returns:
            str: Human-readable country name.
        
        Example:
            >>> fuel_price.country_name
            'Poland'
        """
        return self.country.name

    def clean(self) -> None:
        """Validate that price per liter is positive.
        
        Performs model-level validation to ensure the fuel price
        is greater than zero. This prevents invalid zero or negative
        price entries.
        
        Called automatically by ValidatedModel before save.
        
        Raises:
            ValidationError: If price_per_liter is not positive (≤ 0),
                with error dict mapping 'price_per_liter' to error message.
        
        Example:
            >>> fuel_price = FuelPrice(price_per_liter=Decimal('0'))
            >>> fuel_price.clean()  # Raises ValidationError
        """
        super().clean()
        errors: dict[str, list[str]] = {}

        error = validate_positive_decimal(
            self.price_per_liter,
            "Price per liter"
        )
        if error:
            errors.setdefault("price_per_liter", []).append(error)

        if errors:
            raise ValidationError(errors)