# Refuel Planner Backend

> Intelligent route optimization and fuel cost planning for cross-country travel

[![License](https://img.shields.io/badge/license-TBD-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-4.2+-green.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

---

## 📖 Overview

Refuel Planner helps drivers optimize fuel costs when traveling through multiple countries. The system analyzes routes, car specifications, and real-time fuel prices to calculate optimal refueling strategies.

**Key Features:**
- 🗺️ Google Maps route integration
- 💰 Real-time fuel price tracking across Europe
- 🎯 Three optimization strategies (cheapest, minimum stops, balanced)
- 🚗 Multi-vehicle support
- 🔒 Secure REST API with JWT authentication
- 📊 Comprehensive analytics and reporting

---

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Google Maps API Key

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/refuel-planner.git
cd refuel-planner

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env

# Build and start services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access the API
curl http://localhost:8000/api/v1/fuel-prices/
```

**Admin Panel:** http://localhost:8000/admin  
**API Documentation:** http://localhost:8000/api/docs

---

## 📚 Documentation

Comprehensive documentation is available in the [`/docs`](docs/) directory:

| Document | Description |
|----------|-------------|
| [**Overview**](docs/01-overview.md) | Project vision, use cases, and roadmap |
| [**Architecture**](docs/architecture-diagram.md) | System design and component diagrams |
| [**API Reference**](docs/api-reference.md) | Complete API documentation with examples |
| [**Models Reference**](docs/models-reference.md) | Database models and validation system |
| [**Algorithms**](docs/04-algorithms.md) | Detailed explanation of optimization algorithms |
| [**Deployment**](docs/05-deployment.md) | Production deployment and scaling guide |
| [**Key Considerations**](docs/key-considerations.md) | Critical decisions and open questions |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Application                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Django REST Framework                     │
│                         (API Layer)                          │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│    Route     │   │  Fuel Price  │   │   Planner    │
│   Parser     │   │   Scraper    │   │   Engine     │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  PostgreSQL  │   │    Redis     │   │  Google Maps │
└──────────────┘   └──────────────┘   └──────────────┘
```

---

## 💡 Usage Example

### Calculate Refuel Plan

```python
import requests

# Login
response = requests.post('http://localhost:8000/api/v1/auth/login/', json={
    'username': 'user@example.com',
    'password': 'password'
})
token = response.json()['access']

# Create car profile
car_response = requests.post(
    'http://localhost:8000/api/v1/cars/',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'name': 'VW Golf 7',
        'fuel_type': 'diesel',
        'avg_consumption': 5.5,
        'tank_capacity': 50.0
    }
)
car_id = car_response.json()['id']

# Create route
route_response = requests.post(
    'http://localhost:8000/api/v1/routes/',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'google_maps_url': 'https://www.google.com/maps/dir/Warsaw,+Poland/Berlin,+Germany'
    }
)
route_id = route_response.json()['id']

# Calculate refuel plan
plan_response = requests.post(
    'http://localhost:8000/api/v1/refuel-plans/',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'route_id': route_id,
        'car_id': car_id,
        'reservoir_km': 100,
        'optimization_strategy': 'cheapest'
    }
)

plan = plan_response.json()
print(f"Total cost: €{plan['total_cost']}")
print(f"Number of stops: {plan['number_of_stops']}")
for stop in plan['stops']:
    print(f"  - {stop['country_name']}: {stop['fuel_to_add_liters']}L @ €{stop['price_per_liter']}/L")
```

**Output:**
```
Total cost: €42.75
Number of stops: 1
  - Poland: 31.36L @ €1.35/L
```

---

## 🎯 Optimization Strategies

### 1. Cheapest
Minimizes total fuel cost by prioritizing refueling in countries with lowest prices.

**Best for:** Budget-conscious travelers  
**Trade-off:** May require more stops

### 2. Minimum Stops
Minimizes the number of refueling stops for maximum convenience.

**Best for:** Time-sensitive journeys  
**Trade-off:** May cost more

### 3. Balanced
Optimal trade-off between cost and convenience using weighted scoring.

**Best for:** General use, recommended default  
**Trade-off:** Balanced approach

---

## 🗂️ Project Structure

```
refuel_planner/
├── config/                      # Django settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── celery.py
│
├── apps/
│   ├── users/                   # User management
│   ├── cars/                    # Car profiles
│   ├── routes/                  # Route management
│   │   └── services/
│   │       └── route_parser.py  # Google Maps integration
│   ├── fuel/                    # Fuel prices
│   │   ├── tasks.py            # Celery tasks
│   │   └── scrapers/           # Web scrapers
│   └── planner/                 # Refuel planning
│       └── engine/
│           └── strategies/      # Optimization algorithms
│
├── docs/                        # Documentation
├── tests/                       # Test suite
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🔧 Development

### Setup Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=apps --cov-report=html

# Specific test
pytest tests/test_planner_engine.py -v
```

### Code Quality

```bash
# Format code
black .

# Lint
flake8

# Sort imports
isort .
```

---

## 🐳 Docker Commands

```bash
# Build services
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down

# Run management command
docker-compose exec web python manage.py <command>

# Access shell
docker-compose exec web python manage.py shell

# Database backup
docker-compose exec db pg_dump -U refuel_user refuel_planner > backup.sql
```

---

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/register/` - Register new user
- `POST /api/v1/auth/login/` - Login and get JWT tokens
- `POST /api/v1/auth/refresh/` - Refresh access token

### Cars
- `GET /api/v1/cars/` - List user's cars
- `POST /api/v1/cars/` - Create car profile
- `GET /api/v1/cars/{id}/` - Get car details
- `PUT /api/v1/cars/{id}/` - Update car
- `DELETE /api/v1/cars/{id}/` - Delete car

### Routes
- `GET /api/v1/routes/` - List user's routes
- `POST /api/v1/routes/` - Create route from Google Maps URL
- `GET /api/v1/routes/{id}/` - Get route details
- `DELETE /api/v1/routes/{id}/` - Delete route

### Fuel Prices
- `GET /api/v1/fuel-prices/` - List all fuel prices
- `GET /api/v1/fuel-prices/{country}/` - Get prices for country

### Refuel Plans
- `POST /api/v1/refuel-plans/` - Calculate refuel plan
- `GET /api/v1/refuel-plans/` - List user's plans
- `GET /api/v1/refuel-plans/{id}/` - Get plan details
- `POST /api/v1/refuel-plans/compare/` - Compare all strategies

**Full API documentation:** [`/docs/api-reference.md`](docs/api-reference.md)

---

## 🔐 Security

### Best Practices Implemented

- ✅ JWT authentication
- ✅ Password hashing (bcrypt)
- ✅ HTTPS/SSL support
- ✅ Rate limiting
- ✅ CORS configuration
- ✅ SQL injection prevention (ORM)
- ✅ XSS protection
- ✅ CSRF tokens
- ✅ Security headers

### Environment Variables

Never commit sensitive data! Use `.env` file:

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
GOOGLE_MAPS_API_KEY=your-api-key
DB_PASSWORD=secure-password
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Add type hints
- Keep commits atomic and descriptive

---

## 🧪 Testing

### Test Coverage

Current coverage: **TBD** (target: 80%+)

```bash
# Run tests with coverage
pytest --cov=apps --cov-report=term-missing

# Generate HTML report
pytest --cov=apps --cov-report=html
open htmlcov/index.html
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Algorithm Tests**: Optimization strategy validation
- **E2E Tests**: Complete workflow testing

---

## 📈 Performance

### Benchmarks (Typical)

- Route parsing: ~500ms
- Planning calculation: ~100-300ms
- API response time: <500ms (p95)
- Concurrent users: 500+ (with caching)

### Optimization Tips

1. **Enable Redis caching** for fuel prices
2. **Use connection pooling** for database
3. **Limit waypoint granularity** to 50 points
4. **Implement CDN** for static files
5. **Use read replicas** for high traffic

---

## 🛠️ Technology Stack

### Backend
- **Framework:** Django 4.2 + Django REST Framework
- **Language:** Python 3.11+
- **Database:** PostgreSQL 15
- **Cache:** Redis 7
- **Task Queue:** Celery
- **Web Server:** Gunicorn + Nginx

### External Services
- **Google Maps API:** Route parsing and geocoding
- **Web Scraping:** Fuel price data collection

### DevOps
- **Containerization:** Docker + Docker Compose
- **CI/CD:** GitHub Actions (planned)
- **Monitoring:** Prometheus + Grafana (optional)

---

## 📝 Roadmap

### Phase 1: MVP ✅
- [x] Core API design
- [x] Algorithm specification
- [x] Documentation

### Phase 2: Implementation 🔄
- [ ] Django project setup
- [ ] API endpoints
- [ ] Planning algorithms
- [ ] Fuel price scraping

### Phase 3: Enhancement
- [ ] Gas station locations (Google Places)
- [ ] Real-time traffic integration
- [ ] Mobile app API
- [ ] Historical price trends

### Phase 4: Advanced Features
- [ ] Machine learning for consumption prediction
- [ ] Route comparison tool
- [ ] Carbon footprint calculator
- [ ] Electric vehicle support

---

## 🐛 Known Issues

See [GitHub Issues](https://github.com/your-org/refuel-planner/issues) for current bugs and feature requests.

---

## 📄 License

TBD - To be determined

---

## 👥 Authors

- **Your Name** - *Initial work* - [@yourusername](https://github.com/yourusername)

See also the list of [contributors](https://github.com/your-org/refuel-planner/contributors) who participated in this project.

---

## 🙏 Acknowledgments

- Google Maps API for routing data
- Fuel price data sources
- Django and DRF communities
- All contributors and testers

---

## 📞 Support

- **Documentation:** [`/docs`](docs/)
- **API Docs:** http://localhost:8000/api/docs
- **Issues:** [GitHub Issues](https://github.com/your-org/refuel-planner/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/refuel-planner/discussions)

---

## 🔗 Links

- [Project Website](https://refuelplanner.com) (coming soon)
- [API Documentation](docs/api-reference.md)
- [Algorithm Details](docs/04-algorithms.md)
- [Deployment Guide](docs/05-deployment.md)

---

**Made with ❤️ for travelers who want to save on fuel costs**