# Refuel Planner Backend

> Inteligentna optymalizacja tras i planowanie kosztów paliwa dla podróży międzynarodowych

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-4.2+-green.svg)](https://www.djangoproject.com/)

## 🚀 Szybki Start

### Wymagania

- Docker 20.10+
- Docker Compose 2.0+

### Instalacja

```bash
# 1. Uruchom usługi
docker-compose up --build

# 2. Utwórz superużytkownika
docker-compose exec web python manage.py createsuperuser

# 3. Dostęp do API
http://localhost:8000/api/
```

**Dokumentacja API:** [Swagger UI](http://localhost:8000/api/schema/swagger-ui/)  
**Panel administracyjny:** http://localhost:8000/admin

## 📚 Kluczowe Funkcje

- 🗺️ Upload i parsowanie plików GPX
- 💰 Śledzenie cen paliw w Europie
- 🎯 Strategia optymalizacji Minimum Postojów
- 🚗 Obsługa wielu pojazdów
- 🔒 Bezpieczne REST API z uwierzytelnianiem JWT
- 📊 Offline wykrywanie krajów przy użyciu danych Natural Earth

## 📊 Główne Endpointy API

```
POST /api/auth/register/        # Rejestracja użytkownika
POST /api/auth/login/           # Logowanie i uzyskanie tokenów JWT

GET  /api/cars/                 # Lista pojazdów użytkownika
POST /api/cars/                 # Utworzenie profilu pojazdu

POST /api/routes/               # Upload pliku GPX
GET  /api/routes/               # Lista tras użytkownika

GET  /api/fuel-prices/          # Lista cen paliw

POST /api/refuel-plans/         # Obliczenie planu tankowania
GET  /api/refuel-plans/         # Lista planów użytkownika
```

**Pełna dokumentacja API:** [Swagger UI](http://localhost:8000/api/schema/swagger-ui/)

## 🗂️ Struktura Projektu

```
refuel_planner/
├── cars/                    # Zarządzanie profilami pojazdów
├── fuel_prices/             # Śledzenie cen paliw
├── planner/                 # Silnik planowania tankowań
│   ├── services/           # Logika biznesowa
│   └── strategies/         # Algorytmy optymalizacji
├── routes/                  # Zarządzanie trasami i parsowanie GPX
│   ├── services/           # Usługi przetwarzania tras
│   └── data/               # Dane geograficzne Natural Earth
├── users/                   # Uwierzytelnianie użytkowników
├── refuel_planner/         # Ustawienia projektu Django
├── docs/                    # Dokumentacja
├── tests/                   # Testy E2E
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 📖 Dokumentacja

**Główna dokumentacja API:** [Swagger UI](http://localhost:8000/api/schema/swagger-ui/) - Interaktywna, zawsze aktualna

**Dokumentacja referencyjna:**
- [`docs/models-reference.md`](docs/models-reference.md) - Modele bazy danych i walidacja
- [`docs/04-algorithms.md`](docs/04-algorithms.md) - Szczegóły strategii Minimum Postojów
- [`tests/test_e2e_mvp.py`](tests/test_e2e_mvp.py) - Przykład kompletnego workflow

## 🧪 Testowanie

```bash
# Uruchom wszystkie testy
pytest

# Z pokryciem kodu
pytest --cov

# Konkretny plik testowy
pytest planner/tests/test_planner_api.py

# Testy E2E
pytest tests/test_e2e_mvp.py -v
```

**Struktura testów:**
- Testy jednostkowe: `*/tests/test_*.py`
- Testy E2E: [`tests/test_e2e_mvp.py`](tests/test_e2e_mvp.py)
- Fixture'y: [`conftest.py`](conftest.py)

## 🔧 Rozwój

```bash
# Wyświetl logi
docker-compose logs -f web

# Dostęp do shella
docker-compose exec web python manage.py shell

# Uruchom migracje
docker-compose exec web python manage.py migrate
```

## 🛠️ Stack Technologiczny

- **Framework:** Django 4.2 + Django REST Framework
- **Język:** Python 3.11+
- **Baza danych:** PostgreSQL 15
- **Deployment:** Docker

## 📄 Licencja

Ten projekt jest licencjonowany na licencji MIT - szczegóły w pliku [`LICENSE`](LICENSE).

---

## 👤 Autor

**Rafał Szczerba**

- GitHub: [@RMaster121](https://github.com/RMaster121/)
- Email: rs.szczerba@hotmail.com

---

**Stworzone z ❤️ dla podróżnych, którzy chcą oszczędzać na kosztach paliwa**