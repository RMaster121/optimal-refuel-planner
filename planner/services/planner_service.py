"""Service for creating and managing refuel plans."""

from decimal import Decimal
from typing import Type

from django.db import transaction
from django.utils import timezone

from cars.models import Car
from fuel_prices.models import Country, FuelPrice
from planner.exceptions import PlanningError
from planner.models import RefuelPlan, RefuelStop
from planner.strategies.base_strategy import BaseRefuelStrategy
from planner.strategies.minimum_stops_strategy import MinimumStopsStrategy
from refuel_planner.choices import OptimizationStrategy
from routes.models import Route


class PlannerService:
    """Orchestrates the refuel planning process."""

    # Strategy mapping
    STRATEGY_MAP: dict[str, Type[BaseRefuelStrategy]] = {
        OptimizationStrategy.MIN_STOPS: MinimumStopsStrategy,
    }

    def __init__(self, route: Route, car: Car, reservoir_km: int, strategy: str):
        """
        Initialize planner service.
        
        Args:
            route: Route to plan for
            car: Car to use
            reservoir_km: Safety reserve distance
            strategy: Optimization strategy choice
        """
        self.route = route
        self.car = car
        self.reservoir_km = reservoir_km
        self.strategy_choice = strategy

    @transaction.atomic
    def create_plan(self) -> RefuelPlan:
        """
        Create a complete refuel plan.
        
        Returns:
            Created RefuelPlan instance with all stops
        
        Raises:
            PlanningError: If planning fails for any reason
        """
        fuel_prices = self._get_fuel_prices()
        
        strategy = self._get_strategy_instance()
        
        stops_data = strategy.calculate_plan(self.route.waypoints)
        
        total_fuel_liters, total_cost = self._calculate_totals(stops_data, fuel_prices)
        
        plan = RefuelPlan.objects.create(
            route=self.route,
            car=self.car,
            reservoir_km=self.reservoir_km,
            optimization_strategy=self.strategy_choice,
            total_cost=total_cost,
            total_fuel_needed=total_fuel_liters,
            number_of_stops=len(stops_data),
        )
        
        self._create_stops(plan, stops_data, fuel_prices)
        
        return plan

    def _get_fuel_prices(self) -> dict[str, FuelPrice]:
        """
        Fetch latest fuel prices for all route countries.
        
        Returns:
            Dict mapping country_code -> FuelPrice
        
        Raises:
            PlanningError: If any country is missing price data
        """
        if not self.route.countries:
            raise PlanningError("Route has no countries data")
        
        fuel_prices = {}
        missing_countries = []
        
        for country_code in self.route.countries:
            try:
                country = Country.objects.get(code=country_code.upper())
                
                price = FuelPrice.objects.filter(
                    country=country,
                    fuel_type=self.car.fuel_type
                ).order_by('-scraped_at').first()
                
                if price:
                    fuel_prices[country_code.upper()] = price
                else:
                    missing_countries.append(country_code.upper())
                    
            except Country.DoesNotExist:
                missing_countries.append(country_code.upper())
        
        if missing_countries:
            raise PlanningError(
                f"Missing fuel price data for countries: {', '.join(missing_countries)}"
            )
        
        return fuel_prices

    def _get_strategy_instance(self) -> BaseRefuelStrategy:
        """
        Get strategy instance based on choice.
        
        Returns:
            Strategy instance
        
        Raises:
            PlanningError: If strategy not implemented
        """
        strategy_class = self.STRATEGY_MAP.get(self.strategy_choice)
        
        if not strategy_class:
            raise PlanningError(
                f"Strategy '{self.strategy_choice}' is not yet implemented"
            )
        
        return strategy_class(self.car, self.reservoir_km)

    def _calculate_totals(
        self,
        stops_data: list[dict],
        fuel_prices: dict[str, FuelPrice]
    ) -> tuple[Decimal, Decimal]:
        """
        Calculate total fuel needed and total cost.
        
        Args:
            stops_data: List of stop data from strategy
            fuel_prices: Dict mapping country_code -> FuelPrice
        
        Returns:
            Tuple of (total_fuel_liters, total_cost)
        """
        # Calculate total fuel needed for entire route
        total_distance = self.route.total_distance_km
        total_fuel_liters = ((total_distance / Decimal('100')) * self.car.avg_consumption).quantize(Decimal('0.01'))
        
        # Calculate total cost from stops
        total_cost = Decimal('0')
        for stop in stops_data:
            fuel_liters = stop['fuel_to_add_liters']
            country_code = stop['country_code'].upper()
            price_per_liter = fuel_prices[country_code].price_per_liter
            
            total_cost += fuel_liters * price_per_liter
        
        total_cost = total_cost.quantize(Decimal('0.01'))
        
        return total_fuel_liters, total_cost

    def _create_stops(
        self,
        plan: RefuelPlan,
        stops_data: list[dict],
        fuel_prices: dict[str, FuelPrice]
    ) -> None:
        """
        Create RefuelStop records for the plan.
        
        Args:
            plan: RefuelPlan instance
            stops_data: List of stop data from strategy
            fuel_prices: Dict mapping country_code -> FuelPrice
        """
        stops_to_create = []
        
        for i, stop_data in enumerate(stops_data, start=1):
            country_code = stop_data['country_code'].upper()
            fuel_price = fuel_prices[country_code]
            fuel_liters = stop_data['fuel_to_add_liters']
            cost = fuel_liters * fuel_price.price_per_liter
            
            stop = RefuelStop(
                plan=plan,
                stop_number=i,
                country=fuel_price.country,
                fuel_price=fuel_price,
                distance_from_start_km=stop_data['distance_from_start_km'],
                fuel_to_add_liters=fuel_liters,
                total_cost=cost,
                latitude=stop_data.get('latitude'),
                longitude=stop_data.get('longitude'),
            )
            stops_to_create.append(stop)
        
        RefuelStop.objects.bulk_create(stops_to_create)