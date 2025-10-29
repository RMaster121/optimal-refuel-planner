# syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . .

# Create non-root user
RUN addgroup --system web && adduser --system --ingroup web web
RUN chown -R web:web /app
USER web

EXPOSE 8000

ENV PORT=8000 \
    GUNICORN_WORKERS=${GUNICORN_WORKERS:-3}

CMD ["gunicorn", "refuel_planner.wsgi:application", "--bind", "0.0.0.0:8000"]