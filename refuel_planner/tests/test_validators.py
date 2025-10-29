"""Comprehensive tests for refuel_planner/validators.py."""

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError

from refuel_planner.validators import (
    validate_positive_decimal,
    validate_non_negative_decimal,
    validate_positive_integer,
    validate_non_negative_integer,
    iso_country_code_validator,
    sanitize_text_input,
    validate_and_sanitize_name,
    validate_and_sanitize_location,
)


@pytest.mark.unit
class TestValidatePositiveDecimal:
    """Tests for validate_positive_decimal function."""

    def test_valid_positive_decimal(self):
        """Should return None for valid positive decimal."""
        assert validate_positive_decimal(Decimal('10.5'), 'Test') is None

    def test_valid_positive_integer(self):
        """Should return None for valid positive integer as decimal."""
        assert validate_positive_decimal(5, 'Test') is None

    def test_valid_positive_string_number(self):
        """Should return None for valid positive string number."""
        assert validate_positive_decimal('3.14', 'Test') is None

    def test_valid_positive_float(self):
        """Should return None for valid positive float."""
        assert validate_positive_decimal(2.5, 'Test') is None

    def test_zero_value(self):
        """Should return error for zero value."""
        error = validate_positive_decimal(0, 'Amount')
        assert error is not None
        assert 'greater than zero' in error

    def test_negative_decimal(self):
        """Should return error for negative decimal."""
        error = validate_positive_decimal(Decimal('-5.5'), 'Price')
        assert error is not None
        assert 'greater than zero' in error

    def test_negative_integer(self):
        """Should return error for negative integer."""
        error = validate_positive_decimal(-10, 'Value')
        assert error is not None
        assert 'greater than zero' in error

    def test_none_value(self):
        """Should return None for None value (allows null)."""
        assert validate_positive_decimal(None, 'Test') is None

    def test_invalid_string(self):
        """Should return error for invalid string."""
        error = validate_positive_decimal('not a number', 'Field')
        assert error is not None
        assert 'valid decimal number' in error

    def test_invalid_type(self):
        """Should return error for invalid type."""
        error = validate_positive_decimal({'key': 'value'}, 'Field')
        assert error is not None
        assert 'valid decimal number' in error

    def test_custom_error_message(self):
        """Should use custom error message when provided."""
        error = validate_positive_decimal(0, 'Amount', 'Custom error')
        assert error == 'Custom error'

    def test_field_name_in_error(self):
        """Should include field name in error message."""
        error = validate_positive_decimal(-1, 'Tank Capacity')
        assert 'Tank Capacity' in error


@pytest.mark.unit
class TestValidateNonNegativeDecimal:
    """Tests for validate_non_negative_decimal function."""

    def test_valid_positive_decimal(self):
        """Should return None for valid positive decimal."""
        assert validate_non_negative_decimal(Decimal('10.5'), 'Test') is None

    def test_valid_zero_value(self):
        """Should return None for zero (non-negative)."""
        assert validate_non_negative_decimal(0, 'Test') is None
        assert validate_non_negative_decimal(Decimal('0'), 'Test') is None

    def test_valid_positive_string(self):
        """Should return None for valid positive string number."""
        assert validate_non_negative_decimal('15.25', 'Test') is None

    def test_negative_decimal(self):
        """Should return error for negative decimal."""
        error = validate_non_negative_decimal(Decimal('-5.5'), 'Cost')
        assert error is not None
        assert 'cannot be negative' in error

    def test_negative_integer(self):
        """Should return error for negative integer."""
        error = validate_non_negative_decimal(-1, 'Value')
        assert error is not None
        assert 'cannot be negative' in error

    def test_none_value(self):
        """Should return None for None value."""
        assert validate_non_negative_decimal(None, 'Test') is None

    def test_invalid_string(self):
        """Should return error for invalid string."""
        error = validate_non_negative_decimal('invalid', 'Field')
        assert error is not None
        assert 'valid decimal number' in error

    def test_custom_error_message(self):
        """Should use custom error message when provided."""
        error = validate_non_negative_decimal(-1, 'Amount', 'Custom error')
        assert error == 'Custom error'

    def test_field_name_in_error(self):
        """Should include field name in error message."""
        error = validate_non_negative_decimal(-5, 'Distance')
        assert 'Distance' in error


