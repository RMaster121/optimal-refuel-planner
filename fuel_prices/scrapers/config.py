"""
Configuration management for fuel price scrapers.

This module provides centralized configuration for scraper behavior,
loading settings from environment variables with sensible defaults.
"""

import os
from typing import Optional
from decimal import Decimal


class ScraperConfig:
    """
    Configuration manager for fuel price scrapers.
    
    Loads settings from environment variables with fallback to sensible defaults.
    Provides validation to ensure configuration values are within acceptable ranges.
    
    Environment Variables:
    - FUEL_SCRAPER_TIMEOUT: HTTP request timeout in seconds (default: 30)
    - FUEL_SCRAPER_MAX_RETRIES: Maximum number of retry attempts (default: 3)
    - FUEL_SCRAPER_BACKOFF_FACTOR: Exponential backoff factor (default: 0.5)
    - FUEL_SCRAPER_RATE_LIMIT: Requests per second (default: 1.0)
    - FUEL_SCRAPER_USER_AGENT: Custom user agent string
    """
    
    # Default values
    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_FACTOR = 0.5
    DEFAULT_RATE_LIMIT = 1.0
    DEFAULT_USER_AGENT = 'OptimalRefuelPlanner/1.0 (Fuel Price Scraper)'
    
    # Validation constraints
    MIN_TIMEOUT = 5
    MAX_TIMEOUT = 300
    MIN_RETRIES = 0
    MAX_RETRIES = 10
    MIN_BACKOFF = 0.1
    MAX_BACKOFF = 5.0
    MIN_RATE_LIMIT = 0.1
    MAX_RATE_LIMIT = 10.0
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self._timeout = self._load_int('FUEL_SCRAPER_TIMEOUT', self.DEFAULT_TIMEOUT)
        self._max_retries = self._load_int('FUEL_SCRAPER_MAX_RETRIES', self.DEFAULT_MAX_RETRIES)
        self._backoff_factor = self._load_float('FUEL_SCRAPER_BACKOFF_FACTOR', self.DEFAULT_BACKOFF_FACTOR)
        self._rate_limit = self._load_float('FUEL_SCRAPER_RATE_LIMIT', self.DEFAULT_RATE_LIMIT)
        self._user_agent = self._load_str('FUEL_SCRAPER_USER_AGENT', self.DEFAULT_USER_AGENT)
        
        self._validate()
    
    @property
    def timeout(self) -> int:
        """HTTP request timeout in seconds."""
        return self._timeout
    
    @property
    def max_retries(self) -> int:
        """Maximum number of retry attempts for failed requests."""
        return self._max_retries
    
    @property
    def backoff_factor(self) -> float:
        """Exponential backoff factor for retries."""
        return self._backoff_factor
    
    @property
    def rate_limit(self) -> float:
        """Maximum requests per second."""
        return self._rate_limit
    
    @property
    def user_agent(self) -> str:
        """User agent string for HTTP requests."""
        return self._user_agent
    
    def _load_int(self, key: str, default: int) -> int:
        """
        Load integer value from environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not set
            
        Returns:
            Integer value from environment or default
        """
        value = os.environ.get(key)
        if value is None:
            return default
        
        try:
            return int(value)
        except ValueError:
            return default
    
    def _load_float(self, key: str, default: float) -> float:
        """
        Load float value from environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not set
            
        Returns:
            Float value from environment or default
        """
        value = os.environ.get(key)
        if value is None:
            return default
        
        try:
            return float(value)
        except ValueError:
            return default
    
    def _load_str(self, key: str, default: str) -> str:
        """
        Load string value from environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not set
            
        Returns:
            String value from environment or default
        """
        return os.environ.get(key, default)
    
    def _validate(self):
        """
        Validate configuration values are within acceptable ranges.
        
        Raises:
            ValueError: If any configuration value is invalid
        """
        if not (self.MIN_TIMEOUT <= self._timeout <= self.MAX_TIMEOUT):
            raise ValueError(
                f"Timeout must be between {self.MIN_TIMEOUT} and {self.MAX_TIMEOUT} seconds, "
                f"got {self._timeout}"
            )
        
        if not (self.MIN_RETRIES <= self._max_retries <= self.MAX_RETRIES):
            raise ValueError(
                f"Max retries must be between {self.MIN_RETRIES} and {self.MAX_RETRIES}, "
                f"got {self._max_retries}"
            )
        
        if not (self.MIN_BACKOFF <= self._backoff_factor <= self.MAX_BACKOFF):
            raise ValueError(
                f"Backoff factor must be between {self.MIN_BACKOFF} and {self.MAX_BACKOFF}, "
                f"got {self._backoff_factor}"
            )
        
        if not (self.MIN_RATE_LIMIT <= self._rate_limit <= self.MAX_RATE_LIMIT):
            raise ValueError(
                f"Rate limit must be between {self.MIN_RATE_LIMIT} and {self.MAX_RATE_LIMIT} req/sec, "
                f"got {self._rate_limit}"
            )
        
        if not self._user_agent or not self._user_agent.strip():
            raise ValueError("User agent cannot be empty")
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"ScraperConfig(timeout={self.timeout}, max_retries={self.max_retries}, "
            f"backoff_factor={self.backoff_factor}, rate_limit={self.rate_limit})"
        )