from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="unsafe-secret-key")
DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "corsheaders",
    "users",
    "cars",
    "routes",
    "fuel_prices",
    "planner",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "refuel_planner.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "refuel_planner.wsgi.application"
ASGI_APPLICATION = "refuel_planner.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="optimal_refuel_planner"),
        "USER": config("POSTGRES_USER", default="optimal_refuel_user"),
        "PASSWORD": config("POSTGRES_PASSWORD", default="password"),
        "HOST": config("POSTGRES_HOST", default="db"),
        "PORT": config("POSTGRES_PORT", default=5432, cast=int),
        "CONN_MAX_AGE": config("DB_CONN_MAX_AGE", default=300, cast=int),
        "OPTIONS": {
            "connect_timeout": config("DB_CONNECT_TIMEOUT", default=5, cast=int),
        },
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://redis:6379/1"),
        "TIMEOUT": config("CACHE_DEFAULT_TIMEOUT", default=300, cast=int),
        "OPTIONS": {
            "ssl_cert_reqs": None,
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

DJANGO_LOG_LEVEL = config("DJANGO_LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": DJANGO_LOG_LEVEL,
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Optimal Refuel Planner API",
    "DESCRIPTION": (
        "REST API for planning optimal refueling stops across Europe. "
        "Upload GPX routes, manage vehicles, get fuel prices, and calculate cost-effective refueling strategies."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Schema generation settings
    "SCHEMA_PATH_PREFIX": r"/api/",
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,  # Keep operations in URL order
    # Swagger UI settings
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": False,  # Hide operation IDs for cleaner UI
        "defaultModelsExpandDepth": 2,
        "defaultModelExpandDepth": 2,
        "displayRequestDuration": True,
        "docExpansion": "list",  # Show endpoints collapsed by default
        "filter": True,  # Enable search/filter
        "showExtensions": True,
        "showCommonExtensions": True,
    },
    # Authentication settings
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "Bearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your JWT access token (obtain from /api/auth/login/)",
            }
        }
    },
    "SECURITY": [{"Bearer": []}],
    # Documentation enhancements
    "POSTPROCESSING_HOOKS": [],
    "PREPROCESSING_HOOKS": [],
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SERVERS": [
        {"url": "http://localhost:8000", "description": "Local Development Server"},
        {"url": "http://localhost:8000", "description": "Production Server (update in production)"},
    ],
    # Tag settings for better organization
    "TAGS": [
        {"name": "Authentication", "description": "User authentication and token management"},
        {"name": "Cars", "description": "Manage user vehicles and fuel consumption profiles"},
        {"name": "Routes", "description": "Upload and manage GPX routes with waypoint information"},
        {"name": "Fuel Prices", "description": "Access fuel price data across European countries"},
        {"name": "Refuel Plans", "description": "Generate and manage optimal refueling plans"},
    ],
    # Response settings
    "ENUM_NAME_OVERRIDES": {},
    "DISABLE_ERRORS_AND_WARNINGS": False,
    "AUTHENTICATION_WHITELIST": [],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),  # 1 hour
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),  # 7 days
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
}

_raw_cors_origins = config("DJANGO_ALLOWED_ORIGINS", default="", cast=Csv())
CORS_ALLOWED_ORIGINS = [origin for origin in _raw_cors_origins if origin]

# In development, allow all origins for Swagger UI to work
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = not CORS_ALLOWED_ORIGINS

CORS_ALLOW_CREDENTIALS = True

# CORS headers configuration for Swagger UI
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_EXPOSE_HEADERS = [
    "Content-Type",
    "X-CSRFToken",
]

CSRF_TRUSTED_ORIGINS = [
    origin for origin in config("DJANGO_CSRF_TRUSTED_ORIGINS", default="", cast=Csv()) if origin
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

INTERNAL_IPS = ["127.0.0.1", "localhost"]