@pytest.mark.unit
class TestValidatePositiveInteger:
    """Tests for validate_positive_integer function."""

    def test_valid_positive_integer(self):
        """Should return None for valid positive integer."""
        assert validate_positive_integer(5, 'Test') is None

    def test_valid_positive_integer_min_value_1(self):
        """Should return None for integer >= 1 (default min_value)."""
        assert validate_positive_integer(1, 'Test') is None
        assert validate_positive_integer(100, 'Test') is None

    def test_zero_value_default_min(self):
        """Should return error for zero with default min_value=1."""
        error = validate_positive_integer(0, 'Count')
        assert error is not None
        assert 'at least 1' in error

    def test_negative_integer(self):
        """Should return error for negative integer."""
        error = validate_positive_integer(-5, 'Number')
        assert error is not None
        assert 'at least 1' in error

    def test_custom_min_value(self):
        """Should validate against custom min_value."""
        assert validate_positive_integer(10, 'Test', min_value=10) is None
        error = validate_positive_integer(9, 'Test', min_value=10)
        assert error is not None
        assert 'at least 10' in error

    def test_custom_min_value_zero(self):
        """Should accept zero when min_value=0."""
        assert validate_positive_integer(0, 'Test', min_value=0) is None

    def test_none_value(self):
        """Should return None for None value."""
        assert validate_positive_integer(None, 'Test') is None

    def test_float_value(self):
        """Should return error for float value."""
        error = validate_positive_integer(5.5, 'Count')
        assert error is not None
        assert 'integer' in error

    def test_string_value(self):
        """Should return error for string value."""
        error = validate_positive_integer('5', 'Count')
        assert error is not None
        assert 'integer' in error

    def test_custom_error_message(self):
        """Should use custom error message when provided."""
        error = validate_positive_integer(0, 'Amount', custom_error_msg='Custom error')
        assert error == 'Custom error'

    def test_field_name_in_error(self):
        """Should include field name in error message."""
        error = validate_positive_integer(0, 'Stop Number')
        assert 'Stop Number' in error


@pytest.mark.unit
class TestValidateNonNegativeInteger:
    """Tests for validate_non_negative_integer function."""

    def test_valid_positive_integer(self):
        """Should return None for valid positive integer."""
        assert validate_non_negative_integer(10, 'Test') is None

    def test_valid_zero_value(self):
        """Should return None for zero (non-negative)."""
        assert validate_non_negative_integer(0, 'Test') is None

    def test_negative_integer(self):
        """Should return error for negative integer."""
        error = validate_non_negative_integer(-1, 'Count')
        assert error is not None
        assert 'cannot be negative' in error

    def test_none_value(self):
        """Should return None for None value."""
        assert validate_non_negative_integer(None, 'Test') is None

    def test_float_value(self):
        """Should return error for float value."""
        error = validate_non_negative_integer(5.5, 'Count')
        assert error is not None
        assert 'integer' in error

    def test_string_value(self):
        """Should return error for string value."""
        error = validate_non_negative_integer('10', 'Count')
        assert error is not None
        assert 'integer' in error

    def test_custom_error_message(self):
        """Should use custom error message when provided."""
        error = validate_non_negative_integer(-1, 'Amount', 'Custom error')
        assert error == 'Custom error'

    def test_field_name_in_error(self):
        """Should include field name in error message."""
        error = validate_non_negative_integer(-5, 'Reservoir')
        assert 'Reservoir' in error


@pytest.mark.unit
class TestIsoCountryCodeValidator:
    """Tests for iso_country_code_validator."""

    def test_valid_country_codes(self):
        """Should not raise for valid 2-letter uppercase codes."""
        iso_country_code_validator('PL')
        iso_country_code_validator('DE')
        iso_country_code_validator('US')
        iso_country_code_validator('GB')

    def test_lowercase_code(self):
        """Should raise ValidationError for lowercase code."""
        with pytest.raises(ValidationError) as exc_info:
            iso_country_code_validator('pl')
        assert 'uppercase' in str(exc_info.value).lower()

    def test_mixed_case_code(self):
        """Should raise ValidationError for mixed case code."""
        with pytest.raises(ValidationError):
            iso_country_code_validator('Pl')

    def test_too_short_code(self):
        """Should raise ValidationError for single letter code."""
        with pytest.raises(ValidationError):
            iso_country_code_validator('P')

    def test_too_long_code(self):
        """Should raise ValidationError for three letter code."""
        with pytest.raises(ValidationError):
            iso_country_code_validator('POL')

    def test_numeric_code(self):
        """Should raise ValidationError for numeric code."""
        with pytest.raises(ValidationError):
            iso_country_code_validator('12')

    def test_special_characters(self):
        """Should raise ValidationError for special characters."""
        with pytest.raises(ValidationError):
            iso_country_code_validator('P-')

    def test_empty_string(self):
        """Should raise ValidationError for empty string."""
        with pytest.raises(ValidationError):
            iso_country_code_validator('')


