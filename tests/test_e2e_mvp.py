"""
End-to-end integration test for MVP.

Simulates complete user workflow:
1. User registers
2. User logs in
3. User creates a car profile
4. User uploads a GPX route (Warsaw → Berlin)
5. User creates a refuel plan
6. Verify plan is correct
"""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
class TestMVPEndToEnd:
    
    def test_complete_mvp_workflow(self, api_client, country_poland, country_germany,
                                   fuel_price_pl_gasoline, fuel_price_de_gasoline):
        """Test complete workflow from registration to refuel plan."""
        
        # 1. Register user
        register_response = api_client.post('/api/auth/register/', {
            'email': 'testuser@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User'
        })
        assert register_response.status_code == 201
        tokens = register_response.data['tokens']
        
        # Set auth header
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        # 2. Create car profile
        car_response = api_client.post('/api/cars/', {
            'name': 'Toyota Corolla',
            'fuel_type': 'gasoline',
            'avg_consumption': '6.0',
            'tank_capacity': '50.0'
        })
        assert car_response.status_code == 201
        car_id = car_response.data['id']
        assert car_response.data['max_range_km'] == '833.33'
        
        # 3. Upload GPX route (Warsaw → Berlin)
        gpx_content = create_test_gpx_warsaw_berlin()
        gpx_file = SimpleUploadedFile(
            'warsaw_berlin.gpx',
            gpx_content.encode('utf-8'),
            content_type='application/gpx+xml'
        )
        
        route_response = api_client.post(
            '/api/routes/',
            {'gpx_file': gpx_file, 'waypoint_interval_km': 20},
            format='multipart'
        )
        assert route_response.status_code == 201
        route = route_response.data
        route_id = route['id']
        
        # Verify route details
        assert route['origin'] == 'Poland'
        assert route['destination'] == 'Germany'
        assert float(route['total_distance_km']) >= 515
        assert float(route['total_distance_km']) <= 580
        assert 'PL' in route['countries']
        assert 'DE' in route['countries']
        
        # 4. Create refuel plan
        plan_response = api_client.post('/api/refuel-plans/', {
            'route': route_id,
            'car': car_id,
            'reservoir_km': 100,
            'optimization_strategy': 'min_stops'
        })
        assert plan_response.status_code == 201
        plan = plan_response.data
        
        # Verify plan details
        assert plan['optimization_strategy'] == 'min_stops'
        assert plan['reservoir_km'] == 100
        assert plan['number_of_stops'] == 0  # Route < car range
        assert float(plan['total_fuel_needed']) > 30  # ~33-35L for ~575km
        assert float(plan['total_fuel_needed']) < 40
        
        # 5. List plans (verify we can retrieve it)
        list_response = api_client.get('/api/refuel-plans/')
        assert list_response.status_code == 200
        assert list_response.data['count'] == 1
        
        # 6. Retrieve specific plan
        detail_response = api_client.get(f'/api/refuel-plans/{plan["id"]}/')
        assert detail_response.status_code == 200
        assert detail_response.data['id'] == plan['id']


def create_test_gpx_warsaw_berlin():
    """Create realistic GPX file for Warsaw → Berlin route."""
    return '''<?xml version="1.0"?>
<gpx version="1.1" creator="OptimalRefuelPlanner">
  <trk>
    <name>Warsaw to Berlin</name>
    <trkseg>
      <trkpt lat="52.2297" lon="21.0122"><ele>100</ele></trkpt>
      <trkpt lat="52.3500" lon="20.5000"><ele>95</ele></trkpt>
      <trkpt lat="52.4500" lon="19.8000"><ele>90</ele></trkpt>
      <trkpt lat="52.5000" lon="19.0000"><ele>85</ele></trkpt>
      <trkpt lat="52.5200" lon="18.0000"><ele>80</ele></trkpt>
      <trkpt lat="52.5300" lon="17.0000"><ele>75</ele></trkpt>
      <trkpt lat="52.5350" lon="16.0000"><ele>70</ele></trkpt>
      <trkpt lat="52.5300" lon="15.0000"><ele>65</ele></trkpt>
      <trkpt lat="52.5200" lon="14.0000"><ele>60</ele></trkpt>
      <trkpt lat="52.5200" lon="13.4050"><ele>55</ele></trkpt>
    </trkseg>
  </trk>
</gpx>'''