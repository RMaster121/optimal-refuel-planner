"""Serializers for the Refuel Planner API."""

from rest_framework import serializers

from cars.models import Car
from cars.serializers import CarSerializer
from planner.exceptions import PlanningError
from planner.models import RefuelPlan, RefuelStop
from planner.services.planner_service import PlannerService
from refuel_planner.choices import OptimizationStrategy
from routes.models import Route
from routes.serializers import RouteSerializer


class RefuelStopSerializer(serializers.ModelSerializer):
    """
    Serializer for individual refuel stops.
    
    Displays all stop details including location, fuel, and cost information.
    """
    country_code = serializers.CharField(source='country.code', read_only=True)
    country_name = serializers.CharField(source='country.name', read_only=True)
    fuel_type = serializers.CharField(source='fuel_price.fuel_type', read_only=True)
    price_per_liter = serializers.DecimalField(
        source='fuel_price.price_per_liter',
        max_digits=5,
        decimal_places=3,
        read_only=True
    )
    
    class Meta:
        model = RefuelStop
        fields = [
            'id',
            'stop_number',
            'country_code',
            'country_name',
            'distance_from_start_km',
            'fuel_to_add_liters',
            'fuel_type',
            'price_per_liter',
            'total_cost',
            'latitude',
            'longitude',
        ]
        read_only_fields = fields


class RefuelPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for refuel plans with nested stops.
    
    Used for reading/listing plans. Includes full route and car details.
    """
    route = RouteSerializer(read_only=True)
    car = CarSerializer(read_only=True)
    stops = RefuelStopSerializer(many=True, read_only=True)
    optimization_strategy_display = serializers.CharField(
        source='get_optimization_strategy_display',
        read_only=True
    )
    
    class Meta:
        model = RefuelPlan
        fields = [
            'id',
            'route',
            'car',
            'reservoir_km',
            'optimization_strategy',
            'optimization_strategy_display',
            'total_cost',
            'total_fuel_needed',
            'number_of_stops',
            'stops',
            'created_at',
        ]
        read_only_fields = fields


class CreateRefuelPlanSerializer(serializers.Serializer):
    """
    Serializer for creating refuel plans.
    
    Validates input parameters and orchestrates plan creation via PlannerService.
    """
    route = serializers.PrimaryKeyRelatedField(
        queryset=Route.objects.none(),
        help_text="ID of the route to plan for."
    )
    car = serializers.PrimaryKeyRelatedField(
        queryset=Car.objects.none(),
        help_text="ID of the car to use."
    )
    reservoir_km = serializers.IntegerField(
        required=False,
        default=100,
        min_value=0,
        max_value=500,
        help_text="Safety reserve distance in kilometers (default: 100)."
    )
    optimization_strategy = serializers.ChoiceField(
        required=False,
        choices=OptimizationStrategy.choices,
        default=OptimizationStrategy.MIN_STOPS,
        help_text="Optimization strategy to use (default: min_stops)."
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set querysets dynamically based on request user
        if 'request' in self.context:
            user = self.context['request'].user
            self.fields['route'].queryset = Route.objects.filter(user=user)
            self.fields['car'].queryset = Car.objects.filter(user=user)
    
    def validate_route(self, value):
        """Validate route has required data."""
        if not value.waypoints:
            raise serializers.ValidationError(
                'Route has no waypoints. Cannot create plan.'
            )
        
        if not value.countries:
            raise serializers.ValidationError(
                'Route has no country data. Cannot create plan.'
            )
        
        return value
    
    def create(self, validated_data):
        """Create refuel plan using PlannerService."""
        route = validated_data['route']
        car = validated_data['car']
        reservoir_km = validated_data.get('reservoir_km', 100)
        strategy = validated_data.get('optimization_strategy', OptimizationStrategy.MIN_STOPS)  # TODO: Magic value?
        
        try:
            service = PlannerService(
                route=route,
                car=car,
                reservoir_km=reservoir_km,
                strategy=strategy
            )
            plan = service.create_plan()
            return plan
            
        except PlanningError as e:
            raise serializers.ValidationError({
                'non_field_errors': [str(e)]
            })
    
    def to_representation(self, instance):
        """Use RefuelPlanSerializer for response."""
        return RefuelPlanSerializer(instance).data