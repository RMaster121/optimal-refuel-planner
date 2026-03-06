"""
Unit tests for BaseScraper.

Tests:
- HTTP session creation
- Rate limiting
- Retry mechanism
- Error handling
- Context manager
"""

import pytest
from unittest.mock import Mock, patch
import time
import requests
from fuel_prices.scrapers.base import BaseScraper, ScrapedFuelPrice
from fuel_prices.scrapers.config import ScraperConfig
from fuel_prices.scrapers.exceptions import HTTPException


class ConcreteScraper(BaseScraper):
    """Concrete implementation of BaseScraper for testing."""
    
    def scrape(self):
        response = self.fetch()
        return self.parse_response(response)
    
    def validate_response(self, response):
        return response.status_code == 200
    
    def parse_response(self, response):
        # Simple mock parsing
        return [
            ScrapedFuelPrice(
                country_name='Poland',
                country_code='PL',
                fuel_type='gasoline',
                price_eur=1.5,
                scraped_at=time.time(),
                source_url=self.source_url
            )
        ]


class TestBaseScraper:
    """Test suite for BaseScraper abstract class."""
    
    def test_scraper_initialization(self):
        """Test basic scraper initialization."""
        scraper = ConcreteScraper(source_url='http://example.com')
        
        assert scraper.source_url == 'http://example.com'
        assert scraper.config is not None
        assert scraper.session is not None
    
    def test_scraper_with_custom_config(self):
        """Test scraper initialization with custom config."""
        config = ScraperConfig()
        scraper = ConcreteScraper(source_url='http://example.com', config=config)
        
        assert scraper.config == config
    
    def test_session_has_user_agent(self):
        """Test session has correct user agent header."""
        scraper = ConcreteScraper(source_url='http://example.com')
        
        assert 'User-Agent' in scraper.session.headers
        assert 'OptimalRefuelPlanner' in scraper.session.headers['User-Agent']
    
    def test_session_has_retry_adapter(self):
        """Test session has retry adapter configured."""
        scraper = ConcreteScraper(source_url='http://example.com')
        
        # Check adapters are mounted
        assert scraper.session.get_adapter('http://') is not None
        assert scraper.session.get_adapter('https://') is not None
    
    @patch('requests.Session.get')
    def test_fetch_success(self, mock_get):
        """Test successful fetch operation."""
        scraper = ConcreteScraper(source_url='http://example.com')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html></html>'
        mock_response.content = b'<html></html>'
        mock_get.return_value = mock_response
        
        response = scraper.fetch()
        
        assert response == mock_response
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_fetch_http_error(self, mock_get):
        """Test fetch handles HTTP errors."""
        scraper = ConcreteScraper(source_url='http://example.com')
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = 'Not Found'
        http_error = requests.HTTPError()
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response
        
        with pytest.raises(HTTPException):
            scraper.fetch()
    
    @patch('requests.Session.get')
    def test_fetch_timeout(self, mock_get):
        """Test fetch handles timeout errors."""
        scraper = ConcreteScraper(source_url='http://example.com')
        mock_get.side_effect = requests.Timeout()
        
        with pytest.raises(HTTPException, match='timeout'):
            scraper.fetch()
    
    @patch('requests.Session.get')
    def test_fetch_connection_error(self, mock_get):
        """Test fetch handles connection errors."""
        scraper = ConcreteScraper(source_url='http://example.com')
        mock_get.side_effect = requests.ConnectionError()
        
        with pytest.raises(HTTPException, match='Connection error'):
            scraper.fetch()
    
    @patch('requests.Session.get')
    def test_fetch_validation_failure(self, mock_get):
        """Test fetch handles response validation failure."""
        scraper = ConcreteScraper(source_url='http://example.com')
        
        mock_response = Mock()
        mock_response.status_code = 500  # Will fail validation
        mock_response.raise_for_status = Mock()  # Don't raise on status
        mock_get.return_value = mock_response
        
        with pytest.raises(HTTPException, match='validation failed'):
            scraper.fetch()
    
    def test_rate_limiting(self):
        """Test rate limiting delays requests."""
        config = ScraperConfig()
        config._rate_limit = 2.0  # 2 requests per second
        scraper = ConcreteScraper(source_url='http://example.com', config=config)
        
        # First request should not delay
        start_time = time.time()
        scraper._enforce_rate_limit()
        first_duration = time.time() - start_time
        
        assert first_duration < 0.1  # Should be instant
        
        # Second request should delay ~0.5 seconds (1/2 req/sec)
        start_time = time.time()
        scraper._enforce_rate_limit()
        second_duration = time.time() - start_time
        
        assert second_duration >= 0.4  # Allow some margin
    
    def test_context_manager(self):
        """Test scraper as context manager."""
        with ConcreteScraper(source_url='http://example.com') as scraper:
            assert scraper.session is not None
        
        # Session should be closed after context exit
        # (Can't easily test this without accessing private state)
    
    @patch('requests.Session.get')
    def test_run_success(self, mock_get):
        """Test run method executes workflow."""
        scraper = ConcreteScraper(source_url='http://example.com')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html></html>'
        mock_response.content = b'<html></html>'
        mock_get.return_value = mock_response
        
        results = scraper.run()
        
        assert len(results) > 0
        assert isinstance(results[0], ScrapedFuelPrice)
    
    @patch('requests.Session.get')
    def test_run_cleanup_called(self, mock_get):
        """Test cleanup is called after run."""
        scraper = ConcreteScraper(source_url='http://example.com')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html></html>'
        mock_response.content = b'<html></html>'
        mock_get.return_value = mock_response
        
        with patch.object(scraper, 'cleanup') as mock_cleanup:
            scraper.run()
            mock_cleanup.assert_called_once()
    
    @patch('requests.Session.get')
    def test_run_cleanup_on_error(self, mock_get):
        """Test cleanup is called even on error."""
        scraper = ConcreteScraper(source_url='http://example.com')
        mock_get.side_effect = requests.RequestException()
        
        with patch.object(scraper, 'cleanup') as mock_cleanup:
            with pytest.raises(HTTPException):
                scraper.run()
            mock_cleanup.assert_called_once()
    
    def test_cleanup_closes_session(self):
        """Test cleanup closes HTTP session."""
        scraper = ConcreteScraper(source_url='http://example.com')
        
        assert scraper.session is not None
        scraper.cleanup()
        # After cleanup, session should be closed
        # (Can't easily verify without accessing session state)
