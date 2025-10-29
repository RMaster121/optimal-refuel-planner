"""Custom validators for the refuel planner application."""

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
    """
    Base validator for decimal threshold checks.
    
    :param value: The value to validate
    :param field_name: Name of the field being validated
    :param min_value: Minimum allowed value
    :param inclusive: Whether min_value is inclusive (>=) or exclusive (>)
    :param custom_error_msg: Optional custom error message
    :return: Error message if validation fails, None otherwise
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
    """
    Validate that a value is a positive decimal (> 0).
    
    :param value: The value to validate
    :param field_name: Name of the field being validated (for error messages)
    :param custom_error_msg: Optional custom error message for positive check
    :return: Error message if validation fails, None otherwise
    """
    return _validate_decimal_threshold(
        value, field_name, Decimal('0'), inclusive=False, custom_error_msg=custom_error_msg
    )


def validate_non_negative_decimal(
    value: Any,
    field_name: str,
    custom_error_msg: Optional[str] = None
) -> Optional[str]:
    """
    Validate that a value is a non-negative decimal (>= 0).
    
    :param value: The value to validate
    :param field_name: Name of the field being validated (for error messages)
    :param custom_error_msg: Optional custom error message for non-negative check
    :return: Error message if validation fails, None otherwise
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
    """
    Base validator for integer threshold checks.
    
    :param value: The value to validate
    :param field_name: Name of the field being validated
    :param min_value: Minimum allowed value (inclusive)
    :param custom_error_msg: Optional custom error message
    :return: Error message if validation fails, None otherwise
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
    """
    Validate that a value is a positive integer.
    
    :param value: The value to validate
    :param field_name: Name of the field being validated (for error messages)
    :param min_value: Minimum allowed value (default: 1)
    :param custom_error_msg: Optional custom error message
    :return: Error message if validation fails, None otherwise
    """
    return _validate_integer_threshold(value, field_name, min_value, custom_error_msg)


def validate_non_negative_integer(
    value: Any,
    field_name: str,
    custom_error_msg: Optional[str] = None
) -> Optional[str]:
    """
    Validate that a value is a non-negative integer (>= 0).
    
    :param value: The value to validate
    :param field_name: Name of the field being validated (for error messages)
    :param custom_error_msg: Optional custom error message
    :return: Error message if validation fails, None otherwise
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
    """
    Sanitize text input to prevent XSS attacks and malicious content.
    
    :param value: The text value to sanitize
    :param field_name: Name of the field being sanitized
    :param max_length: Optional maximum length to enforce
    :param allow_tags: Whether to allow safe HTML tags (default: False)
    :return: Tuple of (sanitized_value, error_message)
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
    """
    Validate and sanitize a name field.
    
    :param value: The name value to validate and sanitize
    :param field_name: Name of the field being validated
    :param max_length: Maximum allowed length
    :return: Tuple of (sanitized_value, error_message)
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
    """
    Validate and sanitize a location field using whitelist approach.
    
    :param value: The location value to validate and sanitize
    :param field_name: Name of the field being validated
    :param max_length: Maximum allowed length
    :return: Tuple of (sanitized_value, error_message)
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
    """
    Validate that a fuel price is within reasonable range.
    
    :param value: The price value to validate
    :param field_name: Name of the field being validated
    :param min_price: Minimum allowed price (default: 0.50 EUR)
    :param max_price: Maximum allowed price (default: 3.00 EUR)
    :return: Error message if validation fails, None otherwise
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