# Models Reference

Database models for the OptimalRefuelPlanner system.

---

## Base Models

### TimestampedModel
**Location:** [`refuel_planner/models.py`](../refuel_planner/models.py)

Provides automatic `created_at` and `updated_at` timestamps.

### ValidatedModel
**Location:** [`refuel_planner/models.py`](../refuel_planner/models.py)

Enforces full validation via `full_clean()` on every save.

---

## User

**Location:** [`users/models.py`](../users/models.py)

Extended Django user model with timestamp tracking.

**Key Method:** `__str__()` returns full name, email, or username.

---

## Car

**Location:** [`cars/models.py`](../cars/models.py)

Vehicle with fuel consumption characteristics.

**Fields:**
- `user` (ForeignKey) - Owner
- `name` (CharField) - Vehicle identifier, unique per user
- `fuel_type` (CharField) - "gasoline" or "diesel"
- `avg_consumption` (Decimal) - L/100km, range 1.0-30.0
- `tank_capacity` (Decimal) - Liters, range 20.0-200.0

**Computed Property:**
```python
max_range_km = (tank_capacity / avg_consumption) * 100
```

**Validation:** Name sanitized for XSS, values must be positive and realistic.

---

## Route

**Location:** [`routes/models.py`](../routes/models.py)

Parsed route from GPX file upload.

**Fields:**
- `user` (ForeignKey) - Creator
- `origin` (CharField) - Start location name
- `destination` (CharField) - End location name
- `total_distance_km` (Decimal) - Total distance
- `waypoints` (JSONField) - List of waypoint dicts
- `countries` (JSONField) - List of ISO country codes

**Waypoint Structure:**
```json
{
  "lat": 52.23,
  "lng": 21.01,
  "distance_from_start_km": "0.00",
  "country_code": "PL"
}
```

---

## Country

**Location:** [`fuel_prices/models.py`](../fuel_prices/models.py)

Supported countries for fuel pricing.

**Fields:**
- `code` (CharField) - ISO 3166-1 alpha-2, unique
- `name` (CharField) - Human-readable name, unique

**String:** Returns `"Poland (PL)"` format.

---

## FuelPrice

**Location:** [`fuel_prices/models.py`](../fuel_prices/models.py)

Fuel prices per country, fuel type, and day.

**Fields:**
- `country` (ForeignKey) - Related country
- `fuel_type` (CharField) - "gasoline" or "diesel"
- `price_per_liter` (Decimal) - EUR, must be positive
- `scraped_at` (DateTimeField) - When price was obtained

**Unique Constraint:** `(country, fuel_type, DATE(scraped_at))`
- One price per country/fuel/day
- Enables historical tracking

**Computed Properties:**
- `country_code` - Returns country's ISO code
- `country_name` - Returns country's name

---

## RefuelPlan

**Location:** [`planner/models.py`](../planner/models.py)

Computed refueling strategy for a route and vehicle.

**Fields:**
- `route` (ForeignKey) - Associated route
- `car` (ForeignKey) - Vehicle used
- `reservoir_km` (IntegerField) - Safety reserve, default 100
- `optimization_strategy` (CharField) - "min_stops" (MVP)
- `total_cost` (Decimal) - Total fuel cost in EUR
- `total_fuel_needed` (Decimal) - Total liters required
- `number_of_stops` (IntegerField) - Refuel stop count

**Strategy:** Currently only "min_stops" is implemented.

---

## RefuelStop

**Location:** [`planner/models.py`](../planner/models.py)

Individual refueling stop within a plan.

**Fields:**
- `plan` (ForeignKey) - Parent refuel plan
- `stop_number` (IntegerField) - Sequential number, ≥ 1
- `country` (ForeignKey) - Stop location country
- `fuel_price` (ForeignKey) - Fuel price used
- `distance_from_start_km` (Decimal) - Distance from origin
- `fuel_to_add_liters` (Decimal) - Fuel amount
- `total_cost` (Decimal) - Cost at this stop
- `latitude` (Decimal, optional) - Stop latitude
- `longitude` (Decimal, optional) - Stop longitude

**Unique Constraint:** `(plan, stop_number)`

**Validation:** Ensures fuel price type matches car's fuel type and country.

---

## Validation System

**Location:** [`refuel_planner/validators.py`](../refuel_planner/validators.py)

### Key Validators

- `validate_positive_decimal(value, field_name)` - Ensures value > 0
- `validate_non_negative_decimal(value, field_name)` - Ensures value ≥ 0
- `validate_positive_integer(value, field_name)` - Ensures integer ≥ 1
- `validate_non_negative_integer(value, field_name)` - Ensures integer ≥ 0
- `validate_and_sanitize_name(value, field_name, max_length)` - XSS protection
- `validate_and_sanitize_location(value, field_name, max_length)` - Whitelist validation
- `iso_country_code_validator` - Validates ISO 3166-1 alpha-2 codes

### Validation Flow

1. Field-level validation (Django built-in)
2. `Model.clean()` - Custom validation
3. `Model.save()` - Automatically calls `full_clean()` via `ValidatedModel`

---

## Model Relationships

```
User
├── cars (Car)
│   └── refuel_plans (RefuelPlan)
│       └── stops (RefuelStop)
│           ├── country (Country)
│           └── fuel_price (FuelPrice)
│               └── country (Country)
└── routes (Route)
    └── refuel_plans (RefuelPlan)

Country
├── fuel_prices (FuelPrice)
└── refuel_stops (RefuelStop)
```

---

## Manager Classes

### FuelPriceManager
Auto-optimizes queries with `select_related('country')`.

### RefuelPlanManager
Auto-optimizes queries with `select_related('route', 'car')`.

### RefuelStopManager
Auto-optimizes with deep `select_related` including country, fuel_price, plan, car, and route.

---

## See Also

- **API Documentation**: [Swagger UI](http://localhost:8000/api/schema/swagger-ui/)
- **Algorithm Details**: [`04-algorithms.md`](04-algorithms.md)
- **Code Examples**: [`../tests/test_e2e_mvp.py`](../tests/test_e2e_mvp.py)