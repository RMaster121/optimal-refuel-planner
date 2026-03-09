"""Base class for refuel planning strategies."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import TypedDict, List, Dict, Tuple

from cars.models import Car
from planner.exceptions import PlanningError


class RefuelStopData(TypedDict):
    """Data structure for a refuel stop."""
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

    def __init__(self, car: Car, reservoir_km: int, fuel_prices: dict[str, Decimal]):
        """
        Initialize strategy with car and safety reservoir.
        
        Args:
            car: Car instance with fuel consumption and tank capacity
            reservoir_km: Safety reserve distance in kilometers
        """
        self.car = car
        self.reservoir_km = Decimal(str(reservoir_km))
        self.fuel_prices = fuel_prices

        # Calculate derived values
        self.max_range_km = car.max_range_km
        self.usable_range_km = self.max_range_km - self.reservoir_km

    def calculate_plan(self, segments: list[dict], waypoints: list[dict]) -> list[RefuelStopData]:
        """
        Calculate optimal refuel stops based on strategy.
        
        Args:
            segments: List of border to border segments
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
        if not segments:
            raise PlanningError("Route has no segments")

        stops: List[RefuelStopData] = []
        current_fuel_km = self.max_range_km

        for i, segment in enumerate(segments):
            segment_remaining_km = Decimal(str(segment['distance_km']))
            country_code = segment['country_code']
            current_distance_on_route = Decimal(str(segment['start_distance_km']))

            while current_fuel_km < segment_remaining_km + self.reservoir_km:

                driveable_distance = current_fuel_km - self.reservoir_km

                if driveable_distance < 0:
                    raise PlanningError(f"Reservoir is too high or car range too low to traverse {country_code}.")

                segment_remaining_km -= driveable_distance
                current_distance_on_route += driveable_distance
                current_fuel_km -= driveable_distance

                fuel_needed_km = self.get_fuel_needed_km(current_fuel_km=current_fuel_km,
                                                         segment_remaining_km=segment_remaining_km,
                                                         country_code=country_code, current_segment_index=i,
                                                         segments=segments)

                fuel_to_add_liters = (fuel_needed_km / Decimal('100')) * self.car.avg_consumption
                lat, lng = self.find_closest_coordinates(current_distance_on_route, waypoints)

                stops.append({'distance_from_start_km': current_distance_on_route.quantize(Decimal('0.01')),
                              'country_code': country_code,
                              'fuel_to_add_liters': fuel_to_add_liters.quantize(Decimal('0.01')), 'latitude': lat,
                              'longitude': lng, })

                current_fuel_km += fuel_needed_km

            current_fuel_km -= segment_remaining_km

        return stops

    @staticmethod
    def find_closest_coordinates(target_distance_km: Decimal, waypoints: List[Dict]) -> Tuple[
        Decimal | None, Decimal | None]:
        """
        Binary search of waypoints
        """
        if not waypoints:
            return None, None

        left, right = 0, len(waypoints) - 1
        best_idx = 0
        min_diff = Decimal('Infinity')

        while left <= right:
            mid = (left + right) // 2
            mid_dist = Decimal(str(waypoints[mid]['distance_from_start_km']))

            diff = abs(mid_dist - target_distance_km)
            if diff < min_diff:
                min_diff = diff
                best_idx = mid

            if mid_dist == target_distance_km:
                break  # Perfect match
            elif mid_dist < target_distance_km:
                left = mid + 1
            else:
                right = mid - 1

        # If neighbouring point is minimally closer
        for idx in [best_idx - 1, best_idx + 1]:
            if 0 <= idx < len(waypoints):
                dist = Decimal(str(waypoints[idx]['distance_from_start_km']))
                if abs(dist - target_distance_km) < min_diff:
                    min_diff = abs(dist - target_distance_km)
                    best_idx = idx

        best_wp = waypoints[best_idx]
        return Decimal(str(best_wp['lat'])), Decimal(str(best_wp['lng']))

    @abstractmethod
    def get_fuel_needed_km(self, current_fuel_km, segment_remaining_km, country_code, current_segment_index,
                           segments) -> Decimal:
        pass
