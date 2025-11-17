# Refuel Planning Algorithms

## Overview

The heart of the Refuel Planner is its optimization algorithms. This document explains in detail how each strategy works, the mathematical foundations, and implementation considerations.

---

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Algorithm Foundation](#algorithm-foundation)
3. [Minimum Stops Strategy](#minimum-stops-strategy)
4. [Cheapest Strategy](#cheapest-strategy)
5. [Balanced Strategy](#balanced-strategy)
6. [Edge Cases & Validation](#edge-cases--validation)
7. [Performance Optimization](#performance-optimization)
8. [Testing Scenarios](#testing-scenarios)

---

## Core Concepts

### Key Variables

| Variable | Symbol | Description | Unit |
|----------|--------|-------------|------|
| Tank Capacity | `T` | Maximum fuel tank capacity | Liters |
| Fuel Consumption | `C` | Average consumption rate | L/100km |
| Total Distance | `D` | Route total distance | Kilometers |
| Reservoir | `R` | Safety fuel reserve | Kilometers |
| Current Fuel | `F` | Fuel in tank at any point | Liters |
| Waypoint Distance | `W_i` | Distance to waypoint i | Kilometers |
| Fuel Price | `P_i` | Price per liter at location i | EUR/L |

### Derived Values

**Maximum Range (M):**
```
M = (T / C) × 100
```
Example: Tank=50L, Consumption=6L/100km → M=833.33km

**Safe Range (S):**
```
S = M - R
```
Example: MaxRange=833km, Reservoir=100km → S=733km

**Fuel Needed for Distance (F_d):**
```
F_d = (d / 100) × C
```
Example: Distance=200km, Consumption=6L/100km → F_d=12L

**Reservoir Fuel (F_r):**
```
F_r = (R / 100) × C
```
Example: Reservoir=100km, Consumption=6L/100km → F_r=6L

---

## Algorithm Foundation

All three strategies share common foundation:

### 1. Route Segmentation

The route is divided into segments by country boundaries:

```python
class RouteSegment:
    def __init__(self, waypoints, country_code):
        self.country_code = country_code
        self.start_distance = waypoints[0]['distance_from_start_km']
        self.end_distance = waypoints[-1]['distance_from_start_km']
        self.distance = self.end_distance - self.start_distance
        self.waypoints = waypoints
        
def segment_route_by_country(waypoints):
    """
    Groups consecutive waypoints by country.
    
    Input: [{country: 'PL', distance: 0}, {country: 'PL', distance: 100},
            {country: 'DE', distance: 200}, {country: 'DE', distance: 500}]
    
    Output: [
        RouteSegment(PL, 0-100km),
        RouteSegment(DE, 100-500km)
    ]
    """
    segments = []
    current_country = None
    current_waypoints = []
    
    for waypoint in waypoints:
        if waypoint['country_code'] != current_country:
            if current_waypoints:
                segments.append(RouteSegment(current_waypoints, current_country))
            current_country = waypoint['country_code']
            current_waypoints = [waypoint]
        else:
            current_waypoints.append(waypoint)
    
    if current_waypoints:
        segments.append(RouteSegment(current_waypoints, current_country))
    
    return segments
```

### 2. Fuel State Tracking

At any point in the journey, we track:

```python
class FuelState:
    def __init__(self, distance_km, fuel_liters):
        self.distance = distance_km          # Distance from start
        self.fuel = fuel_liters               # Current fuel in tank
        self.fuel_consumed = 0                # Total fuel consumed
        self.total_cost = 0                   # Total cost so far
```

### 3. Feasibility Check

Before running any algorithm, validate route is possible:

```python
def validate_route_feasibility(route, car, reservoir_km):
    """
    Check if route can be completed with given car and reservoir.
    
    Conditions:
    1. Max range must exceed reservoir (can't have reservoir >= tank range)
    2. No single country segment can exceed safe range
    3. Total distance must be theoretically possible
    """
    max_range = (car.tank_capacity / car.avg_consumption) * 100
    safe_range = max_range - reservoir_km
    reservoir_fuel = (reservoir_km / 100) * car.avg_consumption
    
    # Check 1: Reservoir sensible
    if reservoir_km >= max_range:
        raise ValueError(
            f"Reservoir ({reservoir_km}km) must be less than "
            f"maximum range ({max_range:.0f}km)"
        )
    
    # Check 2: Can physically reach between refuel points
    segments = segment_route_by_country(route.waypoints)
    for segment in segments:
        if segment.distance > safe_range:
            raise ValueError(
                f"Segment in {segment.country_code} ({segment.distance:.0f}km) "
                f"exceeds safe range ({safe_range:.0f}km)"
            )
    
    # Check 3: Minimum stops calculation
    min_stops_needed = math.ceil(route.total_distance_km / safe_range) - 1
    if min_stops_needed > len(segments):
        # This is theoretically possible, alert user
        return {
            'feasible': True,
            'warning': f'Route may require {min_stops_needed} stops'
        }
    
    return {'feasible': True}
```

---

## Minimum Stops Strategy

### Goal
Minimize the number of refueling stops, prioritizing convenience over cost.

### Algorithm

**Principle:** Drive as far as possible before refueling, always refuel to full tank.

**Pseudocode:**
```
MinimumStops(route, car, reservoir):
    state = FuelState(0, car.tank_capacity)  // Start with full tank
    stops = []
    
    for each segment in route.segments:
        fuel_needed = segment.distance × car.consumption / 100
        
        // Check if we can reach end of segment
        fuel_after = state.fuel - fuel_needed
        
        if fuel_after < reservoir_fuel:
            // Need to refuel before or in this segment
            refuel_point = find_last_safe_point(state, segment, reservoir)
            
            // Add refuel stop
            fuel_to_add = car.tank_capacity - state.fuel
            price = get_price(segment.country, car.fuel_type)
            cost = fuel_to_add × price
            
            stop = {
                distance: refuel_point.distance,
                country: segment.country,
                fuel_to_add: fuel_to_add,
                price: price,
                cost: cost
            }
            stops.append(stop)
            
            state.fuel = car.tank_capacity
        
        // Travel through segment
        state.fuel -= fuel_needed
        state.distance += segment.distance
    
    return stops
```

**Implementation:**
```python
class MinimumStopsStrategy:
    def __init__(self, route, car, reservoir_km):
        self.route = route
        self.car = car
        self.reservoir_km = reservoir_km
        self.max_range_km = (car.tank_capacity / car.avg_consumption) * 100
        self.safe_range_km = self.max_range_km - reservoir_km
        
    def calculate(self):
        """Calculate minimum stops refuel plan."""
        segments = segment_route_by_country(self.route.waypoints)
        fuel_prices = self._get_fuel_prices()
        
        stops = []
        current_fuel = self.car.tank_capacity
        current_distance = 0.0
        
        for segment in segments:
            # Calculate fuel needed for this segment
            fuel_needed = (segment.distance / 100) * self.car.avg_consumption
            
            # Check if we can reach end of segment
            fuel_after_segment = current_fuel - fuel_needed
            reservoir_fuel = (self.reservoir_km / 100) * self.car.avg_consumption
            
            if fuel_after_segment < reservoir_fuel:
                # Need to refuel
                
                # Optimal refuel point: as late as possible while maintaining reservoir
                refuel_distance = current_distance + self.safe_range_km - current_fuel / self.car.avg_consumption * 100
                
                # Ensure refuel point is within this segment
                refuel_distance = max(segment.start_distance, 
                                     min(refuel_distance, segment.end_distance))
                
                # Get price for this country
                price = fuel_prices.get(segment.country_code, {}).get(self.car.fuel_type)
                
                if not price:
                    raise ValueError(f"No fuel price data for {segment.country_code}")
                
                # Calculate fuel to add (fill to full)
                fuel_to_add = self.car.tank_capacity - current_fuel
                cost = float(fuel_to_add) * float(price)
                
                # Find approximate coordinates for refuel point
                coords = self._interpolate_coordinates(
                    segment.waypoints, 
                    refuel_distance
                )
                
                stop = {
                    'distance_from_start_km': round(refuel_distance, 2),
                    'country_code': segment.country_code,
                    'fuel_to_add_liters': round(float(fuel_to_add), 2),
                    'price_per_liter': float(price),
                    'total_cost': round(cost, 2),
                    'fuel_before': round(float(current_fuel), 2),
                    'fuel_after': float(self.car.tank_capacity),
                    'latitude': coords['latitude'],
                    'longitude': coords['longitude']
                }
                
                stops.append(stop)
                current_fuel = self.car.tank_capacity
            
            # Travel through segment
            current_fuel -= fuel_needed
            current_distance = segment.end_distance
        
        return stops
```

**Characteristics:**
- **Stops**: Typically 1-2 for routes <1000km
- **Cost**: May not be optimal if price differences are significant
- **Simplicity**: Easy to understand and execute
- **Use Case**: When time/convenience is more important than money

**Example:**

Route: Warsaw → Berlin (570km)  
Car: 50L tank, 6L/100km (max range: 833km)  
Reservoir: 100km (safe range: 733km)

Since 570km < 733km, **zero stops needed** - can complete on initial tank!

---

## Cheapest Strategy

### Goal
Minimize total fuel cost by refueling in countries with lowest prices.

### Algorithm

**Principle:** Identify cheapest countries along route and maximize fuel purchased there.

**Approach:** Dynamic programming with lookahead.

**Pseudocode:**
```
Cheapest(route, car, reservoir):
    segments = group_by_country(route)
    price_map = create_price_map(segments)
    
    // Sort countries by price (ascending)
    sorted_countries = sort_by_price(price_map)
    
    state = FuelState(0, car.tank_capacity)
    stops = []
    
    for each segment in segments:
        // Look ahead: can we reach cheaper country?
        cheaper_ahead = find_cheaper_countries_ahead(segment, sorted_countries)
        
        if cheaper_ahead and can_reach(state, cheaper_ahead, reservoir):
            // Skip refueling here, wait for cheaper country
            continue
        else:
            // Must refuel in this or previous segment
            if state.fuel - segment_fuel_needed < reservoir:
                // Refuel now
                stop = create_refuel_stop(segment, state)
                stops.append(stop)
                state.fuel = car.tank_capacity
        
        // Travel through segment
        state.fuel -= segment.fuel_needed
        state.distance += segment.distance
    
    return stops
```

**Implementation:**
```python
class CheapestStrategy:
    def __init__(self, route, car, reservoir_km):
        self.route = route
        self.car = car
        self.reservoir_km = reservoir_km
        self.max_range_km = (car.tank_capacity / car.avg_consumption) * 100
        self.safe_range_km = self.max_range_km - reservoir_km
        
    def calculate(self):
        """Calculate cheapest cost refuel plan."""
        segments = segment_route_by_country(self.route.waypoints)
        fuel_prices = self._get_fuel_prices()
        
        # Create sorted price index
        country_prices = [
            (seg.country_code, fuel_prices.get(seg.country_code, {}).get(self.car.fuel_type))
            for seg in segments
        ]
        country_prices_sorted = sorted(
            [(c, p) for c, p in country_prices if p],
            key=lambda x: x[1]
        )
        
        stops = []
        current_fuel = self.car.tank_capacity
        current_distance = 0.0
        
        i = 0
        while i < len(segments):
            segment = segments[i]
            fuel_needed = (segment.distance / 100) * self.car.avg_consumption
            fuel_after = current_fuel - fuel_needed
            reservoir_fuel = (self.reservoir_km / 100) * self.car.avg_consumption
            
            # Check if we can skip this segment and refuel in cheaper country ahead
            cheaper_ahead = self._find_cheaper_ahead(
                i, segments, country_prices_sorted, fuel_prices
            )
            
            if cheaper_ahead and self._can_reach_safely(
                current_fuel, segment, cheaper_ahead['segment'], reservoir_fuel
            ):
                # Skip this segment, will refuel later
                current_fuel -= fuel_needed
                current_distance = segment.end_distance
                i += 1
                continue
            
            # Must refuel in this segment
            if fuel_after < reservoir_fuel:
                price = fuel_prices[segment.country_code][self.car.fuel_type]
                
                # Strategy: fill to capacity to minimize stops
                fuel_to_add = self.car.tank_capacity - current_fuel
                cost = float(fuel_to_add) * float(price)
                
                coords = self._get_segment_midpoint(segment)
                
                stop = {
                    'distance_from_start_km': round(current_distance + segment.distance / 2, 2),
                    'country_code': segment.country_code,
                    'fuel_to_add_liters': round(float(fuel_to_add), 2),
                    'price_per_liter': float(price),
                    'total_cost': round(cost, 2),
                    'fuel_before': round(float(current_fuel), 2),
                    'fuel_after': float(self.car.tank_capacity),
                    'latitude': coords['latitude'],
                    'longitude': coords['longitude']
                }
                
                stops.append(stop)
                current_fuel = self.car.tank_capacity
            
            current_fuel -= fuel_needed
            current_distance = segment.end_distance
            i += 1
        
        return stops
    
    def _find_cheaper_ahead(self, current_idx, segments, sorted_prices, price_map):
        """
        Look ahead to find cheaper refueling options.
        
        Returns segment info if cheaper country is reachable, None otherwise.
        """
        current_price = price_map.get(
            segments[current_idx].country_code, {}
        ).get(self.car.fuel_type)
        
        if not current_price:
            return None
        
        # Look at remaining segments
        for i in range(current_idx + 1, len(segments)):
            future_segment = segments[i]
            future_price = price_map.get(
                future_segment.country_code, {}
            ).get(self.car.fuel_type)
            
            if future_price and future_price < current_price * 0.95:  # 5% threshold
                return {
                    'segment': future_segment,
                    'price': future_price,
                    'index': i
                }
        
        return None
    
    def _can_reach_safely(self, current_fuel, from_segment, to_segment, reservoir_fuel):
        """Check if we can reach target segment with fuel remaining > reservoir."""
        distance_between = to_segment.start_distance - from_segment.end_distance
        total_distance = from_segment.distance + distance_between
        
        fuel_needed = (total_distance / 100) * self.car.avg_consumption
        fuel_remaining = current_fuel - fuel_needed
        
        return fuel_remaining >= reservoir_fuel
```

**Characteristics:**
- **Stops**: May have more stops than minimum if crossing through cheaper countries
- **Cost**: Optimal or near-optimal cost
- **Complexity**: More complex logic with lookahead
- **Use Case**: When fuel savings are priority

**Example:**

Route: Warsaw (PL) → Berlin (DE) → Amsterdam (NL)  
Prices: PL=€1.30, DE=€1.60, NL=€1.70  
Tank: 60L, Consumption: 7L/100km

Strategy fills tank in Poland, potentially stops again in Poland if route loops back, avoiding expensive Germany and Netherlands.

---

## Balanced Strategy

### Goal
Optimal trade-off between cost and number of stops.

### Algorithm

**Principle:** Use weighted scoring function combining both factors.

**Scoring Function:**
```
Score = α × normalized_cost + β × normalized_stops
where α + β = 1 (typically α=0.6, β=0.4)
```

**Normalization:**
```
normalized_cost = (current_cost - min_possible_cost) / (max_possible_cost - min_possible_cost)
normalized_stops = (current_stops - min_stops) / (max_stops - min_stops)
```

**Implementation:**
```python
class BalancedStrategy:
    COST_WEIGHT = 0.6      # Weight for cost optimization
    STOPS_WEIGHT = 0.4     # Weight for stop minimization
    
    def __init__(self, route, car, reservoir_km):
        self.route = route
        self.car = car
        self.reservoir_km = reservoir_km
        self.max_range_km = (car.tank_capacity / car.avg_consumption) * 100
        self.safe_range_km = self.max_range_km - reservoir_km
        
    def calculate(self):
        """Calculate balanced refuel plan using dynamic programming."""
        segments = segment_route_by_country(self.route.waypoints)
        fuel_prices = self._get_fuel_prices()
        
        # First, calculate bounds for normalization
        min_stops_plan = MinimumStopsStrategy(
            self.route, self.car, self.reservoir_km
        ).calculate()
        
        cheapest_plan = CheapestStrategy(
            self.route, self.car, self.reservoir_km
        ).calculate()
        
        min_stops = len(min_stops_plan)
        max_stops = len(cheapest_plan)
        min_cost = sum(s['total_cost'] for s in cheapest_plan)
        max_cost = sum(s['total_cost'] for s in min_stops_plan)
        
        # Dynamic programming approach
        best_plan = self._dp_optimize(
            segments, fuel_prices, min_stops, max_stops, min_cost, max_cost
        )
        
        return best_plan
    
    def _dp_optimize(self, segments, prices, min_stops, max_stops, min_cost, max_cost):
        """
        Use dynamic programming to find optimal balanced solution.
        
        State: (segment_idx, fuel_level)
        Value: (total_cost, num_stops, score)
        """
        # State space
        n = len(segments)
        fuel_levels = range(0, int(self.car.tank_capacity) + 1, 5)  # Discretize fuel
        
        # DP table: dp[segment][fuel] = (cost, stops, path)
        dp = {}
        
        # Initialize
        dp[(0, int(self.car.tank_capacity))] = (0, 0, [])
        
        for seg_idx in range(n):
            segment = segments[seg_idx]
            fuel_needed = (segment.distance / 100) * self.car.avg_consumption
            price = prices[segment.country_code][self.car.fuel_type]
            
            for fuel in fuel_levels:
                if (seg_idx, fuel) not in dp:
                    continue
                
                current_cost, current_stops, current_path = dp[(seg_idx, fuel)]
                
                # Option 1: Don't refuel in this segment
                fuel_after = fuel - fuel_needed
                if fuel_after >= 0:
                    next_state = (seg_idx + 1, int(fuel_after))
                    if next_state not in dp or self._better_score(
                        current_cost, current_stops,
                        dp[next_state][0], dp[next_state][1],
                        min_cost, max_cost, min_stops, max_stops
                    ):
                        dp[next_state] = (current_cost, current_stops, current_path)
                
                # Option 2: Refuel in this segment
                for refuel_amount in range(0, int(self.car.tank_capacity - fuel) + 1, 5):
                    if refuel_amount == 0:
                        continue
                    
                    new_fuel = fuel + refuel_amount
                    refuel_cost = refuel_amount * float(price)
                    fuel_after_refuel = new_fuel - fuel_needed
                    
                    if fuel_after_refuel >= 0:
                        next_state = (seg_idx + 1, int(fuel_after_refuel))
                        new_cost = current_cost + refuel_cost
                        new_stops = current_stops + 1
                        new_path = current_path + [{
                            'segment': seg_idx,
                            'fuel_added': refuel_amount,
                            'cost': refuel_cost
                        }]
                        
                        if next_state not in dp or self._better_score(
                            new_cost, new_stops,
                            dp[next_state][0], dp[next_state][1],
                            min_cost, max_cost, min_stops, max_stops
                        ):
                            dp[next_state] = (new_cost, new_stops, new_path)
        
        # Find best final state
        best_state = min(
            [(k, v) for k, v in dp.items() if k[0] == n],
            key=lambda x: self._calculate_score(
                x[1][0], x[1][1], min_cost, max_cost, min_stops, max_stops
            )
        )
        
        return self._convert_to_stops(best_state[1][2], segments, prices)
    
    def _calculate_score(self, cost, stops, min_cost, max_cost, min_stops, max_stops):
        """Calculate weighted score for a solution."""
        # Normalize
        norm_cost = (cost - min_cost) / (max_cost - min_cost) if max_cost > min_cost else 0
        norm_stops = (stops - min_stops) / (max_stops - min_stops) if max_stops > min_stops else 0
        
        # Weighted combination
        score = self.COST_WEIGHT * norm_cost + self.STOPS_WEIGHT * norm_stops
        return score
    
    def _better_score(self, cost1, stops1, cost2, stops2, min_cost, max_cost, min_stops, max_stops):
        """Compare two solutions."""
        score1 = self._calculate_score(cost1, stops1, min_cost, max_cost, min_stops, max_stops)
        score2 = self._calculate_score(cost2, stops2, min_cost, max_cost, min_stops, max_stops)
        return score1 < score2
```

**Characteristics:**
- **Stops**: Between minimum and cheapest strategies
- **Cost**: Near-optimal, better than minimum stops
- **Complexity**: Most complex, uses dynamic programming
- **Use Case**: General purpose, good default choice

---

## Edge Cases & Validation

### 1. Route Too Long for Single Tank

**Problem:** Total distance > max range

**Detection:**
```python
if route.total_distance_km > max_range_km:
    raise ValueError("Route requires multiple refuels")
```

**Solution:** Algorithm automatically handles with multiple stops

### 2. Segment Longer Than Safe Range

**Problem:** Single country segment > safe range

**Detection:**
```python
for segment in segments:
    if segment.distance > safe_range_km:
        raise ValueError(f"Cannot traverse {segment.country} safely")
```

**Solution:** Either increase tank size or reduce reservoir

### 3. No Fuel Price Data

**Problem:** Missing prices for route countries

**Detection:**
```python
for segment in segments:
    if segment.country not in fuel_prices:
        raise ValueError(f"No price data for {segment.country}")
```

**Solution:** Manual price entry or skip route

### 4. Reservoir > Max Range

**Problem:** User sets impossible reservoir

**Detection:**
```python
if reservoir_km >= max_range_km:
    raise ValueError("Reservoir cannot exceed max range")
```

**Solution:** Reduce reservoir or change car

### 5. Very Short Routes

**Problem:** Route < reservoir

**Handling:**
```python
if route.total_distance_km < reservoir_km:
    # No refueling needed at all
    return []
```

### 6. Circular Routes

**Problem:** Route crosses same country multiple times

**Handling:**
- Treat as separate segments
- May refuel multiple times in same country
- Cheapest strategy handles this well

---

## Performance Optimization

### 1. Waypoint Granularity

**Trade-off:** More waypoints = better accuracy but slower processing

**Optimization:**
```python
def optimize_waypoints(waypoints, target_count=50):
    """
    Reduce waypoints to target count while preserving country boundaries.
    """
    if len(waypoints) <= target_count:
        return waypoints
    
    # Always keep first, last, and country boundary points
    critical_points = [0, len(waypoints) - 1]
    
    for i in range(1, len(waypoints)):
        if waypoints[i]['country_code'] != waypoints[i-1]['country_code']:
            critical_points.extend([i-1, i])
    
    # Sample remaining points evenly
    step = (len(waypoints) - len(critical_points)) // (target_count - len(critical_points))
    sampled = critical_points + list(range(0, len(waypoints), step))
    
    return [waypoints[i] for i in sorted(set(sampled))]
```

### 2. Price Caching

Cache fuel prices with Redis:

```python
def get_fuel_prices(country_codes, fuel_type):
    """Get prices with caching."""
    cache_key = f"prices:{fuel_type}:{':'.join(sorted(country_codes))}"
    
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    prices = db.query_prices(country_codes, fuel_type)
    redis.setex(cache_key, 3600, json.dumps(prices))  # 1 hour cache
    
    return prices
```

### 3. Parallel Strategy Calculation

For compare endpoint:

```python
from concurrent.futures import ThreadPoolExecutor

def calculate_all_strategies(route, car, reservoir_km):
    """Calculate all strategies in parallel."""
    strategies = [
        ('cheapest', CheapestStrategy),
        ('min_stops', MinimumStopsStrategy),
        ('balanced', BalancedStrategy)
    ]
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            name: executor.submit(
                StrategyClass(route, car, reservoir_km).calculate
            )
            for name, StrategyClass in strategies
        }
        
        results = {
            name: future.result()
            for name, future in futures.items()
        }
    
    return results
```

---

## Testing Scenarios

### Test Case 1: Basic Short Route

```python
def test_short_route():
    """Test route shorter than safe range."""
    route = create_route("Warsaw", "Poznan", 300)  # 300km
    car = create_car(tank=50, consumption=6)        # Range: 833km
    reservoir = 100
    
    stops = MinimumStopsStrategy(route, car, reservoir).calculate()
    
    assert len(stops) == 0, "Should not need refueling"
```

### Test Case 2: Exactly One Stop Needed

```python
def test_one_stop_route():
    """Test route requiring exactly one stop."""
    route = create_route("Warsaw", "Berlin", 570)
    car = create_car(tank=40, consumption=8)        # Range: 500km
    reservoir = 50                                   # Safe: 450km
    
    stops = MinimumStopsStrategy(route, car, reservoir).calculate()
    
    assert len(stops) == 1
    assert 400 <= stops[0]['distance_from_start_km'] <= 450
```

### Test Case 3: Cheapest vs Expensive Countries

```python
def test_price_optimization():
    """Test that cheapest strategy saves money."""
    route = create_multi_country_route([
        ("PL", 200, 1.30),
        ("DE", 300, 1.65),
        ("NL", 200, 1.70)
    ])
    car = create_car(tank=60, consumption=7)
    reservoir = 100
    
    cheap_stops = CheapestStrategy(route, car, reservoir).calculate()
    min_stops = MinimumStopsStrategy(route, car, reservoir).calculate()
    
    cheap_cost = sum(s['total_cost'] for s in cheap_stops)
    min_cost = sum(s['total_cost'] for s in min_stops)
    
    assert cheap_cost <= min_cost, "Cheapest should cost less or equal"
    
    # Verify refueling happens in Poland (cheapest)
    poland_refuels = [s for s in cheap_stops if s['country_code'] == 'PL']
    assert len(poland_refuels) > 0, "Should refuel in Poland"
```

### Test Case 4: Edge Case - Impossible Route

```python
def test_impossible_route():
    """Test route that cannot be completed."""
    route = create_route("Warsaw", "Moscow", 1200)
    car = create_car(tank=50, consumption=10)       # Range: 500km
    reservoir = 100                                  # Safe: 400km
    
    # Segment longer than safe range
    with pytest.raises(ValueError, match="Cannot traverse"):
        MinimumStopsStrategy(route, car, reservoir).calculate()
```

### Test Case 5: Circular Route

```python
def test_circular_route():
    """Test route crossing same country multiple times."""
    route = create_circular_route([
        ("PL", 200),
        ("DE", 300),
        ("CZ", 100),
        ("PL", 200)  # Back to Poland
    ])
    car = create_car(tank=60, consumption=7)
    reservoir = 50
    
    stops = CheapestStrategy(route, car, reservoir).calculate()
    
    # Should optimize for both PL segments
    pl_stops = [s for s in stops if s['country_code'] == 'PL']
    assert len(pl_stops) >= 1, "Should refuel in Poland"
```

---

## Algorithm Comparison Summary

| Aspect | Minimum Stops | Cheapest | Balanced |
|--------|---------------|----------|----------|
| **Primary Goal** | Minimize stops | Minimize cost | Balance both |
| **Typical Stops** | 1-2 | 2-4 | 1-3 |
| **Cost** | Higher | Lowest | Medium |
| **Complexity** | O(n) | O(n²) | O(n² × m) |
| **Best For** | Time-sensitive | Budget-conscious | General use |
| **Predictability** | High | Medium | Medium |

**Recommendations:**
- **Business travelers**: Minimum Stops
- **Long-distance tourists**: Cheapest
- **Default**: Balanced

---

## Future Enhancements

### 1. Real-time Traffic

Incorporate traffic data to adjust fuel consumption:
```
adjusted_consumption = base_consumption × traffic_factor
```

### 2. Elevation Profile

Account for hills affecting consumption:
```
elevation_factor = 1 + (elevation_gain / distance) × 0.1
adjusted_consumption = base_consumption × elevation_factor
```

### 3. Weather Conditions

Temperature and wind affect consumption:
```
weather_factor = 1 + wind_speed × 0.05 + temp_effect
```

### 4. Historical Optimization

Learn from past trips:
```
ml_adjusted_consumption = model.predict(
    route, weather, traffic, driver_profile
)
```

### 5. Station-Specific Prices

Instead of country averages, use actual station prices:
```
stations = get_nearby_stations(waypoint, radius=50km)
best_station = min(stations, key=lambda s: s.price)
```

---

## References

- [Dynamic Programming](https://en.wikipedia.org/wiki/Dynamic_programming)
- [Vehicle Routing Problem](https://en.wikipedia.org/wiki/Vehicle_routing_problem)
- [Greedy Algorithms](https://en.wikipedia.org/wiki/Greedy_algorithm)
- Fuel Consumption Standards (EU Regulation)