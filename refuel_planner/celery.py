"""
Celery configuration for OptimalRefuelPlanner.
"""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'refuel_planner.settings')

app = Celery('refuel_planner')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'scrape-fuel-prices-daily': {
        'task': 'fuel_prices.scrape_fuel_prices',
        'schedule': crontab(hour=1, minute=0),  # 2:00 AM UTC daily
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not picked up
        },
    },
}

# Set timezone for scheduled tasks
app.conf.timezone = 'Europe/Warsaw'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working correctly."""
    print(f'Request: {self.request!r}')