"""
Integration tests for ScraperManager.

Tests complete workflow:
1. Scraping
2. Country mapping
3. Validation
4. Database loading
"""

import pytest
from unittest.mock import Mock, patch
from django.utils import timezone
from fuel_prices.models import Country, FuelPrice
from fuel_prices.scrapers.manager import ScraperManager
from fuel_prices.scrapers.base import ScrapedFuelPrice


@pytest.mark.django_db
class TestScraperManager:
    """Test suite for ScraperManager orchestration."""
    
    @patch('fuel_prices.scrapers.html_table_scraper.HTMLTableScraper.run')
    def test_full_workflow_success(self, mock_scraper_run):
        """Test complete scraping workflow with valid data."""
        # Setup mock data
        now = timezone.now()
        mock_scraper_run.return_value = [
            ScrapedFuelPrice(
                country_name='Poland',
                country_code=None,  # Will be mapped
                fuel_type='gasoline',
                price_eur=1.397,
                scraped_at=now,
                source_url='http://example.com'
            ),
            ScrapedFuelPrice(
                country_name='Germany',
                country_code=None,
                fuel_type='diesel',
                price_eur=1.622,
                scraped_at=now,
                source_url='http://example.com'
            ),
        ]
        
        manager = ScraperManager()
        report = manager.run_scraping('http://example.com', auto_create_countries=True)
        
        assert report['success'] is True
        assert report['scraped_count'] == 2
        assert report['mapped_count'] == 2
        assert report['valid_count'] == 2
        assert report['loaded_stats']['created'] == 2
        
        # Verify database
        assert FuelPrice.objects.count() == 2
        assert Country.objects.count() == 2
    
    @patch('fuel_prices.scrapers.html_table_scraper.HTMLTableScraper.run')
    def test_workflow_with_unmapped_country(self, mock_scraper_run):
        """Test workflow handles unmapped countries."""
        now = timezone.now()
        mock_scraper_run.return_value = [
            ScrapedFuelPrice(
                country_name='Atlantis',  # Invalid country
                country_code=None,
                fuel_type='gasoline',
                price_eur=1.5,
                scraped_at=now,
                source_url='http://example.com'
            ),
        ]
        
        manager = ScraperManager()
        report = manager.run_scraping('http://example.com')
        
        assert report['success'] is False
        assert report['scraped_count'] == 1
        assert report['mapped_count'] == 0  # Couldn't map Atlantis
        assert 'Country mapping failed' in report['errors'][0]
    
    @patch('fuel_prices.scrapers.html_table_scraper.HTMLTableScraper.run')
    def test_workflow_with_invalid_data(self, mock_scraper_run):
        """Test workflow handles validation failures."""
        future_time = timezone.now() + timezone.timedelta(days=1)
        mock_scraper_run.return_value = [
            ScrapedFuelPrice(
                country_name='Poland',
                country_code=None,
                fuel_type='gasoline',
                price_eur=-1.0,  # Invalid: negative price
                scraped_at=future_time,  # Invalid: future date
                source_url='http://example.com'
            ),
        ]
        
        manager = ScraperManager()
        report = manager.run_scraping('http://example.com')
        
        assert report['success'] is False
        assert report['mapped_count'] == 1
        assert report['valid_count'] == 0  # Failed validation
        assert 'All records failed validation' in report['errors'][0]
    
    @patch('fuel_prices.scrapers.html_table_scraper.HTMLTableScraper.run')
    def test_workflow_no_data_scraped(self, mock_scraper_run):
        """Test workflow handles empty scraping result."""
        mock_scraper_run.return_value = []
        
        manager = ScraperManager()
        report = manager.run_scraping('http://example.com')
        
        assert report['success'] is False
        assert report['scraped_count'] == 0
        assert 'No data scraped' in report['errors'][0]
    
    @patch('fuel_prices.scrapers.html_table_scraper.HTMLTableScraper.run')
    def test_workflow_with_existing_countries(self, mock_scraper_run, country_poland):
        """Test workflow with pre-existing countries."""
        now = timezone.now()
        mock_scraper_run.return_value = [
            ScrapedFuelPrice(
                country_name='Poland',
                country_code=None,
                fuel_type='gasoline',
                price_eur=1.397,
                scraped_at=now,
                source_url='http://example.com'
            ),
        ]
        
        manager = ScraperManager()
        report = manager.run_scraping('http://example.com', auto_create_countries=False)
        
        assert report['success'] is True
        assert FuelPrice.objects.count() == 1
        assert Country.objects.count() == 1  # Only the pre-existing one
    
    @patch('fuel_prices.scrapers.html_table_scraper.HTMLTableScraper.run')
    def test_workflow_updates_existing_prices(self, mock_scraper_run, country_poland):
        """Test workflow updates existing fuel prices."""
        now = timezone.now()
        
        # Create existing price
        FuelPrice.objects.create(
            country=country_poland,
            fuel_type='gasoline',
            price_per_liter='1.300',
            scraped_at=now
        )
        
        # Scrape new price
        mock_scraper_run.return_value = [
            ScrapedFuelPrice(
                country_name='Poland',
                country_code=None,
                fuel_type='gasoline',
                price_eur=1.397,  # Different price
                scraped_at=now,
                source_url='http://example.com'
            ),
        ]
        
        manager = ScraperManager()
        report = manager.run_scraping('http://example.com', auto_create_countries=False)
        
        assert report['success'] is True
        assert report['loaded_stats']['updated'] == 1
        assert report['loaded_stats']['created'] == 0
        
        # Verify price was updated
        price = FuelPrice.objects.first()
        assert str(price.price_per_liter) == '1.397'
    
    @patch('fuel_prices.scrapers.html_table_scraper.HTMLTableScraper.run')
    def test_workflow_with_missing_prices(self, mock_scraper_run):
        """Test workflow handles missing prices (None values)."""
        now = timezone.now()
        mock_scraper_run.return_value = [
            ScrapedFuelPrice(
                country_name='Poland',
                country_code=None,
                fuel_type='gasoline',
                price_eur=None,  # Missing price
                scraped_at=now,
                source_url='http://example.com'
            ),
        ]
        
        manager = ScraperManager()
        report = manager.run_scraping('http://example.com', auto_create_countries=True)
        
        assert report['success'] is True
        assert report['loaded_stats']['skipped'] == 1
        assert FuelPrice.objects.count() == 0  # Nothing loaded
    
    @patch('fuel_prices.scrapers.html_table_scraper.HTMLTableScraper.run')
    def test_workflow_partial_success(self, mock_scraper_run):
        """Test workflow with mix of valid and invalid data."""
        now = timezone.now()
        mock_scraper_run.return_value = [
            ScrapedFuelPrice(
                country_name='Poland',
                country_code=None,
                fuel_type='gasoline',
                price_eur=1.397,  # Valid
                scraped_at=now,
                source_url='http://example.com'
            ),
            ScrapedFuelPrice(
                country_name='Germany',
                country_code=None,
                fuel_type='gasoline',
                price_eur=-1.0,  # Invalid
                scraped_at=now,
                source_url='http://example.com'
            ),
        ]
        
        manager = ScraperManager()
        report = manager.run_scraping('http://example.com', auto_create_countries=True)
        
        assert report['success'] is True
        assert report['valid_count'] == 1
        assert report['loaded_stats']['created'] == 1
        assert FuelPrice.objects.count() == 1
    
    @patch('fuel_prices.scrapers.html_table_scraper.HTMLTableScraper.run')
    def test_workflow_scraper_exception(self, mock_scraper_run):
        """Test workflow handles scraper exceptions."""
        from fuel_prices.scrapers.exceptions import ScraperException
        
        mock_scraper_run.side_effect = ScraperException("Connection failed")
        
        manager = ScraperManager()
        report = manager.run_scraping('http://example.com')
        
        assert report['success'] is False
        assert len(report['errors']) > 0
        assert 'Scraper error' in report['errors'][0]
    
    def test_workflow_with_sample_html(self, sample_scraper_html, mock_scraper_response):
        """Test workflow with actual HTML parsing."""
        with patch('requests.Session.get') as mock_get:
            mock_get.return_value = mock_scraper_response
            
            manager = ScraperManager()
            report = manager.run_scraping('http://example.com', auto_create_countries=True)
            
            assert report['success'] is True
            assert report['scraped_count'] > 0
            assert report['mapped_count'] > 0
            # Results depend on sample HTML content