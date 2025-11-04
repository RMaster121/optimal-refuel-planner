"""Tests for the MinimumStopsStrategy algorithm."""

from decimal import Decimal

import pytest

from cars.models import Car
from planner.exceptions import PlanningError
from planner.strategies.minimum_stops_strategy import MinimumStopsStrategy


class TestMinimumStopsStrategy:
    """Test the greedy minimum stops algorithm."""

    def test_simple_route_no_refuel(self, car_gasoline):
        """
        Test 1: Short route requiring no refuel stops.
        
        Route: 200km
        Car range: 733km (usable: 633km with 100km reservoir)
        Expected: 0 stops
        """
        strategy = MinimumStopsStrategy(car_gasoline, reservoir_km=100)
        
        waypoints = [
            {'lat': 52.0, 'lng': 21.0, 'country_code': 'PL', 'distance_from_start_km': 0},
            {'lat': 52.1, 'lng': 21.5, 'country_code': 'PL', 'distance_from_start_km': 100},
            {'lat': 52.2, 'lng': 22.0, 'country_code': 'PL', 'distance_from_start_km': 200},
        ]
        
        stops = strategy.calculate_plan(waypoints)
        
        assert len(stops) == 0

    def test_long_route_multiple_refuels(self, car_gasoline):
        """
        Test 2: Long route requiring multiple refuel stops.
        
        Route: 1500km
        Car range: 733km (usable: 633km with 100km reservoir)
        Expected: 2 stops (at ~633km and ~1266km)
        """
        strategy = MinimumStopsStrategy(car_gasoline, reservoir_km=100)
        
        # Create waypoints every 100km for 1500km
        waypoints = []
        for i in range(16):  # 0 to 1500km
            waypoints.append({
                'lat': 52.0 + i * 0.1,
                'lng': 21.0 + i * 0.1,
                'country_code': 'PL',
                'distance_from_start_km': i * 100
            })
        
        stops = strategy.calculate_plan(waypoints)
        
        assert len(stops) == 2
        # First stop should be around when fuel gets low (before hitting reservoir boundary)
        assert stops[0]['distance_from_start_km'] < Decimal('700')
        # Second stop similar pattern
        assert stops[1]['distance_from_start_km'] < Decimal('1400')

    def test_multi_country_short(self, car_gasoline):
        """
        Test 3: Multi-country route not requiring refuel.
        
        Route: Warsaw → Berlin (~575km)
        Expected: 0 stops (within usable range)
        """
        strategy = MinimumStopsStrategy(car_gasoline, reservoir_km=100)
        
        waypoints = [
            {'lat': 52.23, 'lng': 21.01, 'country_code': 'PL', 'distance_from_start_km': 0},
            {'lat': 52.40, 'lng': 19.50, 'country_code': 'PL', 'distance_from_start_km': 150},
            {'lat': 52.50, 'lng': 17.00, 'country_code': 'PL', 'distance_from_start_km': 300},
            {'lat': 52.40, 'lng': 14.50, 'country_code': 'DE', 'distance_from_start_km': 450},
            {'lat': 52.52, 'lng': 13.40, 'country_code': 'DE', 'distance_from_start_km': 575},
        ]
        
        stops = strategy.calculate_plan(waypoints)
        
        assert len(stops) == 0

    def test_multi_country_long_with_price_difference(self, car_gasoline):
        """
        Test 4: Cross-border route with refuel stop.
        
        Route: 1000km crossing PL/DE border
        Expected: 1 stop at optimal location
        """
        strategy = MinimumStopsStrategy(car_gasoline, reservoir_km=100)
        
        waypoints = [
            {'lat': 52.0, 'lng': 21.0, 'country_code': 'PL', 'distance_from_start_km': 0},
            {'lat': 52.2, 'lng': 19.0, 'country_code': 'PL', 'distance_from_start_km': 200},
            {'lat': 52.4, 'lng': 17.0, 'country_code': 'PL', 'distance_from_start_km': 400},
            {'lat': 52.5, 'lng': 15.0, 'country_code': 'DE', 'distance_from_start_km': 600},
            {'lat': 52.6, 'lng': 13.0, 'country_code': 'DE', 'distance_from_start_km': 800},
            {'lat': 52.7, 'lng': 11.0, 'country_code': 'DE', 'distance_from_start_km': 1000},
        ]
        
        stops = strategy.calculate_plan(waypoints)
        
        assert len(stops) == 1
        assert stops[0]['distance_from_start_km'] < Decimal('700')

    def test_segment_exceeds_usable_range(self, car_gasoline):
        """
        Test 5: Route segment exceeds usable range - should raise error.
        
        Usable range: 633km
        Segment: 700km
        Expected: PlanningError
        """
        strategy = MinimumStopsStrategy(car_gasoline, reservoir_km=100)
        
        waypoints = [
            {'lat': 52.0, 'lng': 21.0, 'country_code': 'PL', 'distance_from_start_km': 0},
            {'lat': 55.0, 'lng': 28.0, 'country_code': 'PL', 'distance_from_start_km': 700},
        ]
        
        with pytest.raises(PlanningError, match="exceeds usable range"):
            strategy.calculate_plan(waypoints)

    def test_reservoir_exceeds_max_range(self, car_gasoline):
        """
        Test 6: Reservoir larger than max range - should raise error.
        
        Max range: 733km
        Reservoir: 800km
        Expected: PlanningError
        """
        with pytest.raises(PlanningError, match="must be less than max range"):
            MinimumStopsStrategy(car_gasoline, reservoir_km=800)

    def test_exact_reservoir_boundary(self, car_gasoline):
        """
        Test 7: Fuel exactly at reservoir boundary triggers refuel.
        
        Setup: Arrange segments so fuel = reservoir exactly
        Expected: Refuel triggered
        """
        strategy = MinimumStopsStrategy(car_gasoline, reservoir_km=100)
        
        # First segment consumes exactly to reservoir level
        # Max range: 733km, after 633km we have 100km left (= reservoir)
        waypoints = [
            {'lat': 52.0, 'lng': 21.0, 'country_code': 'PL', 'distance_from_start_km': 0},
            {'lat': 52.5, 'lng': 22.0, 'country_code': 'PL', 'distance_from_start_km': 633},
            {'lat': 53.0, 'lng': 23.0, 'country_code': 'PL', 'distance_from_start_km': 700},
        ]
        
        stops = strategy.calculate_plan(waypoints)
        
        # Should refuel at waypoint 1 because next segment (67km) + reservoir (100km) = 167km > 100km remaining
        assert len(stops) == 1

    def test_route_exact_multiple_of_range(self, car_diesel):
        """
        Test 8: Route distance exactly equals usable range.
        
        Diesel car: 60L tank, 5.5L/100km consumption
        - Max range: ~1090.91km
        - Reservoir: 100km
        - Usable range: ~990.91km
        Route: 990km (just within usable range)
        Expected: 0 stops (exactly fits within one tank)
        """
        strategy = MinimumStopsStrategy(car_diesel, reservoir_km=100)
        
        # Create route of 990km (within usable range of ~990.91km)
        waypoints = []
        for i in range(11):  # 0 to 1000km in 100km increments
            if i == 10:
                # Last waypoint at 990km instead of 1000km
                waypoints.append({
                    'lat': 52.0 + i * 0.1,
                    'lng': 21.0 + i * 0.1,
                    'country_code': 'PL',
                    'distance_from_start_km': 990
                })
            else:
                waypoints.append({
                    'lat': 52.0 + i * 0.1,
                    'lng': 21.0 + i * 0.1,
                    'country_code': 'PL',
                    'distance_from_start_km': i * 100
                })
        
        stops = strategy.calculate_plan(waypoints)
        
        assert len(stops) == 0

    def test_empty_route(self, car_gasoline):
        """
        Test 9: Empty route (no waypoints) should raise error.
        
        Expected: PlanningError
        """
        strategy = MinimumStopsStrategy(car_gasoline, reservoir_km=100)
        
        waypoints = []
        
        with pytest.raises(PlanningError, match="at least 2 waypoints"):
            strategy.calculate_plan(waypoints)

    def test_single_waypoint(self, car_gasoline):
        """
        Test 10: Single waypoint route should raise error.
        
        Expected: PlanningError
        """
        strategy = MinimumStopsStrategy(car_gasoline, reservoir_km=100)
        
        waypoints = [
            {'lat': 52.0, 'lng': 21.0, 'country_code': 'PL', 'distance_from_start_km': 0},
        ]
        
        with pytest.raises(PlanningError, match="at least 2 waypoints"):
            strategy.calculate_plan(waypoints)