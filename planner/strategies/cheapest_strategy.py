from decimal import Decimal
from planner.exceptions import PlanningError
from planner.strategies.base_strategy import BaseRefuelStrategy


class CheapestStrategy(BaseRefuelStrategy):
    """Cheapest strategy. Looks ahead for cheaper countries."""

    def get_fuel_needed_km(
            self,
            current_fuel_km: Decimal,
            segment_remaining_km: Decimal,
            country_code: str,
            current_segment_index: int,
            segments: list[dict]
    ) -> Decimal:

        current_price = self.fuel_prices.get(country_code)
        if not current_price:
            raise PlanningError(f"No price data for {country_code}")

        distance_to_cheaper = segment_remaining_km
        target_price = None

        for j in range(current_segment_index + 1, len(segments)):
            future_seg = segments[j]
            future_price = self.fuel_prices.get(future_seg['country_code'])

            if future_price and future_price < current_price:
                target_price = future_price
                break
            else:
                distance_to_cheaper += Decimal(str(future_seg['distance_km']))

        return self._calculate_optimal_refuel(current_fuel_km, distance_to_cheaper, current_price, target_price)

    def _calculate_optimal_refuel(
            self,
            current_fuel_km: Decimal,
            distance_to_cheaper: Decimal,
            current_price: Decimal,
            target_price: Decimal | None
    ) -> Decimal:
        if target_price is not None:
            fuel_needed_km = (distance_to_cheaper + self.reservoir_km) - current_fuel_km
            return min(fuel_needed_km, self.max_range_km - current_fuel_km)

        return self.max_range_km - current_fuel_km