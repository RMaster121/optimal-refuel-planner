"""Custom exceptions for the routes app."""


class InvalidGPXFileError(Exception):
    """Raised when GPX file is invalid or cannot be parsed."""
    pass


class GeocodingError(Exception):
    """Raised when country lookup fails."""
    pass


class RouteProcessingError(Exception):
    """Raised when route processing fails."""
    pass