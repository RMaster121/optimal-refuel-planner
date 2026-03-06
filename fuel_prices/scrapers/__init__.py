"""
Fuel Price Scraper Package

This package provides infrastructure for scraping fuel price data from external sources.

Key Components:
- BaseScraper: Abstract base class for all scrapers
- HTMLTableScraper: Concrete scraper for HTML tables
- CountryMapper: Maps country names to ISO codes
- FuelPriceValidator: Validates scraped data
- FuelPriceLoader: Loads data into database
- ScraperManager: Orchestrates complete workflow
- ScraperConfig: Configuration management
- Custom exceptions for error handling
"""

from .base import BaseScraper, ScrapedFuelPrice
from .config import ScraperConfig
from .html_table_scraper import HTMLTableScraper
from .country_mapper import CountryMapper
from .validators import FuelPriceValidator
from .data_loader import FuelPriceLoader
from .manager import ScraperManager
from .exceptions import (
    ScraperException,
    HTTPException,
    ParsingException,
    ValidationException,
    RateLimitException,
)

__all__ = [
    'BaseScraper',
    'ScrapedFuelPrice',
    'ScraperConfig',
    'HTMLTableScraper',
    'CountryMapper',
    'FuelPriceValidator',
    'FuelPriceLoader',
    'ScraperManager',
    'ScraperException',
    'HTTPException',
    'ParsingException',
    'ValidationException',
    'RateLimitException',
]