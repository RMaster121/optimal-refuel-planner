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
    """Canonical list of supported countries to prevent mismatched codes and names."""

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
        """Normalize code before field validation."""
        if self.code:
            self.code = self.code.strip().upper()
        super().clean_fields(exclude=exclude)

    def clean(self) -> None:
        """Validate country code and name."""
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
    def get_queryset(self):
        return super().get_queryset().select_related('country')


class FuelPrice(ValidatedModel, TimestampedModel):
    """Historical fuel price records per country and fuel type."""

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
        return self.country.code

    @property
    def country_name(self) -> str:
        return self.country.name

    def clean(self) -> None:
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