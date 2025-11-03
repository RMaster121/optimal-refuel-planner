"""Base class for refuel planning strategies."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import TypedDict

from cars.models import Car


class RefuelStopData(TypedDict):
    """Data structure for a refuel stop."""
    waypoint_index: int
    distance_from_start_km: Decimal
    country_code: str
    fuel_to_add_liters: Decimal
    latitude: Decimal | None
    longitude: Decimal | None


class BaseRefuelStrategy(ABC):
    """
    Abstract base class for refuel planning strategies.
    
    All strategies must implement calculate_plan() method.
    """

    def __init__(self, car: Car, reservoir_km: int):
        """
        Initialize strategy with car and safety reservoir.
        
        Args:
            car: Car instance with fuel consumption and tank capacity
            reservoir_km: Safety reserve distance in kilometers
        """
        self.car = car
        self.reservoir_km = Decimal(str(reservoir_km))
        
        # Calculate derived values
        self.max_range_km = car.max_range_km
        self.usable_range_km = self.max_range_km - self.reservoir_km

    @abstractmethod
    def calculate_plan(self, waypoints: list[dict]) -> list[RefuelStopData]:
        """
        Calculate optimal refuel stops based on strategy.
        
        Args:
            waypoints: List of waypoint dicts with keys:
                - lat: float
                - lng: float
                - country_code: str
                - distance_from_start: float (cumulative km from start)
        
        Returns:
            List of RefuelStopData dictionaries
        
        Raises:
            PlanningError: If route is infeasible or invalid
        """
        pass