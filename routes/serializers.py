"""Serializers for the Route API."""

from decimal import Decimal

from rest_framework import serializers

from routes.exceptions import RouteProcessingError
from routes.models import Route
from routes.services.route_processor import RouteProcessor


class RouteSerializer(serializers.ModelSerializer):
    """
    Serializer for Route model - used for reading/listing routes.
    
    Returns all route data including computed waypoints and countries.
    """
    
    class Meta:
        model = Route
        fields = [
            'id',
            'origin',
            'destination',
            'total_distance_km',
            'waypoints',
            'countries',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class RouteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating routes from GPX file uploads.
    
    Accepts a GPX file and optional waypoint interval,
    processes it offline, and creates a Route instance.
    """
    gpx_file = serializers.FileField(
        write_only=True,
        required=True,
        help_text="GPX file containing the route trackpoints."
    )
    waypoint_interval_km = serializers.IntegerField(
        write_only=True,
        required=False,
        default=20,
        min_value=10,
        max_value=200,
        help_text=(
            "Distance between waypoints in km. "
            "Default: 20 (safer for algorithm). "
            "Use higher values (50-100) for long simple routes."
        )
    )
    
    class Meta:
        model = Route
        fields = [
            'id',
            'gpx_file',
            'waypoint_interval_km',
            'origin',
            'destination',
            'total_distance_km',
            'waypoints',
            'countries',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'origin',
            'destination',
            'total_distance_km',
            'waypoints',
            'countries',
            'created_at',
        ]
    
    def validate_gpx_file(self, value):
        """Validate GPX file upload."""
        if not value:
            raise serializers.ValidationError("GPX file is required.")
        
        if not value.name.lower().endswith('.gpx'):
            raise serializers.ValidationError(
                "Invalid file type. Only .gpx files are accepted."
            )
        
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File too large. Maximum size is {max_size / 1024 / 1024:.0f}MB."
            )
        
        return value
    
    def validate_waypoint_interval_km(self, value):
        """Validate waypoint interval."""
        if value < 10:
            raise serializers.ValidationError(
                "Waypoint interval too small. Minimum is 10km."
            )
        
        if value > 200:
            raise serializers.ValidationError(
                "Waypoint interval too large. Maximum is 200km."
            )
        
        return value
    
    def create(self, validated_data):
        """Process GPX file and create Route instance."""
        gpx_file = validated_data.pop('gpx_file')
        waypoint_interval_km = validated_data.pop('waypoint_interval_km', 20)
        user = self.context['request'].user
        
        try:
            processor = RouteProcessor()
            route_data = processor.process_gpx_upload(
                gpx_file,
                waypoint_interval_km=waypoint_interval_km
            )
            
            route = Route.objects.create(
                user=user,
                origin=route_data['origin'],
                destination=route_data['destination'],
                total_distance_km=Decimal(str(route_data['total_distance_km'])),
                waypoints=route_data['waypoints'],
                countries=route_data['countries']
            )
            
            return route
            
        except RouteProcessingError as e:
            raise serializers.ValidationError({
                'gpx_file': f"Failed to process GPX file: {str(e)}"
            })
        except Exception as e:
            raise serializers.ValidationError({
                'gpx_file': f"Unexpected error processing GPX file: {str(e)}"
            })
    
    def to_representation(self, instance):
        """Use RouteSerializer for response."""
        return RouteSerializer(instance).data