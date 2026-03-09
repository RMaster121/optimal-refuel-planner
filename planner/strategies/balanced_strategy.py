from decimal import Decimal
from planner.strategies.cheapest_strategy import CheapestStrategy

class BalancedStrategy(CheapestStrategy):
    """
    Balanced (cheapest, but with fine on every stop)
    """
    STOP_PENALTY_EUR = Decimal('5.00')

    def _calculate_optimal_refuel(
            self,
            current_fuel_km: Decimal,
            distance_to_cheaper: Decimal,
            current_price: Decimal,
            target_price: Decimal | None
    ) -> Decimal:
        if target_price is not None:
            price_diff = current_price - target_price
            max_savings_eur = price_diff * self.car.tank_capacity

            if max_savings_eur > self.STOP_PENALTY_EUR:
                fuel_needed_km = (distance_to_cheaper + self.reservoir_km) - current_fuel_km
                return min(fuel_needed_km, self.max_range_km - current_fuel_km)

        return self.max_range_km - current_fuel_km