@pytest.mark.unit
class TestSanitizeTextInput:
    """Tests for sanitize_text_input function."""

    def test_simple_text(self):
        """Should return same text for simple input."""
        sanitized, error = sanitize_text_input('Hello World', 'Test')
        assert sanitized == 'Hello World'
        assert error is None

    def test_strips_whitespace(self):
        """Should strip leading/trailing whitespace."""
        sanitized, error = sanitize_text_input('  Hello World  ', 'Test')
        assert sanitized == 'Hello World'
        assert error is None

    def test_removes_html_tags_by_default(self):
        """Should remove HTML tags by default."""
        sanitized, error = sanitize_text_input('Hello <script>alert("XSS")</script>World', 'Test')
        assert '<script>' not in sanitized
        assert 'Hello' in sanitized
        assert 'World' in sanitized

    def test_removes_dangerous_tags(self):
        """Should remove dangerous HTML tags."""
        sanitized, error = sanitize_text_input('<img src=x onerror=alert(1)>', 'Test')
        assert '<img' not in sanitized
        assert 'onerror' not in sanitized

    def test_allows_safe_tags_when_enabled(self):
        """Should allow safe HTML tags when allow_tags=True."""
        sanitized, error = sanitize_text_input('Hello <b>World</b>', 'Test', allow_tags=True)
        assert '<b>World</b>' in sanitized
        assert error is None

    def test_removes_unsafe_tags_even_when_allowed(self):
        """Should remove unsafe tags even when allow_tags=True."""
        sanitized, error = sanitize_text_input('Hello <script>bad</script> <b>good</b>', 'Test', allow_tags=True)
        assert '<script>' not in sanitized
        assert '<b>good</b>' in sanitized

    def test_max_length_validation(self):
        """Should return error when exceeding max_length."""
        long_text = 'A' * 100
        sanitized, error = sanitize_text_input(long_text, 'Test', max_length=50)
        assert error is not None
        assert 'exceeds maximum length' in error
        assert '50' in error

    def test_max_length_exact(self):
        """Should accept text exactly at max_length."""
        text = 'A' * 50
        sanitized, error = sanitize_text_input(text, 'Test', max_length=50)
        assert error is None

    def test_empty_string(self):
        """Should return empty string without error for empty input."""
        sanitized, error = sanitize_text_input('', 'Test')
        assert sanitized == ''
        assert error is None

    def test_whitespace_only(self):
        """Should return error for whitespace-only input."""
        sanitized, error = sanitize_text_input('   ', 'Test')
        assert error is not None
        assert 'cannot be empty' in error

    def test_tags_only(self):
        """Should return error for tags-only input."""
        sanitized, error = sanitize_text_input('<div></div>', 'Test')
        assert error is not None
        assert 'cannot be empty' in error

    def test_none_value(self):
        """Should return None value as-is."""
        sanitized, error = sanitize_text_input(None, 'Test')
        assert sanitized is None
        assert error is None

    def test_field_name_in_error(self):
        """Should include field name in error messages."""
        _, error = sanitize_text_input('A' * 100, 'Description', max_length=50)
        assert 'Description' in error


