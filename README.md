# Refuel Planner Backend

> Intelligent route optimization and fuel cost planning for cross-country travel

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-4.2+-green.svg)](https://www.djangoproject.com/)

## ✅ MVP Status

The MVP is **COMPLETE** and includes:

- ✅ User authentication (JWT)
- ✅ Car profile management
- ✅ GPX route upload & parsing
- ✅ Offline country detection
- ✅ Minimum Stops refuel planning algorithm
- ✅ Complete REST API

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Installation

```bash
# 1. Start services
docker-compose up --build

# 2. Create superuser
docker-compose exec web python manage.py createsuperuser

# 3. Access API
http://localhost:8000/api/
```

**API Documentation:** [`docs/API.md`](docs/API.md)  
**Admin Panel:** http://localhost:8000/admin

## 📚 Key Features

- 🗺️ GPX route upload and parsing
- 💰 Fuel price tracking across Europe
- 🎯 Minimum Stops optimization strategy
- 🚗 Multi-vehicle support
- 🔒 Secure REST API with JWT authentication
- 📊 Offline country detection using Natural Earth data

## 📊 Core API Endpoints

```
POST /api/auth/register/        # Register new user
POST /api/auth/login/           # Login and get JWT tokens

GET  /api/cars/                 # List user's cars
POST /api/cars/                 # Create car profile

POST /api/routes/upload-gpx/    # Upload GPX file
GET  /api/routes/               # List user's routes

GET  /api/fuel-prices/          # List fuel prices

POST /api/refuel-plans/         # Calculate refuel plan
GET  /api/refuel-plans/         # List user's plans
```

**Full API reference:** [`docs/api-reference.md`](docs/api-reference.md)

## 🗂️ Project Structure

```
refuel_planner/
├── cars/                    # Car profile management
├── fuel_prices/             # Fuel price tracking
├── planner/                 # Refuel planning engine
│   ├── services/           # Business logic
│   └── strategies/         # Optimization algorithms
├── routes/                  # Route management & GPX parsing
│   ├── services/           # Route processing services
│   └── data/               # Natural Earth geographic data
├── users/                   # User authentication
├── refuel_planner/         # Django project settings
├── docs/                    # Documentation
├── tests/                   # E2E tests
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 📖 Documentation

**Primary API Docs:** [Swagger UI](http://localhost:8000/api/schema/swagger-ui/) - Interactive, always up-to-date

**Reference Docs:**
- [`models-reference.md`](docs/models-reference.md) - Database models and validation
- [`04-algorithms.md`](docs/04-algorithms.md) - Minimum Stops strategy details
- [`tests/test_e2e_mvp.py`](tests/test_e2e_mvp.py) - Complete workflow example

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest planner/tests/test_planner_api.py

# Run E2E tests
pytest tests/test_e2e_mvp.py -v
```

**Test Structure:**
- Unit tests: `*/tests/test_*.py`
- E2E tests: [`tests/test_e2e_mvp.py`](tests/test_e2e_mvp.py)
- Fixtures: [`conftest.py`](conftest.py)

## 🔧 Development

```bash
# View logs
docker-compose logs -f web

# Access shell
docker-compose exec web python manage.py shell

# Run migrations
docker-compose exec web python manage.py migrate
```

## 🛠️ Technology Stack

- **Framework:** Django 4.2 + Django REST Framework
- **Language:** Python 3.11+
- **Database:** PostgreSQL 15
- **Deployment:** Docker

## 📄 License

TBD - To be determined

---

**Made with ❤️ for travelers who want to save on fuel costs**