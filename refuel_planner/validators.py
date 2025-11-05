"""Custom validators for the refuel planner application.

This module provides validation functions for common data types used throughout
the application, including decimal numbers, text inputs, and fuel prices.
All validators return error messages or None, making them easy to integrate
with Django's validation system and serializers.

Key Features:
    - Decimal and integer validation with configurable thresholds
    - Text sanitization to prevent XSS attacks
    - Location and name validation with whitelist approach
    - Fuel price range validation with reasonable defaults
    - ISO country code validation
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

import bleach
from django.core.validators import RegexValidator


def _validate_decimal_threshold(
    value: Any,
    field_name: str,
    min_value: Decimal,
    inclusive: bool,
    custom_error_msg: Optional[str] = None
) -> Optional[str]:
    """Base validator for decimal threshold checks.
    
    Internal helper function for validating decimal values against minimum
    thresholds. Supports both inclusive (>=) and exclusive (>) comparisons.
    
    Args:
        value: The value to validate (can be any type, will attempt conversion).
        field_name: Name of the field being validated, used in error messages.
        min_value: Minimum allowed value as a Decimal.
        inclusive: If True, uses >= comparison; if False, uses > comparison.
        custom_error_msg: Optional custom error message to override defaults.
    
    Returns:
        Error message string if validation fails, None if validation passes.
    
    Example:
        >>> _validate_decimal_threshold(5.5, "Price", Decimal('0'), False)
        None
        >>> _validate_decimal_threshold(-1, "Price", Decimal('0'), True)
        'Price cannot be negative.'
    """
    if value is None:
        return None
        
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, TypeError):
        return f"{field_name} must be a valid decimal number."
    
    if inclusive:
        if decimal_value < min_value:
            return custom_error_msg or f"{field_name} cannot be negative."
    else:
        if decimal_value <= min_value:
            return custom_error_msg or f"{field_name} must be greater than zero."
    
    return None


def validate_positive_decimal(
    value: Any,
    field_name: str,
    custom_error_msg: Optional[str] = None
) -> Optional[str]:
    """Validate that a value is a positive decimal (> 0).
    
    This validator checks that the input can be converted to a Decimal
    and that its value is strictly greater than zero. Used for validating
    fields like prices, consumption rates, and capacities where zero or
    negative values are not meaningful.
    
    Args:
        value: The value to validate (can be any type).
        field_name: Name of the field being validated, used in error messages.
        custom_error_msg: Optional custom error message for the positive check.
            If not provided, a default message will be used.
    
    Returns:
        Error message string if validation fails, None if valid.
    
    Example:
        >>> validate_positive_decimal(5.5, "Price")
        None
        >>> validate_positive_decimal(0, "Price")
        'Price must be greater than zero.'
        >>> validate_positive_decimal(-10, "Price")
        'Price must be greater than zero.'
        >>> validate_positive_decimal("abc", "Price")
        'Price must be a valid decimal number.'
    """
    return _validate_decimal_threshold(
        value, field_name, Decimal('0'), inclusive=False, custom_error_msg=custom_error_msg
    )


def validate_non_negative_decimal(
    value: Any,
    field_name: str,
    custom_error_msg: Optional[str] = None
) -> Optional[str]:
    """Validate that a value is a non-negative decimal (>= 0).
    
    This validator allows zero but rejects negative values. Used for fields
    where zero is a valid value but negative numbers are not, such as
    distances or optional monetary values.
    
    Args:
        value: The value to validate (can be any type).
        field_name: Name of the field being validated, used in error messages.
        custom_error_msg: Optional custom error message for non-negative check.
            If not provided, a default message will be used.
    
    Returns:
        Error message string if validation fails, None if valid.
    
    Example:
        >>> validate_non_negative_decimal(0, "Distance")
        None
        >>> validate_non_negative_decimal(10.5, "Distance")
        None
        >>> validate_non_negative_decimal(-5, "Distance")
        'Distance cannot be negative.'
    """
    return _validate_decimal_threshold(
        value, field_name, Decimal('0'), inclusive=True, custom_error_msg=custom_error_msg
    )


def _validate_integer_threshold(
    value: Any,
    field_name: str,
    min_value: int,
    custom_error_msg: Optional[str] = None
) -> Optional[str]:
    """Base validator for integer threshold checks.
    
    Internal helper function for validating integer values against minimum
    thresholds. Always uses inclusive comparison (>=).
    
    Args:
        value: The value to validate (must be an integer).
        field_name: Name of the field being validated, used in error messages.
        min_value: Minimum allowed value (inclusive).
        custom_error_msg: Optional custom error message to override defaults.
    
    Returns:
        Error message string if validation fails, None if validation passes.
    
    Example:
        >>> _validate_integer_threshold(5, "Count", 1)
        None
        >>> _validate_integer_threshold(0, "Count", 1)
        'Count must be at least 1.'
    """
    if value is None:
        return None
        
    if not isinstance(value, int):
        return f"{field_name} must be an integer."
    
    if value < min_value:
        if min_value == 0:
            return custom_error_msg or f"{field_name} cannot be negative."
        else:
            return custom_error_msg or f"{field_name} must be at least {min_value}."
    
    return None


def validate_positive_integer(
    value: Any,
    field_name: str,
    min_value: int = 1,
    custom_error_msg: Optional[str] = None
) -> Optional[str]:
    """Validate that a value is a positive integer.
    
    Ensures the value is an integer and at least equal to min_value.
    Useful for counts, IDs, or other fields requiring whole positive numbers.
    
    Args:
        value: The value to validate (must be an integer).
        field_name: Name of the field being validated, used in error messages.
        min_value: Minimum allowed value (default: 1).
        custom_error_msg: Optional custom error message.
    
    Returns:
        Error message string if validation fails, None if valid.
    
    Example:
        >>> validate_positive_integer(5, "Count")
        None
        >>> validate_positive_integer(0, "Count")
        'Count must be at least 1.'
        >>> validate_positive_integer(1.5, "Count")
        'Count must be an integer.'
    """
    return _validate_integer_threshold(value, field_name, min_value, custom_error_msg)


def validate_non_negative_integer(
    value: Any,
    field_name: str,
    custom_error_msg: Optional[str] = None
) -> Optional[str]:
    """Validate that a value is a non-negative integer (>= 0).
    
    Similar to validate_positive_integer but allows zero. Used for counts
    that can legitimately be zero, such as "number of optional items".
    
    Args:
        value: The value to validate (must be an integer).
        field_name: Name of the field being validated, used in error messages.
        custom_error_msg: Optional custom error message.
    
    Returns:
        Error message string if validation fails, None if valid.
    
    Example:
        >>> validate_non_negative_integer(0, "Optional Count")
        None
        >>> validate_non_negative_integer(10, "Optional Count")
        None
        >>> validate_non_negative_integer(-5, "Optional Count")
        'Optional Count cannot be negative.'
    """
    return _validate_integer_threshold(value, field_name, 0, custom_error_msg)


iso_country_code_validator = RegexValidator(
    regex=r'^[A-Z]{2}$',
    message='Country code must be exactly 2 uppercase letters (ISO 3166-1 alpha-2 format).',
    code='invalid_country_code'
)


def sanitize_text_input(
    value: str,
    field_name: str,
    max_length: Optional[int] = None,
    allow_tags: bool = False
) -> tuple[str, Optional[str]]:
    """Sanitize text input to prevent XSS attacks and malicious content.
    
    Uses the bleach library to strip dangerous HTML/JavaScript while optionally
    preserving safe formatting tags. Trims whitespace and enforces maximum
    length constraints. This is a critical security function used throughout
    the application for user-submitted text.
    
    Args:
        value: The text value to sanitize.
        field_name: Name of the field being sanitized, used in error messages.
        max_length: Optional maximum length to enforce.
        allow_tags: If True, allow safe HTML tags (b, i, u, em, strong).
            If False (default), strip all HTML tags.
    
    Returns:
        Tuple of (sanitized_value, error_message). The error_message is None
        if sanitization succeeded, or a string describing the problem.
    
    Example:
        >>> sanitize_text_input("  Hello  ", "Name")
        ('Hello', None)
        >>> sanitize_text_input("<script>alert('xss')</script>Hi", "Name")
        ('Hi', None)
        >>> sanitize_text_input("<b>Bold</b>", "Name", allow_tags=True)
        ('<b>Bold</b>', None)
        >>> sanitize_text_input("x" * 150, "Name", max_length=100)
        ('xxx...', 'Name exceeds maximum length of 100 characters.')
    """
    if not value:
        return value, None
    
    sanitized = value.strip()
    
    if allow_tags:
        allowed_tags = ['b', 'i', 'u', 'em', 'strong']
        allowed_attrs = {}
    else:
        allowed_tags = []
        allowed_attrs = {}
    
    sanitized = bleach.clean(
        sanitized,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True
    )
    
    if max_length and len(sanitized) > max_length:
        return sanitized, f"{field_name} exceeds maximum length of {max_length} characters."
    
    if not sanitized:
        return sanitized, f"{field_name} cannot be empty or contain only whitespace/tags."
    
    return sanitized, None


def validate_and_sanitize_name(
    value: str,
    field_name: str = "Name",
    max_length: int = 100
) -> tuple[str, Optional[str]]:
    """Validate and sanitize a name field.
    
    Performs strict validation on name fields by first checking for dangerous
    patterns (HTML tags, JavaScript), then sanitizing the input. Designed for
    user-facing names like car names, route names, etc.
    
    Args:
        value: The name value to validate and sanitize.
        field_name: Name of the field being validated (default: "Name").
        max_length: Maximum allowed length (default: 100 characters).
    
    Returns:
        Tuple of (sanitized_value, error_message). The error_message is None
        if validation passed, or a string describing the validation failure.
    
    Example:
        >>> validate_and_sanitize_name("Toyota Corolla", "Car Name")
        ('Toyota Corolla', None)
        >>> validate_and_sanitize_name("  Ford  ", "Car Name")
        ('Ford', None)
        >>> validate_and_sanitize_name("<script>bad</script>", "Car Name")
        ('<script>bad</script>', 'Car Name contains invalid characters or patterns.')
    """
    if value:
        dangerous_patterns = [
            r'[<>]',
            r'javascript:',
            r'on\w+\s*=',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return value.strip(), f"{field_name} contains invalid characters or patterns."
    
    sanitized, error = sanitize_text_input(value, field_name, max_length, allow_tags=False)
    
    if error:
        return sanitized, error
    
    return sanitized, None


def validate_and_sanitize_location(
    value: str,
    field_name: str = "Location",
    max_length: int = 200
) -> tuple[str, Optional[str]]:
    """Validate and sanitize a location field using whitelist approach.
    
    Uses a strict whitelist of allowed characters suitable for geographic
    locations: letters, numbers, spaces, commas, periods, hyphens, and
    parentheses. This covers most international location formats while
    preventing injection attacks.
    
    Args:
        value: The location value to validate and sanitize.
        field_name: Name of the field being validated (default: "Location").
        max_length: Maximum allowed length (default: 200 characters).
    
    Returns:
        Tuple of (sanitized_value, error_message). The error_message is None
        if validation passed, or a string describing the validation failure.
    
    Example:
        >>> validate_and_sanitize_location("Warsaw, Poland", "Start Point")
        ('Warsaw, Poland', None)
        >>> validate_and_sanitize_location("Berlin (Germany)", "End Point")
        ('Berlin (Germany)', None)
        >>> validate_and_sanitize_location("City <script>", "Location")
        ('City <script>', 'Location contains invalid characters. Only letters...')
    """
    if value:
        stripped = value.strip()
        if not re.match(r'^[\w\s,.\-()]+$', stripped, re.UNICODE):
            return stripped, f"{field_name} contains invalid characters. Only letters, numbers, spaces, commas, periods, hyphens, and parentheses are allowed."
    
    sanitized, error = sanitize_text_input(value, field_name, max_length, allow_tags=False)
    
    if error:
        return sanitized, error
    
    return sanitized, None


def validate_fuel_price_range(
    value: Any,
    field_name: str = "Fuel price",
    min_price: Decimal = Decimal('0.50'),
    max_price: Decimal = Decimal('3.00')
) -> Optional[str]:
    """Validate that a fuel price is within reasonable range.
    
    Ensures fuel prices are realistic to prevent data entry errors or
    malicious input. Default range (0.50-3.00 EUR) covers typical European
    fuel prices with some margin for extreme cases.
    
    Args:
        value: The price value to validate (can be any type).
        field_name: Name of the field being validated (default: "Fuel price").
        min_price: Minimum allowed price (default: 0.50 EUR).
        max_price: Maximum allowed price (default: 3.00 EUR).
    
    Returns:
        Error message string if validation fails, None if valid.
    
    Example:
        >>> validate_fuel_price_range(1.45, "Price")
        None
        >>> validate_fuel_price_range(0.30, "Price")
        'Price must be between 0.50 and 3.00 EUR.'
        >>> validate_fuel_price_range(5.00, "Price")
        'Price must be between 0.50 and 3.00 EUR.'
    """
    if value is None:
        return None
        
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, TypeError):
        return f"{field_name} must be a valid decimal number."
    
    if decimal_value < min_price or decimal_value > max_price:
        return f"{field_name} must be between {min_price} and {max_price} EUR."
    
    return None