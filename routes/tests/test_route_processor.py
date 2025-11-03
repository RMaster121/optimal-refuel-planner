"""Tests for route processor service."""

import io

import pytest

from routes.exceptions import RouteProcessingError, InvalidGPXFileError
from routes.services.route_processor import RouteProcessor


@pytest.mark.django_db
class TestRouteProcessor:
    """Test suite for RouteProcessor."""

    def test_process_gpx_upload_success(self, simple_gpx_content):
        """Test successful GPX file processing."""
        processor = RouteProcessor()
        gpx_file = io.BytesIO(simple_gpx_content.encode('utf-8'))
        
        result = processor.process_gpx_upload(gpx_file, waypoint_interval_km=50)

        assert result['origin'] == 'Poland'
        assert result['destination'] == 'Germany'
        assert result['total_distance_km'] > 0
        assert len(result['waypoints']) >= 2
        assert 'PL' in result['countries']
        assert 'DE' in result['countries']

    def test_process_gpx_upload_custom_interval(self, simple_gpx_content):
        """Test GPX processing with custom waypoint interval."""
        processor = RouteProcessor()
        gpx_file = io.BytesIO(simple_gpx_content.encode('utf-8'))
        
        result = processor.process_gpx_upload(gpx_file, waypoint_interval_km=25)

        assert 'waypoints' in result
        assert len(result['waypoints']) >= 2

    def test_process_gpx_upload_invalid_file_raises_error(self, empty_gpx_content):
        """Test that invalid GPX file raises error."""
        processor = RouteProcessor()
        gpx_file = io.BytesIO(empty_gpx_content.encode('utf-8'))

        with pytest.raises(InvalidGPXFileError):
            processor.process_gpx_upload(gpx_file)

    def test_identify_countries_adds_country_codes(self):
        """Test that waypoints are enriched with country codes."""
        processor = RouteProcessor()
        waypoints = [
            {'lat': 52.2297, 'lng': 21.0122, 'distance_from_start_km': 0.0},
            {'lat': 52.5200, 'lng': 13.4050, 'distance_from_start_km': 520.0},
        ]

        enhanced, countries = processor._identify_countries(waypoints)

        assert len(enhanced) == 2
        assert enhanced[0]['country_code'] == 'PL'
        assert enhanced[1]['country_code'] == 'DE'
        assert countries == ['PL', 'DE']

    def test_identify_countries_maintains_order(self):
        """Test that country list maintains order of appearance."""
        processor = RouteProcessor()
        waypoints = [
            {'lat': 52.2297, 'lng': 21.0122, 'distance_from_start_km': 0.0},    # PL
            {'lat': 50.0647, 'lng': 19.9450, 'distance_from_start_km': 100.0},  # PL
            {'lat': 52.5200, 'lng': 13.4050, 'distance_from_start_km': 520.0},  # DE
        ]

        enhanced, countries = processor._identify_countries(waypoints)

        assert countries == ['PL', 'DE']  # PL only listed once

    def test_waypoints_have_all_required_fields(self, simple_gpx_content):
        """Test that processed waypoints contain all required fields."""
        processor = RouteProcessor()
        gpx_file = io.BytesIO(simple_gpx_content.encode('utf-8'))
        
        result = processor.process_gpx_upload(gpx_file)

        for waypoint in result['waypoints']:
            assert 'lat' in waypoint
            assert 'lng' in waypoint
            assert 'country_code' in waypoint
            assert 'distance_from_start_km' in waypoint