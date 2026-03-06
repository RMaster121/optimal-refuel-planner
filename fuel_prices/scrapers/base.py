"""
Abstract base class for all fuel price scrapers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import logging
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import HTTPException, ScraperException
from .config import ScraperConfig


@dataclass
class ScrapedFuelPrice:
    """
    Data transfer object for scraped fuel price data.
    
    Attributes:
        country_name: Human-readable country name (e.g., "Poland")
        country_code: ISO 3166-1 alpha-2 code (e.g., "PL") - may be None if unmapped
        fuel_type: Fuel type string ("gasoline" or "diesel")
        price_eur: Price per liter in EUR (Decimal-compatible) - None for missing data
        scraped_at: Timestamp when data was collected
        source_url: URL where data was scraped from
    """
    country_name: str
    country_code: Optional[str]
    fuel_type: str
    price_eur: Optional[float]
    scraped_at: datetime
    source_url: str


class BaseScraper(ABC):
    """
    Abstract base class for all fuel price scrapers.
    
    Subclasses must implement:
    - scrape(): Main scraping logic
    - validate_response(): Response validation
    - parse_response(): Raw data parsing
    
    Example:
        class MyCustomScraper(BaseScraper):
            def scrape(self) -> List[ScrapedFuelPrice]:
                raw_data = self.fetch()
                return self.parse_response(raw_data)
            
            def validate_response(self, response: requests.Response) -> bool:
                return response.status_code == 200
            
            def parse_response(self, response: requests.Response) -> List[ScrapedFuelPrice]:
                # Parse response and return list of ScrapedFuelPrice objects
                pass
    """
    
    def __init__(
        self,
        source_url: str,
        config: Optional[ScraperConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize base scraper.
        
        Args:
            source_url: URL to scrape data from
            config: Optional ScraperConfig instance. If None, uses default configuration
            logger: Optional logger instance. If None, creates logger for this class
        """
        self.source_url = source_url
        self.config = config or ScraperConfig()
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        self.session = self._create_session()
        self._last_request_time = 0.0
    
    def _create_session(self) -> requests.Session:
        """
        Create HTTP session with retry logic and connection pooling.
        
        Configures:
        - Retry strategy for transient failures (429, 500-504)
        - Connection pooling for efficiency
        - Default headers including User-Agent
        
        Returns:
            Configured requests.Session with retry adapter
        """
        session = requests.Session()
        
        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            raise_on_status=False
        )
        
        # Apply retry adapter to both HTTP and HTTPS
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        return session
    
    def _enforce_rate_limit(self):
        """
        Enforce rate limiting by adding delays between requests.
        
        Calculates the time since the last request and sleeps if necessary
        to maintain the configured rate limit (requests per second).
        """
        if self.config.rate_limit <= 0:
            return
        
        min_interval = 1.0 / self.config.rate_limit
        time_since_last = time.time() - self._last_request_time
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def fetch(self) -> requests.Response:
        """
        Fetch data from source URL with error handling and rate limiting.
        
        This method:
        1. Enforces rate limiting
        2. Makes HTTP GET request
        3. Validates response
        4. Handles errors with detailed logging
        
        Returns:
            Response object from the source URL
            
        Raises:
            HTTPException: On HTTP errors, timeouts, or invalid responses
        """
        try:
            self._enforce_rate_limit()
            
            self.logger.info(f"Fetching data from {self.source_url}")
            response = self.session.get(
                self.source_url,
                timeout=self.config.timeout
            )
            
            # Check HTTP status
            response.raise_for_status()
            
            # Validate response
            if not self.validate_response(response):
                raise HTTPException(
                    f"Response validation failed for {self.source_url}"
                )
            
            self.logger.info(
                f"Successfully fetched data from {self.source_url} "
                f"(status: {response.status_code}, size: {len(response.content)} bytes)"
            )
            return response
            
        except requests.Timeout as e:
            self.logger.error(f"Request timeout for {self.source_url}: {e}")
            raise HTTPException(f"Request timeout: {e}") from e
        
        except requests.ConnectionError as e:
            self.logger.error(f"Connection error for {self.source_url}: {e}")
            raise HTTPException(f"Connection error: {e}") from e
        
        except requests.HTTPError as e:
            self.logger.error(
                f"HTTP error for {self.source_url}: {e.response.status_code}"
            )
            raise HTTPException(
                f"HTTP {e.response.status_code}: {e.response.reason}"
            ) from e
        
        except requests.RequestException as e:
            self.logger.error(f"Request failed for {self.source_url}: {e}")
            raise HTTPException(f"Request failed: {e}") from e
    
    @abstractmethod
    def scrape(self) -> List[ScrapedFuelPrice]:
        """
        Main scraping method to be implemented by subclasses.
        
        This method should:
        1. Fetch data using self.fetch()
        2. Parse the response using self.parse_response()
        3. Return list of ScrapedFuelPrice objects
        
        Returns:
            List of ScrapedFuelPrice objects
            
        Raises:
            ScraperException: On scraping failures
        """
        pass
    
    @abstractmethod
    def validate_response(self, response: requests.Response) -> bool:
        """
        Validate HTTP response before parsing.
        
        Subclasses should implement validation logic specific to their
        data source, such as:
        - Checking response status code
        - Verifying content type
        - Checking for expected markers in content
        
        Args:
            response: HTTP response object
            
        Returns:
            True if response is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: requests.Response) -> List[ScrapedFuelPrice]:
        """
        Parse HTTP response into structured data.
        
        Subclasses must implement parsing logic to extract fuel prices
        from the response content and transform them into ScrapedFuelPrice objects.
        
        Args:
            response: HTTP response object with content to parse
            
        Returns:
            List of ScrapedFuelPrice objects
            
        Raises:
            ParsingException: On parsing failures
        """
        pass
    
    def run(self) -> List[ScrapedFuelPrice]:
        """
        Execute the complete scraping workflow.
        
        This method orchestrates the scraping process:
        1. Log start of scraping
        2. Execute scrape() method
        3. Log results
        4. Handle errors
        5. Clean up resources
        
        Returns:
            List of successfully scraped fuel prices
            
        Raises:
            ScraperException: On scraping failures
        """
        self.logger.info(f"Starting scraper: {self.__class__.__name__}")
        
        try:
            results = self.scrape()
            self.logger.info(
                f"Scraping completed successfully. Found {len(results)} fuel price records."
            )
            return results
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}", exc_info=True)
            raise
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """
        Clean up resources (e.g., close HTTP session).
        
        This method is called automatically after scraping completes or fails.
        Subclasses can override to add additional cleanup logic.
        """
        if self.session:
            self.session.close()
            self.logger.debug("HTTP session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.cleanup()
        return False