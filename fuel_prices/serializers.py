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
    """
    Serializer for FuelPrice model with comprehensive validation.
    
    Accepts country_code for write operations and returns denormalized
    country_code and country_name for read operations.
    All prices are in EUR.
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
        if not value:
            raise serializers.ValidationError("Fuel type is required.")
        
        valid_types = [choice[0] for choice in FuelType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid fuel type. Must be one of: {', '.join(valid_types)}"
            )
        
        return value
    
    def validate(self, attrs):
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
        validated_data.pop('country_code', None)
        
        if 'scraped_at' not in validated_data:
            validated_data['scraped_at'] = timezone.now()
        
        return super().create(validated_data)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['country_code'] = instance.country_code
        return representation