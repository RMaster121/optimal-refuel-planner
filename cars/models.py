from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from refuel_planner.choices import FuelType
from refuel_planner.models import TimestampedModel, ValidatedModel
from refuel_planner.validators import (
    validate_positive_decimal,
    validate_and_sanitize_name,
)


class Car(ValidatedModel, TimestampedModel):
    """Vehicle definition tied to a user profile."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cars",
        help_text="Owner of the vehicle.",
    )
    name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Human-readable vehicle name, unique per user.",
    )
    fuel_type = models.CharField(
        max_length=10,
        choices=FuelType.choices,
        db_index=True,
        help_text="Fuel variant consumed by this vehicle.",
    )
    avg_consumption = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Average fuel consumption in L/100km.",
    )
    tank_capacity = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Total tank capacity in liters.",
    )

    class Meta:
        ordering = ("name",)
        unique_together = (("user", "name"),)
        indexes = [
            models.Index(fields=["user", "fuel_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_fuel_type_display()})"

    @property
    def max_range_km(self) -> Decimal:
        """Return theoretical driving range (km) for a full tank."""
        try:
            if self.avg_consumption and self.tank_capacity:
                return (self.tank_capacity / self.avg_consumption) * Decimal("100")
        except (InvalidOperation, ZeroDivisionError):
            return Decimal("0")
        return Decimal("0")

    def clean(self) -> None:
        """Model-level validation for numeric inputs and text sanitization."""
        super().clean()
        errors: dict[str, list[str]] = {}

        if self.name:
            sanitized_name, error = validate_and_sanitize_name(
                self.name,
                field_name="Vehicle name",
                max_length=100
            )
            if error:
                errors.setdefault("name", []).append(error)
            else:
                self.name = sanitized_name

        error = validate_positive_decimal(
            self.avg_consumption,
            "Average consumption"
        )
        if error:
            errors.setdefault("avg_consumption", []).append(error)

        error = validate_positive_decimal(
            self.tank_capacity,
            "Tank capacity"
        )
        if error:
            errors.setdefault("tank_capacity", []).append(error)

        if errors:
            raise ValidationError(errors)