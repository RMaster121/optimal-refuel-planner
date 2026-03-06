"""
Celery tasks for automated fuel price scraping.

Tasks:
- scrape_fuel_prices_task: Scheduled task to scrape fuel prices daily

Schedule Configuration:
Add to settings.py:
    from celery.schedules import crontab
    
    CELERY_BEAT_SCHEDULE = {
        'scrape-fuel-prices-daily': {
            'task': 'fuel_prices.scrape_fuel_prices',
            'schedule': crontab(hour=2, minute=0),  # 2:00 AM UTC daily
            'options': {'expires': 3600},
        },
    }
"""

from celery import shared_task
from django.conf import settings
import logging
import os

from .scrapers.manager import ScraperManager
from .scrapers.html_table_scraper import HTMLTableScraper


logger = logging.getLogger(__name__)


@shared_task(
    name='fuel_prices.scrape_fuel_prices',
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def scrape_fuel_prices_task(self):
    """
    Scheduled Celery task to scrape fuel prices.
    
    This task is designed to run automatically on a schedule (e.g., daily)
    to keep fuel price data up-to-date. It includes automatic retry logic
    for transient failures.
    
    Retries:
    - Maximum 3 retry attempts
    - 5-minute delay between retries
    - Exponential backoff on repeated failures
    
    Returns:
        dict: Scraping workflow report with statistics
        
    Raises:
        Exception: Re-raised after max retries exhausted
        
    Example Schedule (add to settings.py):
        CELERY_BEAT_SCHEDULE = {
            'scrape-fuel-prices-daily': {
                'task': 'fuel_prices.scrape_fuel_prices',
                'schedule': crontab(hour=2, minute=0),
            },
        }
    """
    logger.info("Starting scheduled fuel price scraping task")
    
    # Get source URL from settings or environment
    source_url = (
        os.environ.get('FUEL_PRICE_SOURCE_URL') or
        getattr(settings, 'FUEL_PRICE_SOURCE_URL', None)
    )
    
    if not source_url:
        error_msg = "FUEL_PRICE_SOURCE_URL not configured in settings or environment"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }
    
    try:
        # Initialize scraper manager
        manager = ScraperManager(scraper_class=HTMLTableScraper)
        
        # Run scraping workflow
        report = manager.run_scraping(
            source_url=source_url,
            auto_create_countries=True
        )
        
        # Check if scraping succeeded
        if not report['success']:
            error_msg = f"Scraping failed: {report.get('errors', [])}"
            logger.error(error_msg)
            
            # Retry the task
            raise self.retry(
                exc=Exception(error_msg),
                countdown=self.default_retry_delay * (2 ** self.request.retries)
            )
        
        # Log success
        stats = report.get('loaded_stats', {})
        logger.info(
            f"Scraping task completed successfully: "
            f"{stats.get('created', 0)} created, "
            f"{stats.get('updated', 0)} updated, "
            f"{stats.get('skipped', 0)} skipped"
        )
        
        return report
        
    except Exception as exc:
        logger.error(f"Scraping task error: {exc}", exc_info=True)
        
        # Retry with exponential backoff
        raise self.retry(
            exc=exc,
            countdown=self.default_retry_delay * (2 ** self.request.retries)
        )


@shared_task(name='fuel_prices.test_scraper_connection')
def test_scraper_connection():
    """
    Test task to verify scraper connectivity and configuration.
    
    This is a diagnostic task that can be run manually to verify
    that the scraper system is properly configured and can
    connect to the data source.
    
    Returns:
        dict: Connection test results
        
    Example:
        From Django shell or Celery:
        >>> from fuel_prices.tasks import test_scraper_connection
        >>> result = test_scraper_connection.delay()
        >>> print(result.get())
    """
    logger.info("Testing scraper connection")
    
    source_url = (
        os.environ.get('FUEL_PRICE_SOURCE_URL') or
        getattr(settings, 'FUEL_PRICE_SOURCE_URL', None)
    )
    
    if not source_url:
        return {
            'success': False,
            'error': 'FUEL_PRICE_SOURCE_URL not configured'
        }
    
    try:
        from .scrapers.html_table_scraper import HTMLTableScraper
        from .scrapers.config import ScraperConfig
        
        # Test basic HTTP connectivity
        config = ScraperConfig()
        scraper = HTMLTableScraper(source_url, config=config)
        
        response = scraper.fetch()
        is_valid = scraper.validate_response(response)
        
        return {
            'success': is_valid,
            'source_url': source_url,
            'status_code': response.status_code,
            'content_length': len(response.content),
            'message': 'Connection successful' if is_valid else 'Validation failed'
        }
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }