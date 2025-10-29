from django.core.exceptions import ValidationError
from django.db import models

from cars.models import Car
from fuel_prices.models import Country, FuelPrice
from refuel_planner.choices import OptimizationStrategy
from refuel_planner.models import ValidatedModel
from refuel_planner.validators import (
    validate_non_negative_decimal,
    validate_non_negative_integer,
    validate_positive_decimal,
    validate_positive_integer,
)
from routes.models import Route


class RefuelPlanManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('route', 'car')


class RefuelPlan(ValidatedModel):
    objects = RefuelPlanManager()
    """Computed optimal refueling strategy for a specific route and vehicle."""

    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="refuel_plans",
        help_text="Route for which this plan was generated.",
    )
    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name="refuel_plans",
        help_text="Vehicle configuration used in this plan.",
    )
    reservoir_km = models.IntegerField(
        default=100,
        help_text="Safety reserve distance in kilometers to maintain in tank.",
    )
    optimization_strategy = models.CharField(
        max_length=20,
        choices=OptimizationStrategy.choices,
        help_text="Optimization approach used to compute this plan.",
    )
    total_cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Total fuel cost for the entire route in EUR.",
    )
    total_fuel_needed = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        help_text="Total liters of fuel required for the route.",
    )
    number_of_stops = models.IntegerField(
        help_text="Number of refueling stops in this plan.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the plan was generated.",
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["route", "car", "optimization_strategy"]),
        ]

    def __str__(self) -> str:
        return f"Plan for {self.route.origin} → {self.route.destination} ({self.get_optimization_strategy_display()})"

    def clean(self) -> None:
        super().clean()
        errors: dict[str, list[str]] = {}

        error = validate_non_negative_integer(
            self.reservoir_km,
            "Reservoir distance"
        )
        if error:
            errors.setdefault("reservoir_km", []).append(error)

        error = validate_non_negative_decimal(
            self.total_cost,
            "Total cost"
        )
        if error:
            errors.setdefault("total_cost", []).append(error)

        error = validate_positive_decimal(
            self.total_fuel_needed,
            "Total fuel needed"
        )
        if error:
            errors.setdefault("total_fuel_needed", []).append(error)

        error = validate_non_negative_integer(
            self.number_of_stops,
            "Number of stops"
        )
        if error:
            errors.setdefault("number_of_stops", []).append(error)

        if errors:
            raise ValidationError(errors)


class RefuelStopManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'country',
            'fuel_price',
            'fuel_price__country',
            'plan',
            'plan__car',
            'plan__route'
        )


class RefuelStop(ValidatedModel):
    """Individual refueling stop within an optimization plan."""

    objects = RefuelStopManager()

    plan = models.ForeignKey(
        RefuelPlan,
        on_delete=models.CASCADE,
        related_name="stops",
        help_text="Parent refuel plan containing this stop.",
    )
    stop_number = models.IntegerField(
        help_text="Sequential stop number (1, 2, 3, etc.).",
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="refuel_stops",
        help_text="Country where this refueling occurs.",
    )
    fuel_price = models.ForeignKey(
        FuelPrice,
        on_delete=models.PROTECT,
        related_name="refuel_stops",
        help_text="Fuel price entry used for this stop.",
    )
    distance_from_start_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        help_text="Distance from route origin to this stop in kilometers.",
    )
    fuel_to_add_liters = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Liters of fuel to add at this stop.",
    )
    total_cost = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        help_text="Total cost of fuel purchased at this stop in EUR.",
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude coordinate of the stop location.",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude coordinate of the stop location.",
    )

    class Meta:
        ordering = ("stop_number",)
        unique_together = (("plan", "stop_number"),)
        indexes = [
            models.Index(fields=["plan", "country"]),
        ]

    def __str__(self) -> str:
        return f"Stop #{self.stop_number} at {self.distance_from_start_km} km ({self.country.code.upper()})"

    def clean(self) -> None:
        super().clean()
        errors: dict[str, list[str]] = {}

        error = validate_positive_integer(
            self.stop_number,
            "Stop number",
            min_value=1
        )
        if error:
            errors.setdefault("stop_number", []).append(error)

        # Validate that fuel_price matches the car's fuel type
        if self.plan_id and self.fuel_price_id:
            if self.fuel_price.fuel_type != self.plan.car.fuel_type:
                errors.setdefault("fuel_price", []).append(
                    f"Fuel price type ({self.fuel_price.get_fuel_type_display()}) "
                    f"must match car fuel type ({self.plan.car.get_fuel_type_display()})."
                )

        # Validate that fuel_price country matches the stop country
        if self.country_id and self.fuel_price_id:
            if self.fuel_price.country_id != self.country_id:
                errors.setdefault("fuel_price", []).append(
                    f"Fuel price country ({self.fuel_price.country.name}) "
                    f"must match stop country ({self.country.name})."
                )

        error = validate_non_negative_decimal(
            self.distance_from_start_km,
            "Distance"
        )
        if error:
            errors.setdefault("distance_from_start_km", []).append(error)

        error = validate_positive_decimal(
            self.fuel_to_add_liters,
            "Fuel to add"
        )
        if error:
            errors.setdefault("fuel_to_add_liters", []).append(error)

        error = validate_non_negative_decimal(
            self.total_cost,
            "Total cost"
        )
        if error:
            errors.setdefault("total_cost", []).append(error)

        if errors:
            raise ValidationError(errors)