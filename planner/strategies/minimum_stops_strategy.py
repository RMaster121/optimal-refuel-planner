"""Greedy minimum stops refuel planning strategy."""

from decimal import Decimal

from planner.exceptions import PlanningError
from planner.strategies.base_strategy import BaseRefuelStrategy, RefuelStopData


class MinimumStopsStrategy(BaseRefuelStrategy):
    """
    Greedy algorithm for minimum refuel stops.
    
    Strategy:
    - Start with full tank
    - For each waypoint, check if current_fuel < next_segment + reservoir
    - If true: refuel now (fill to 100%)
    """

    def __init__(self, car, reservoir_km: int):
        super().__init__(car, reservoir_km)
        
        # Validate reservoir
        if self.reservoir_km >= self.max_range_km:
            raise PlanningError(
                f"Reservoir ({reservoir_km} km) must be less than max range "
                f"({self.max_range_km} km)"
            )
        
        if self.reservoir_km < 0:
            raise PlanningError("Reservoir cannot be negative")

    def calculate_plan(self, waypoints: list[dict]) -> list[RefuelStopData]:
        """Greedy algorithm: refuel when current_fuel < next_segment + reservoir."""
        if not waypoints or len(waypoints) < 2:
            raise PlanningError("Route must have at least 2 waypoints (start and end)")
        
        # Validate all segments are feasible
        self._validate_segments(waypoints)
        
        stops: list[RefuelStopData] = []
        current_fuel_km = self.max_range_km  # Start with full tank
        
        for i in range(len(waypoints) - 1):
            current_waypoint = waypoints[i]
            next_waypoint = waypoints[i + 1]
            
            # Calculate segment distance
            current_distance = Decimal(str(current_waypoint['distance_from_start_km']))
            next_distance = Decimal(str(next_waypoint['distance_from_start_km']))
            segment_distance = next_distance - current_distance
            
            # Check if we need to refuel at current waypoint
            # Condition: current_fuel < next_segment + reservoir
            if current_fuel_km < segment_distance + self.reservoir_km:
                # Calculate how much fuel to add (fill to 100%)
                fuel_needed_km = self.max_range_km - current_fuel_km
                fuel_needed_liters = (fuel_needed_km / Decimal('100')) * self.car.avg_consumption
                
                # Create refuel stop at current waypoint
                stop: RefuelStopData = {
                    'waypoint_index': i,
                    'distance_from_start_km': current_distance,
                    'country_code': current_waypoint['country_code'],
                    'fuel_to_add_liters': fuel_needed_liters,
                    'latitude': Decimal(str(current_waypoint['lat'])) if current_waypoint.get('lat') else None,
                    'longitude': Decimal(str(current_waypoint['lng'])) if current_waypoint.get('lng') else None,
                }
                stops.append(stop)
                
                # After refueling, tank is full
                current_fuel_km = self.max_range_km
            
            # Travel to next waypoint
            current_fuel_km -= segment_distance
        
        return stops

    def _validate_segments(self, waypoints: list[dict]) -> None:
        """Validate that all route segments are feasible."""
        for i in range(len(waypoints) - 1):
            current_distance = Decimal(str(waypoints[i]['distance_from_start_km']))
            next_distance = Decimal(str(waypoints[i + 1]['distance_from_start_km']))
            segment_distance = next_distance - current_distance
            
            if segment_distance > self.usable_range_km:
                raise PlanningError(
                    f"Segment {i} ({segment_distance} km) exceeds usable range "
                    f"({self.usable_range_km} km). Route is infeasible."
                )