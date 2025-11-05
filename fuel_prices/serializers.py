"""Serializers for fuel price data transformation and validation.

This module provides REST Framework serializers for the fuel_prices app,
handling data transformation between API requests/responses and Django models.
It includes comprehensive validation for fuel price data, country codes, and
fuel types.

The serializers support denormalized read operations (including country code
and name) while accepting minimal write data (just country code), improving
API usability while maintaining data integrity.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from fuel_prices.models import Country, FuelPrice
from refuel_planner.choices import FuelType
from refuel_planner.validators import (
    validate_positive_decimal,
    validate_fuel_price_range,
    iso_country_code_validator,
)


class FuelPriceSerializer(serializers.ModelSerializer):
    """Serializer for FuelPrice model with comprehensive validation.
    
    Handles serialization and deserialization of fuel price data with
    automatic validation of country codes, fuel types, and price ranges.
    Provides denormalized country information in read operations for
    improved API usability.
    
    Country codes are automatically normalized to uppercase and validated
    against ISO 3166-1 alpha-2 standards. Prices are validated to be
    positive and within reasonable ranges (0.50-3.00 EUR).
    
    If scraped_at timestamp is not provided during creation, it is
    automatically set to the current time.
    
    Read Fields:
        - id: Primary key (integer)
        - country_code: Two-letter ISO country code (string)
        - country_name: Human-readable country name (string)
        - fuel_type: Type of fuel - 'gasoline' or 'diesel' (string)
        - price_per_liter: Price per liter in EUR (decimal, 3 places)
        - scraped_at: Timestamp of price collection (datetime)
    
    Write Fields:
        - country_code: Two-letter ISO code, must match existing Country (required)
        - fuel_type: Must be valid FuelType choice (required)
        - price_per_liter: Must be 0.50-3.00 EUR range (required)
        - scraped_at: Optional timestamp, defaults to current time
    
    Validation:
        - Country code must be valid ISO 3166-1 alpha-2 format
        - Country must exist in database
        - Fuel type must be 'gasoline' or 'diesel'
        - Price must be positive (> 0)
        - Price must be within 0.50-3.00 EUR range
        - Unique constraint: one price per country/fuel type/day
    
    Example:
        Creating a fuel price:
        
        >>> data = {
        ...     'country_code': 'PL',
        ...     'fuel_type': 'gasoline',
        ...     'price_per_liter': '1.45'
        ... }
        >>> serializer = FuelPriceSerializer(data=data)
        >>> serializer.is_valid()
        True
        >>> fuel_price = serializer.save()
        >>> fuel_price.country.name
        'Poland'
        
        Serializing an instance:
        
        >>> serializer = FuelPriceSerializer(fuel_price)
        >>> serializer.data
        {
            'id': 1,
            'country_code': 'PL',
            'country_name': 'Poland',
            'fuel_type': 'gasoline',
            'price_per_liter': '1.450',
            'scraped_at': '2024-01-15T10:30:00Z'
        }
    """
    country_code = serializers.CharField(
        max_length=2,
        write_only=True,
        help_text="ISO 3166-1 alpha-2 country code (e.g., PL, DE)."
    )
    country_name = serializers.CharField(
        source='country.name',
        read_only=True,
        help_text="Human-readable country name."
    )
    
    class Meta:
        model = FuelPrice
        fields = [
            'id',
            'country_code',
            'country_name',
            'fuel_type',
            'price_per_liter',
            'scraped_at',
        ]
        read_only_fields = ['id', 'scraped_at']
    
    def validate_country_code(self, value):
        """Validate and normalize country code.
        
        Ensures the country code is valid ISO 3166-1 alpha-2 format and
        that the country exists in the database. Automatically normalizes
        the code to uppercase.
        
        Args:
            value: Raw country code string from request data.
        
        Returns:
            str: Normalized uppercase country code.
        
        Raises:
            serializers.ValidationError: If code is empty, invalid ISO format,
                or country doesn't exist in database.
        
        Example:
            >>> serializer.validate_country_code('pl')
            'PL'
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Country code cannot be empty.")
        
        value = value.strip().upper()
        
        try:
            iso_country_code_validator(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        
        if not Country.objects.filter(code=value).exists():
            raise serializers.ValidationError(
                f"Country with code '{value}' does not exist. "
                "Please ensure the country is registered in the system first."
            )
        
        return value
    
    def validate_price_per_liter(self, value):
        """Validate fuel price is positive and within acceptable range.
        
        Ensures the price is greater than zero and within the acceptable
        range of 0.50-3.00 EUR to catch data entry errors or anomalies.
        
        Args:
            value: Decimal price value from request data.
        
        Returns:
            Decimal: Validated price value.
        
        Raises:
            serializers.ValidationError: If price is None, not positive,
                or outside the 0.50-3.00 EUR range.
        
        Example:
            >>> serializer.validate_price_per_liter(Decimal('1.45'))
            Decimal('1.45')
            >>> serializer.validate_price_per_liter(Decimal('0'))
            # Raises ValidationError: "Price per liter must be greater than zero."
        """
        if value is None:
            raise serializers.ValidationError("Price per liter is required.")
        
        error = validate_positive_decimal(value, "Price per liter")
        if error:
            raise serializers.ValidationError(error)
        
        error = validate_fuel_price_range(value, "Price per liter")
        if error:
            raise serializers.ValidationError(error)
        
        return value
    
    def validate_fuel_type(self, value):
        """Validate fuel type is a recognized choice.
        
        Ensures the fuel type is one of the valid options defined in
        the FuelType choices ('gasoline' or 'diesel').
        
        Args:
            value: Fuel type string from request data.
        
        Returns:
            str: Validated fuel type value.
        
        Raises:
            serializers.ValidationError: If fuel type is empty or not
                a valid choice from FuelType.
        
        Example:
            >>> serializer.validate_fuel_type('gasoline')
            'gasoline'
            >>> serializer.validate_fuel_type('kerosene')
            # Raises ValidationError: "Invalid fuel type..."
        """
        if not value:
            raise serializers.ValidationError("Fuel type is required.")
        
        valid_types = [choice[0] for choice in FuelType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid fuel type. Must be one of: {', '.join(valid_types)}"
            )
        
        return value
    
    def validate(self, attrs):
        """Perform cross-field validation and country lookup.
        
        Resolves the country_code to the actual Country instance and
        adds it to validated data. This ensures the country exists
        before attempting to create a FuelPrice record.
        
        Args:
            attrs: Dictionary of validated field values.
        
        Returns:
            dict: Validated attributes with 'country' key added.
        
        Raises:
            serializers.ValidationError: If country with given code
                doesn't exist in database.
        
        Example:
            >>> attrs = {'country_code': 'PL', 'fuel_type': 'gasoline', ...}
            >>> validated = serializer.validate(attrs)
            >>> 'country' in validated
            True
        """
        country_code = attrs.get('country_code')
        
        if country_code:
            try:
                country = Country.objects.get(code=country_code)
                attrs['country'] = country
            except Country.DoesNotExist:
                raise serializers.ValidationError({
                    'country_code': f"Country with code '{country_code}' does not exist."
                })
        
        return attrs
    
    def create(self, validated_data):
        """Create a new FuelPrice instance with automatic timestamp.
        
        Removes the temporary country_code field and sets scraped_at
        to current time if not provided. The country relation is already
        resolved in the validate() method.
        
        Args:
            validated_data: Dictionary of validated field values including
                the Country instance.
        
        Returns:
            FuelPrice: Newly created FuelPrice instance.
        
        Example:
            >>> validated_data = {
            ...     'country': country_instance,
            ...     'fuel_type': 'gasoline',
            ...     'price_per_liter': Decimal('1.45')
            ... }
            >>> fuel_price = serializer.create(validated_data)
            >>> fuel_price.scraped_at  # Auto-set to current time
        """
        validated_data.pop('country_code', None)
        
        if 'scraped_at' not in validated_data:
            validated_data['scraped_at'] = timezone.now()
        
        return super().create(validated_data)
    
    def to_representation(self, instance):
        """Convert FuelPrice instance to API response format.
        
        Adds the denormalized country_code field to the standard
        representation for improved API usability. The country_name
        is already included through the ModelSerializer field definition.
        
        Args:
            instance: FuelPrice model instance to serialize.
        
        Returns:
            dict: Serialized representation with all read fields including
                denormalized country_code.
        
        Example:
            >>> representation = serializer.to_representation(fuel_price)
            >>> representation['country_code']
            'PL'
            >>> representation['country_name']
            'Poland'
        """
        representation = super().to_representation(instance)
        representation['country_code'] = instance.country_code
        return representation