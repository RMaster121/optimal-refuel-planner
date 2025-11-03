from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from refuel_planner.models import ValidatedModel
from refuel_planner.validators import (
    validate_positive_decimal,
    validate_and_sanitize_location,
)


class Route(ValidatedModel):
    """Route data from GPX file uploads."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="routes",
        help_text="User who created this route.",
    )
    origin = models.CharField(
        max_length=200,
        help_text="Human-readable starting location of the route.",
    )
    destination = models.CharField(
        max_length=200,
        help_text="Human-readable ending location of the route.",
    )
    total_distance_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        help_text="Total distance of the route in kilometers.",
    )
    waypoints = models.JSONField(
        default=list,
        blank=True,
        help_text="List of waypoint dictionaries with lat, lng, country_code, and distance_from_start.",
    )
    countries = models.JSONField(
        default=list,
        blank=True,
        help_text="List of ISO country codes encountered along the route.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the route was created.",
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.origin} → {self.destination} ({self.total_distance_km} km)"

    def clean(self) -> None:
        super().clean()
        errors: dict[str, list[str]] = {}

        if self.origin:
            sanitized_origin, error = validate_and_sanitize_location(
                self.origin,
                field_name="Origin",
                max_length=200
            )
            if error:
                errors.setdefault("origin", []).append(error)
            else:
                self.origin = sanitized_origin

        if self.destination:
            sanitized_destination, error = validate_and_sanitize_location(
                self.destination,
                field_name="Destination",
                max_length=200
            )
            if error:
                errors.setdefault("destination", []).append(error)
            else:
                self.destination = sanitized_destination

        error = validate_positive_decimal(
            self.total_distance_km,
            "Total distance"
        )
        if error:
            errors.setdefault("total_distance_km", []).append(error)

        if self.waypoints is not None and not isinstance(self.waypoints, list):
            errors.setdefault("waypoints", []).append("Waypoints must be a list.")

        if self.countries is not None and not isinstance(self.countries, list):
            errors.setdefault("countries", []).append("Countries must be a list.")

        if errors:
            raise ValidationError(errors)