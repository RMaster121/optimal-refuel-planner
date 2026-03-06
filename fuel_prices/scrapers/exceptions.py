"""
Custom exceptions for the fuel price scraper system.

This module defines a hierarchy of exceptions used throughout the scraper system
to provide clear error handling and logging.
"""


class ScraperException(Exception):
    """
    Base exception for all scraper-related errors.
    
    All custom exceptions in the scraper system inherit from this base class,
    allowing for catch-all exception handling when needed.
    """
    pass


class HTTPException(ScraperException):
    """
    Raised when HTTP request operations fail.
    
    Examples:
    - Connection timeouts
    - HTTP error status codes (4xx, 5xx)
    - Network connectivity issues
    - SSL/TLS errors
    """
    pass


class ParsingException(ScraperException):
    """
    Raised when HTML or data parsing fails.
    
    Examples:
    - Invalid HTML structure
    - Missing expected elements
    - Malformed data format
    - Unexpected content structure
    """
    pass


class ValidationException(ScraperException):
    """
    Raised when scraped data fails validation checks.
    
    Examples:
    - Invalid country codes
    - Price values out of acceptable range
    - Missing required fields
    - Invalid fuel type values
    """
    pass


class RateLimitException(ScraperException):
    """
    Raised when rate limiting thresholds are exceeded.
    
    Examples:
    - Too many requests in a given time period
    - HTTP 429 (Too Many Requests) responses
    - Server-imposed rate limits
    """
    pass