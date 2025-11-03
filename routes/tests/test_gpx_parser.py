"""Tests for GPX parser service."""

import io

import pytest

from routes.exceptions import InvalidGPXFileError
from routes.services.gpx_parser import GPXParser


@pytest.mark.django_db
class TestGPXParser:
    """Test suite for GPXParser."""

    def test_parse_simple_gpx_file(self, simple_gpx_content):
        """Test parsing a simple valid GPX file."""
        parser = GPXParser()
        gpx_file = io.BytesIO(simple_gpx_content.encode('utf-8'))
        result = parser.parse_gpx_file(gpx_file)

        assert result['name'] == 'Warsaw to Berlin'
        assert len(result['trackpoints']) == 2
        assert result['trackpoints'][0]['lat'] == pytest.approx(52.2297, abs=0.0001)
        assert result['trackpoints'][0]['lng'] == pytest.approx(21.0122, abs=0.0001)
        assert result['total_distance_m'] > 0

    def test_parse_route_format(self, route_format_gpx_content):
        """Test parsing GPX file with route instead of track."""
        parser = GPXParser()
        gpx_file = io.BytesIO(route_format_gpx_content.encode('utf-8'))
        result = parser.parse_gpx_file(gpx_file)

        assert result['name'] == 'Krakow to Wroclaw'
        assert len(result['trackpoints']) == 2
        assert result['trackpoints'][0]['lat'] == pytest.approx(50.0647, abs=0.0001)

    def test_parse_empty_gpx_raises_error(self, empty_gpx_content):
        """Test that GPX without trackpoints raises error."""
        parser = GPXParser()
        gpx_file = io.BytesIO(empty_gpx_content.encode('utf-8'))

        with pytest.raises(InvalidGPXFileError, match="No trackpoints found"):
            parser.parse_gpx_file(gpx_file)

    def test_parse_invalid_xml_raises_error(self):
        """Test that invalid XML raises error."""
        parser = GPXParser()
        invalid_xml = "This is not XML"
        gpx_file = io.BytesIO(invalid_xml.encode('utf-8'))

        with pytest.raises(InvalidGPXFileError, match="Invalid GPX format"):
            parser.parse_gpx_file(gpx_file)

    def test_haversine_distance_calculation(self):
        """Test Haversine distance calculation accuracy."""
        parser = GPXParser()
        # Warsaw to Berlin: ~520 km
        distance = parser._haversine_distance(52.2297, 21.0122, 52.5200, 13.4050)
        
        # Should be approximately 520 km (520000 m)
        assert 510000 < distance < 530000

    def test_generate_waypoints_default_interval(self):
        """Test waypoint generation with default 50km interval."""
        parser = GPXParser()
        trackpoints = [
            {'lat': 52.0, 'lng': 21.0},
            {'lat': 52.5, 'lng': 21.0},  # ~55 km north
            {'lat': 53.0, 'lng': 21.0},  # ~111 km north total
        ]
        
        waypoints = parser.generate_waypoints(trackpoints, interval_km=50)
        
        assert len(waypoints) >= 3  # Start, middle, end
        assert waypoints[0]['distance_from_start_km'] == 0.0
        assert waypoints[-1]['distance_from_start_km'] > 100

    def test_generate_waypoints_custom_interval(self):
        """Test waypoint generation with custom 25km interval."""
        parser = GPXParser()
        trackpoints = [
            {'lat': 52.0, 'lng': 21.0},
            {'lat': 52.5, 'lng': 21.0},
            {'lat': 53.0, 'lng': 21.0},
        ]
        
        waypoints = parser.generate_waypoints(trackpoints, interval_km=25)
        
        # Should have more waypoints with smaller interval
        assert len(waypoints) > 3

    def test_generate_waypoints_empty_trackpoints(self):
        """Test waypoint generation with empty trackpoints."""
        parser = GPXParser()
        waypoints = parser.generate_waypoints([])
        assert waypoints == []

    def test_generate_waypoints_includes_start_and_end(self):
        """Test that waypoints always include start and end points."""
        parser = GPXParser()
        trackpoints = [
            {'lat': 52.0, 'lng': 21.0},
            {'lat': 52.2, 'lng': 21.2},
            {'lat': 52.4, 'lng': 21.4},
        ]
        
        waypoints = parser.generate_waypoints(trackpoints, interval_km=100)
        
        assert waypoints[0]['lat'] == 52.0
        assert waypoints[0]['lng'] == 21.0
        assert waypoints[-1]['lat'] == 52.4
        assert waypoints[-1]['lng'] == 21.4