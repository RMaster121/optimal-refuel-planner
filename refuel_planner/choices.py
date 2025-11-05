"""Django choice classes for the refuel planner application.

This module provides centralized choice enumerations used across multiple apps
in the OptimalRefuelPlanner project. These choices ensure consistency in
database storage and API validation for fuel types and optimization strategies.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class FuelType(models.TextChoices):
    """Enumeration of supported fuel types.
    
    Defines the fuel variants that vehicles can consume and for which
    fuel price data is collected. Used across the cars, fuel_prices,
    and planner apps to ensure consistency in fuel type references.
    
    Available Choices:
        GASOLINE: Regular unleaded gasoline fuel.
        DIESEL: Diesel fuel.
    
    Used By:
        - Car.fuel_type: Specifies vehicle fuel consumption type
        - FuelPrice.fuel_type: Identifies fuel variant for pricing data
        - RefuelPlan filtering: Strategy selection based on fuel type
    
    Example:
        >>> car = Car(fuel_type=FuelType.GASOLINE, ...)
        >>> fuel_price = FuelPrice(fuel_type=FuelType.DIESEL, ...)
        >>> if car.fuel_type == FuelType.GASOLINE:
        ...     print("Uses gasoline")
    """

    GASOLINE = "gasoline", _("Gasoline")
    DIESEL = "diesel", _("Diesel")


class OptimizationStrategy(models.TextChoices):
    """Enumeration of refuel plan optimization strategies.
    
    Defines the available algorithms for computing optimal refueling stops
    along a route. Each strategy balances different priorities like cost
    minimization versus convenience (fewer stops).
    
    Available Choices:
        CHEAPEST: Optimize for lowest total fuel cost, may result in more stops
            at cheaper stations even if slightly out of the way.
        MIN_STOPS: Minimize the number of refueling stops, prioritizing
            convenience over cost savings.
        BALANCED: Balance between cost and convenience, finding middle ground
            between total price and number of stops.
    
    Used By:
        - RefuelPlan.strategy: Records which strategy was used for a plan
        - PlannerService: Selects optimization algorithm based on strategy choice
        - API endpoints: Accepts user preference for planning strategy
    
    Implementation Status:
        - MIN_STOPS: ✅ Implemented in MinimumStopsStrategy
        - CHEAPEST: ⏳ Planned for future implementation
        - BALANCED: ⏳ Planned for future implementation
    
    Example:
        >>> service = PlannerService(
        ...     route=route,
        ...     car=car,
        ...     strategy=OptimizationStrategy.MIN_STOPS
        ... )
        >>> plan = service.create_plan()
        >>> print(f"Used strategy: {plan.strategy}")
    """

    CHEAPEST = "cheapest", _("Cheapest price")
    MIN_STOPS = "min_stops", _("Minimum stops")
    BALANCED = "balanced", _("Balanced approach")
