"""Tests for Route API endpoints."""

import io
from decimal import Decimal

import pytest
from rest_framework import status


@pytest.mark.django_db
class TestRouteAPI:
    """Test suite for Route API endpoints."""

    def test_list_routes_requires_authentication(self, api_client):
        """Test that listing routes requires authentication."""
        response = api_client.get('/api/routes/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_routes_returns_user_routes(self, authenticated_client, route):
        """Test that authenticated user can list their routes."""
        response = authenticated_client.get('/api/routes/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['origin'] == 'Warsaw, Poland'

    def test_list_routes_filters_by_user(self, authenticated_client, route, another_user):
        """Test that users only see their own routes."""
        from routes.models import Route
        
        # Create route for another user
        Route.objects.create(
            user=another_user,
            origin='Paris, France',
            destination='London, UK',
            total_distance_km=Decimal('450.00'),
            waypoints=[],
            countries=['FR', 'UK']
        )
        
        response = authenticated_client.get('/api/routes/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['origin'] == 'Warsaw, Poland'

    def test_create_route_with_gpx_file(self, authenticated_client, gpx_file_simple):
        """Test creating a route by uploading a GPX file."""
        response = authenticated_client.post(
            '/api/routes/',
            {
                'gpx_file': gpx_file_simple,
                'waypoint_interval_km': 50
            },
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['origin'] == 'Poland'
        assert response.data['destination'] == 'Germany'
        assert 'waypoints' in response.data
        assert 'countries' in response.data

    def test_create_route_with_invalid_file_type(self, authenticated_client):
        """Test that non-GPX files are rejected."""
        txt_file = io.BytesIO(b"Not a GPX file")
        txt_file.name = 'test.txt'
        
        response = authenticated_client.post(
            '/api/routes/',
            {'gpx_file': txt_file},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_route_without_file(self, authenticated_client):
        """Test that route creation without file fails."""
        response = authenticated_client.post('/api/routes/', {})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_route(self, authenticated_client, route):
        """Test retrieving a specific route."""
        response = authenticated_client.get(f'/api/routes/{route.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['origin'] == 'Warsaw, Poland'
        assert response.data['destination'] == 'Berlin, Germany'

    def test_retrieve_other_user_route_returns_404(
        self, authenticated_client, another_user
    ):
        """Test that users cannot access other users' routes."""
        from routes.models import Route
        
        other_route = Route.objects.create(
            user=another_user,
            origin='Paris, France',
            destination='London, UK',
            total_distance_km=Decimal('450.00'),
            waypoints=[],
            countries=['FR', 'UK']
        )
        
        response = authenticated_client.get(f'/api/routes/{other_route.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_route(self, authenticated_client, route):
        """Test deleting a route."""
        response = authenticated_client.delete(f'/api/routes/{route.id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify route is deleted
        response = authenticated_client.get(f'/api/routes/{route.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_search_routes_by_origin(self, authenticated_client, route):
        """Test searching routes by origin."""
        response = authenticated_client.get('/api/routes/?search=Warsaw')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_search_routes_by_destination(self, authenticated_client, route):
        """Test searching routes by destination."""
        response = authenticated_client.get('/api/routes/?search=Berlin')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_order_routes_by_created_at(self, authenticated_client, user):
        """Test ordering routes by creation date."""
        from routes.models import Route
        
        # Create multiple routes
        Route.objects.create(
            user=user,
            origin='A',
            destination='B',
            total_distance_km=Decimal('100.00'),
            waypoints=[],
            countries=['PL']
        )
        Route.objects.create(
            user=user,
            origin='C',
            destination='D',
            total_distance_km=Decimal('200.00'),
            waypoints=[],
            countries=['DE']
        )
        
        response = authenticated_client.get('/api/routes/?ordering=-created_at')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_custom_waypoint_interval(self, authenticated_client, gpx_file_simple):
        """Test creating route with custom waypoint interval."""
        response = authenticated_client.post(
            '/api/routes/',
            {
                'gpx_file': gpx_file_simple,
                'waypoint_interval_km': 25
            },
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_201_CREATED