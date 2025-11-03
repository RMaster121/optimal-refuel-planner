"""Process uploaded GPX files into route data."""

from typing import Dict, List, Tuple

from routes.exceptions import RouteProcessingError, InvalidGPXFileError, GeocodingError
from routes.services.gpx_parser import GPXParser
from routes.services.offline_geocoder import OfflineGeocoder


class RouteProcessor:
    """Process uploaded GPX files into route data with offline country detection."""

    def __init__(self):
        self.gpx_parser = GPXParser()
        self.geocoder = OfflineGeocoder()

    def process_gpx_upload(self, gpx_file, waypoint_interval_km: int = 50) -> Dict:
        """
        Complete GPX processing pipeline.

        Args:
            gpx_file: Uploaded file object
            waypoint_interval_km: Waypoint spacing in km (default: 50)

        Returns:
            dict - {
                'origin': str,
                'destination': str,
                'total_distance_km': float,
                'waypoints': list,
                'countries': list
            }

        Raises:
            RouteProcessingError: If processing fails
        """
        try:
            gpx_data = self.gpx_parser.parse_gpx_file(gpx_file)

            waypoints = self.gpx_parser.generate_waypoints(
                gpx_data['trackpoints'],
                waypoint_interval_km
            )

            waypoints, countries = self._identify_countries(waypoints)

            origin_info = self.geocoder.get_country(
                waypoints[0]['lat'],
                waypoints[0]['lng']
            )
            dest_info = self.geocoder.get_country(
                waypoints[-1]['lat'],
                waypoints[-1]['lng']
            )

            return {
                'origin': origin_info['country_name'],
                'destination': dest_info['country_name'],
                'total_distance_km': round(gpx_data['total_distance_m'] / 1000, 2),
                'waypoints': waypoints,
                'countries': countries
            }

        except (InvalidGPXFileError, GeocodingError) as e:
            raise
        except Exception as e:
            raise RouteProcessingError(f"Route processing failed: {str(e)}")

    def _identify_countries(self, waypoints: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """
        Geocode waypoints to identify countries using offline data.
        
        Args:
            waypoints: List of waypoint dicts with lat/lng
            
        Returns:
            Tuple of (enhanced_waypoints, ordered_countries)
            - enhanced_waypoints: Waypoints with country_code added
            - ordered_countries: Unique country codes in order of appearance
        """
        enhanced_waypoints = []
        seen_countries = set()
        ordered_countries = []

        for waypoint in waypoints:
            try:
                country_info = self.geocoder.get_country(
                    waypoint['lat'],
                    waypoint['lng']
                )
                waypoint['country_code'] = country_info['country_code']

                if country_info['country_code'] not in seen_countries:
                    seen_countries.add(country_info['country_code'])
                    ordered_countries.append(country_info['country_code'])

            except GeocodingError:
                waypoint['country_code'] = (
                    enhanced_waypoints[-1]['country_code']
                    if enhanced_waypoints else None
                )

            enhanced_waypoints.append(waypoint)

        return enhanced_waypoints, ordered_countries