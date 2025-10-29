"""Tests for Route model."""

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone

from routes.models import Route


@pytest.mark.integration
class TestRouteModel:
    """Tests for Route model."""

    def test_create_route_with_valid_data(self, db, user):
        """Should create route with valid data."""
        route = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[
                {'lat': 52.2297, 'lng': 21.0122, 'country_code': 'PL', 'distance_from_start': 0},
                {'lat': 52.5200, 'lng': 13.4050, 'country_code': 'DE', 'distance_from_start': 520}
            ],
            countries=['PL', 'DE']
        )
        
        assert route.user == user
        assert route.google_maps_url == 'https://maps.google.com/test'
        assert route.origin == 'Warsaw, Poland'
        assert route.destination == 'Berlin, Germany'
        assert route.total_distance_km == Decimal('520.00')
        assert len(route.waypoints) == 2
        assert route.countries == ['PL', 'DE']

    def test_str_representation(self, db, user):
        """Should return formatted string with origin, destination, and distance."""
        route = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Paris, France',
            destination='London, UK',
            total_distance_km=Decimal('450.25'),
            waypoints=[],
            countries=['FR', 'GB']
        )
        
        assert str(route) == 'Paris, France → London, UK (450.25 km)'

    def test_origin_sanitization(self, db, user):
        """Should sanitize origin on validation."""
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='  Warsaw, Poland  ',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        route.full_clean()
        assert route.origin == 'Warsaw, Poland'  # Whitespace stripped

    def test_destination_sanitization(self, db, user):
        """Should sanitize destination on validation."""
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='  Berlin, Germany  ',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        route.full_clean()
        assert route.destination == 'Berlin, Germany'

    def test_origin_rejects_invalid_characters(self, db, user):
        """Should reject origin with invalid characters."""
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw<script>alert(1)</script>',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        with pytest.raises(ValidationError) as exc_info:
            route.full_clean()
        
        assert 'origin' in exc_info.value.error_dict

    def test_destination_rejects_invalid_characters(self, db, user):
        """Should reject destination with invalid characters."""
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin@#$%',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        with pytest.raises(ValidationError) as exc_info:
            route.full_clean()
        
        assert 'destination' in exc_info.value.error_dict

    def test_total_distance_must_be_positive(self, db, user):
        """Should raise ValidationError for non-positive distance."""
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('0'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        with pytest.raises(ValidationError) as exc_info:
            route.full_clean()
        
        assert 'total_distance_km' in exc_info.value.error_dict
        assert 'greater than zero' in str(exc_info.value.error_dict['total_distance_km'])

    def test_negative_distance_not_allowed(self, db, user):
        """Should raise ValidationError for negative distance."""
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('-100.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        with pytest.raises(ValidationError) as exc_info:
            route.full_clean()
        
        assert 'total_distance_km' in exc_info.value.error_dict

    def test_waypoints_must_be_list(self, db, user):
        """Should raise ValidationError if waypoints is not a list."""
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints={'invalid': 'dict'},
            countries=['PL', 'DE']
        )
        
        with pytest.raises(ValidationError) as exc_info:
            route.full_clean()
        
        assert 'waypoints' in exc_info.value.error_dict
        assert 'must be a list' in str(exc_info.value.error_dict['waypoints'])

    def test_countries_must_be_list(self, db, user):
        """Should raise ValidationError if countries is not a list."""
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries='PLDE'
        )
        
        with pytest.raises(ValidationError) as exc_info:
            route.full_clean()
        
        assert 'countries' in exc_info.value.error_dict
        assert 'must be a list' in str(exc_info.value.error_dict['countries'])

    def test_empty_waypoints_list_allowed(self, db, user):
        """Should allow empty waypoints list."""
        route = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        assert route.waypoints == []

    def test_empty_countries_list_allowed(self, db, user):
        """Should allow empty countries list."""
        route = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=[]
        )
        
        assert route.countries == []

    def test_default_waypoints_is_empty_list(self, db, user):
        """Should default waypoints to empty list."""
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            countries=['PL', 'DE']
        )
        
        # Before saving, default should be set
        assert route.waypoints == []

    def test_default_countries_is_empty_list(self, db, user):
        """Should default countries to empty list."""
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[]
        )
        
        assert route.countries == []

    def test_user_is_required(self, db):
        """Should raise ValidationError when user is missing."""
        route = Route(
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        with pytest.raises(ValidationError) as exc_info:
            route.full_clean()
        
        assert 'user' in exc_info.value.error_dict

    def test_google_maps_url_is_required(self, db, user):
        """Should raise ValidationError when google_maps_url is missing."""
        route = Route(
            user=user,
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        with pytest.raises(ValidationError) as exc_info:
            route.full_clean()
        
        assert 'google_maps_url' in exc_info.value.error_dict

    def test_origin_is_required(self, db, user):
        """Should raise ValidationError when origin is missing."""
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        with pytest.raises(ValidationError) as exc_info:
            route.full_clean()
        
        assert 'origin' in exc_info.value.error_dict

    def test_destination_is_required(self, db, user):
        """Should raise ValidationError when destination is missing."""
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        with pytest.raises(ValidationError) as exc_info:
            route.full_clean()
        
        assert 'destination' in exc_info.value.error_dict

    def test_total_distance_km_is_required(self, db, user):
        """Should raise ValidationError when total_distance_km is missing."""
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        with pytest.raises(ValidationError) as exc_info:
            route.full_clean()
        
        assert 'total_distance_km' in exc_info.value.error_dict

    def test_multiple_routes_for_same_user(self, db, user):
        """Should allow multiple routes for the same user."""
        route1 = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test1',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        route2 = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test2',
            origin='Paris, France',
            destination='London, UK',
            total_distance_km=Decimal('450.00'),
            waypoints=[],
            countries=['FR', 'GB']
        )
        
        assert route1.user == route2.user
        assert route1.origin != route2.origin

    def test_multiple_users_same_route(self, db, user, another_user):
        """Should allow different users to have the same route."""
        route1 = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test1',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        route2 = Route.objects.create(
            user=another_user,
            google_maps_url='https://maps.google.com/test2',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        assert route1.user != route2.user
        assert route1.origin == route2.origin
        assert route1.destination == route2.destination

    def test_ordering_by_created_at_descending(self, db, user):
        """Should order routes by created_at in descending order (newest first)."""
        route1 = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test1',
            origin='Route 1',
            destination='Dest 1',
            total_distance_km=Decimal('100.00'),
            waypoints=[],
            countries=[]
        )
        
        route2 = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test2',
            origin='Route 2',
            destination='Dest 2',
            total_distance_km=Decimal('200.00'),
            waypoints=[],
            countries=[]
        )
        
        route3 = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test3',
            origin='Route 3',
            destination='Dest 3',
            total_distance_km=Decimal('300.00'),
            waypoints=[],
            countries=[]
        )
        
        routes = list(Route.objects.all())
        
        # Newest first
        assert routes[0] == route3
        assert routes[1] == route2
        assert routes[2] == route1

    def test_created_at_auto_populated(self, db, user):
        """Should auto-populate created_at timestamp."""
        before = timezone.now()
        route = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        after = timezone.now()
        
        assert route.created_at is not None
        assert before <= route.created_at <= after

    def test_created_at_does_not_change_on_update(self, db, user):
        """Should not change created_at on update."""
        route = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        original_created_at = route.created_at
        
        route.total_distance_km = Decimal('530.00')
        route.save()
        
        assert route.created_at == original_created_at

    def test_complex_waypoints_structure(self, db, user):
        """Should handle complex waypoints structure."""
        waypoints = [
            {
                'lat': 52.2297,
                'lng': 21.0122,
                'country_code': 'PL',
                'distance_from_start': 0,
                'city': 'Warsaw'
            },
            {
                'lat': 52.4064,
                'lng': 16.9252,
                'country_code': 'PL',
                'distance_from_start': 300,
                'city': 'Poznań'
            },
            {
                'lat': 52.5200,
                'lng': 13.4050,
                'country_code': 'DE',
                'distance_from_start': 520,
                'city': 'Berlin'
            }
        ]
        
        route = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=waypoints,
            countries=['PL', 'DE']
        )
        
        assert len(route.waypoints) == 3
        assert route.waypoints[0]['city'] == 'Warsaw'
        assert route.waypoints[1]['city'] == 'Poznań'
        assert route.waypoints[2]['city'] == 'Berlin'

    def test_url_field_validates_url_format(self, db, user):
        """Should validate URL format for google_maps_url."""
        route = Route(
            user=user,
            google_maps_url='not-a-valid-url',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        with pytest.raises(ValidationError) as exc_info:
            route.full_clean()
        
        assert 'google_maps_url' in exc_info.value.error_dict

    def test_route_fixture(self, route):
        """Should work with route fixture."""
        assert route.origin == 'Warsaw, Poland'
        assert route.destination == 'Berlin, Germany'
        assert route.total_distance_km == Decimal('520.00')
        assert len(route.waypoints) == 2
        assert route.countries == ['PL', 'DE']

    def test_validated_model_calls_full_clean_on_save(self, db, user):
        """Should call full_clean() on save (ValidatedModel behavior)."""
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('0'),  # Invalid - not positive
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        # Should raise validation error on save due to ValidatedModel
        with pytest.raises(ValidationError):
            route.save()

    def test_origin_max_length_validation(self, db, user):
        """Should validate max_length for origin."""
        long_origin = 'A' * 250  # Exceeds max_length of 200
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin=long_origin,
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        with pytest.raises(ValidationError) as exc_info:
            route.full_clean()
        
        assert 'origin' in exc_info.value.error_dict

    def test_destination_max_length_validation(self, db, user):
        """Should validate max_length for destination."""
        long_destination = 'B' * 250  # Exceeds max_length of 200
        route = Route(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination=long_destination,
            total_distance_km=Decimal('520.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        with pytest.raises(ValidationError) as exc_info:
            route.full_clean()
        
        assert 'destination' in exc_info.value.error_dict

    def test_unicode_in_locations(self, db, user):
        """Should accept unicode characters in locations."""
        route = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Łódź, Polska',
            destination='München, Deutschland',
            total_distance_km=Decimal('750.00'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        assert 'Łódź' in route.origin
        assert 'München' in route.destination

    def test_decimal_precision_for_distance(self, db, user):
        """Should store distance with proper decimal precision."""
        route = Route.objects.create(
            user=user,
            google_maps_url='https://maps.google.com/test',
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            total_distance_km=Decimal('520.47'),
            waypoints=[],
            countries=['PL', 'DE']
        )
        
        assert route.total_distance_km == Decimal('520.47')