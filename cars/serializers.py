"""Serializers for the Car API."""

from decimal import Decimal

from rest_framework import serializers

from cars.models import Car
from refuel_planner.validators import (
    validate_and_sanitize_name,
    validate_positive_decimal,
)


class CarSerializer(serializers.ModelSerializer):
    """
    Serializer for Car model with comprehensive validation.
    
    Includes all car fields plus a computed read-only max_range_km field.
    Validates that avg_consumption and tank_capacity are positive and reasonable.
    Ensures car names are unique per user.
    """
    max_range_km = serializers.DecimalField(
        max_digits=7,
        decimal_places=2,
        read_only=True,
        help_text="Computed maximum range in kilometers on a full tank."
    )
    
    class Meta:
        model = Car
        fields = [
            'id',
            'name',
            'fuel_type',
            'avg_consumption',
            'tank_capacity',
            'max_range_km',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'max_range_km', 'created_at', 'updated_at']
    
    def validate_avg_consumption(self, value):
        """Validate average consumption is positive and within 1-30 L/100km range."""
        if value is None:
            raise serializers.ValidationError("Average consumption is required.")
        
        error = validate_positive_decimal(value, "Average consumption")
        if error:
            raise serializers.ValidationError(error)
        
        if value < Decimal('1.0'):
            raise serializers.ValidationError(
                "Average consumption seems unreasonably low. "
                "Please enter a value between 1 and 30 L/100km."
            )
        
        if value > Decimal('30.0'):
            raise serializers.ValidationError(
                "Average consumption seems unreasonably high. "
                "Please enter a value between 1 and 30 L/100km."
            )
        
        return value
    
    def validate_tank_capacity(self, value):
        """Validate tank capacity is positive and within 20-200 liters range."""
        if value is None:
            raise serializers.ValidationError("Tank capacity is required.")
        
        error = validate_positive_decimal(value, "Tank capacity")
        if error:
            raise serializers.ValidationError(error)
        
        if value < Decimal('20.0'):
            raise serializers.ValidationError(
                "Tank capacity seems unreasonably low. "
                "Please enter a value between 20 and 200 liters."
            )
        
        if value > Decimal('200.0'):
            raise serializers.ValidationError(
                "Tank capacity seems unreasonably high. "
                "Please enter a value between 20 and 200 liters."
            )
        
        return value
    
    def validate_name(self, value):
        """Validate and sanitize the car name."""
        sanitized_value, error = validate_and_sanitize_name(
            value,
            field_name="Car name",
            max_length=100
        )
        
        if error:
            raise serializers.ValidationError(error)
        
        return sanitized_value
    
    def validate(self, attrs):
        """Ensure car name is unique per user."""
        user = self.context.get('request').user if self.context.get('request') else None
        name = attrs.get('name')
        
        if user and name:
            queryset = Car.objects.filter(user=user, name=name)
            
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError({
                    'name': 'You already have a car with this name.'
                })
        
        return attrs