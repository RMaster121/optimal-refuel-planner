from django.db import models
from django.utils.translation import gettext_lazy as _


class FuelType(models.TextChoices):
    """Shared fuel-type enumeration across the application."""

    GASOLINE = "gasoline", _("Gasoline")
    DIESEL = "diesel", _("Diesel")


class OptimizationStrategy(models.TextChoices):
    """Strategies supported by the refuel optimization engine."""

    CHEAPEST = "cheapest", _("Cheapest price")
    MIN_STOPS = "min_stops", _("Minimum stops")
    BALANCED = "balanced", _("Balanced approach")