@pytest.mark.unit
class TestValidateAndSanitizeName:
    """Tests for validate_and_sanitize_name function."""

    def test_valid_simple_name(self):
        """Should accept valid simple name."""
        sanitized, error = validate_and_sanitize_name('John Doe', 'Name')
        assert sanitized == 'John Doe'
        assert error is None

    def test_valid_name_with_numbers(self):
        """Should accept name with numbers."""
        sanitized, error = validate_and_sanitize_name('Toyota Corolla 2020', 'Car Name')
        assert sanitized == 'Toyota Corolla 2020'
        assert error is None

    def test_strips_whitespace(self):
        """Should strip whitespace."""
        sanitized, error = validate_and_sanitize_name('  John Doe  ', 'Name')
        assert sanitized == 'John Doe'
        assert error is None

    def test_rejects_script_tag(self):
        """Should reject <script> tag."""
        sanitized, error = validate_and_sanitize_name('<script>alert(1)</script>', 'Name')
        assert error is not None
        assert 'invalid characters' in error

    def test_rejects_angle_brackets(self):
        """Should reject angle brackets."""
        sanitized, error = validate_and_sanitize_name('Name<test>', 'Name')
        assert error is not None
        assert 'invalid characters' in error

    def test_rejects_javascript_protocol(self):
        """Should reject javascript: protocol."""
        sanitized, error = validate_and_sanitize_name('javascript:alert(1)', 'Name')
        assert error is not None
        assert 'invalid characters' in error

    def test_rejects_event_handler(self):
        """Should reject event handlers like onclick."""
        sanitized, error = validate_and_sanitize_name('name onclick=alert(1)', 'Name')
        assert error is not None
        assert 'invalid characters' in error

    def test_case_insensitive_javascript_check(self):
        """Should detect JavaScript in any case."""
        sanitized, error = validate_and_sanitize_name('JaVaScRiPt:alert(1)', 'Name')
        assert error is not None

    def test_max_length_validation(self):
        """Should validate max_length."""
        long_name = 'A' * 150
        sanitized, error = validate_and_sanitize_name(long_name, 'Name', max_length=100)
        assert error is not None
        assert 'exceeds maximum length' in error

    def test_unicode_characters(self):
        """Should accept unicode characters."""
        sanitized, error = validate_and_sanitize_name('Łódź Vehicle', 'Name')
        assert error is None
        assert 'Łódź' in sanitized

    def test_default_field_name(self):
        """Should use default field name."""
        _, error = validate_and_sanitize_name('<script>', )
        assert 'Name' in error

    def test_field_name_in_error(self):
        """Should include custom field name in error."""
        _, error = validate_and_sanitize_name('<script>', 'Vehicle Name')
        assert 'Vehicle Name' in error


@pytest.mark.unit
class TestValidateAndSanitizeLocation:
    """Tests for validate_and_sanitize_location function."""

    def test_valid_simple_location(self):
        """Should accept valid simple location."""
        sanitized, error = validate_and_sanitize_location('Warsaw, Poland', 'Location')
        assert sanitized == 'Warsaw, Poland'
        assert error is None

    def test_valid_location_with_numbers(self):
        """Should accept location with numbers."""
        sanitized, error = validate_and_sanitize_location('Route 66', 'Location')
        assert sanitized == 'Route 66'
        assert error is None

    def test_valid_location_with_parentheses(self):
        """Should accept location with parentheses."""
        sanitized, error = validate_and_sanitize_location('Berlin (Germany)', 'Location')
        assert sanitized == 'Berlin (Germany)'
        assert error is None

    def test_valid_location_with_periods(self):
        """Should accept location with periods."""
        sanitized, error = validate_and_sanitize_location('St. Petersburg', 'Location')
        assert sanitized == 'St. Petersburg'
        assert error is None

    def test_valid_location_with_hyphens(self):
        """Should accept location with hyphens."""
        sanitized, error = validate_and_sanitize_location('Saint-Petersburg', 'Location')
        assert sanitized == 'Saint-Petersburg'
        assert error is None

    def test_strips_whitespace(self):
        """Should strip whitespace."""
        sanitized, error = validate_and_sanitize_location('  Warsaw  ', 'Location')
        assert sanitized == 'Warsaw'
        assert error is None

    def test_rejects_special_characters(self):
        """Should reject special characters not in whitelist."""
        sanitized, error = validate_and_sanitize_location('Location@#$', 'Location')
        assert error is not None
        assert 'invalid characters' in error

    def test_rejects_html_tags(self):
        """Should reject HTML tags."""
        sanitized, error = validate_and_sanitize_location('<script>alert(1)</script>', 'Location')
        assert error is not None
        assert 'invalid characters' in error

    def test_max_length_validation(self):
        """Should validate max_length."""
        long_location = 'A' * 250
        sanitized, error = validate_and_sanitize_location(long_location, 'Location', max_length=200)
        assert error is not None
        assert 'exceeds maximum length' in error

    def test_unicode_characters(self):
        """Should accept unicode characters."""
        sanitized, error = validate_and_sanitize_location('Łódź, Polska', 'Location')
        assert error is None
        assert 'Łódź' in sanitized

    def test_default_field_name(self):
        """Should use default field name."""
        _, error = validate_and_sanitize_location('Invalid@Location')
        assert 'Location' in error

    def test_allowed_characters_list(self):
        """Should accept all whitelisted characters."""
        valid = 'ABCabc123 ,.-()'
        sanitized, error = validate_and_sanitize_location(valid, 'Location')
        assert error is None
        assert sanitized == valid