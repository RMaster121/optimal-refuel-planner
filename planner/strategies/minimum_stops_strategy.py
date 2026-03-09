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

    def get_fuel_needed_km(self, current_fuel_km: Decimal, *args, **kwargs) -> Decimal:
        return self.max_range_km - current_fuel_km

