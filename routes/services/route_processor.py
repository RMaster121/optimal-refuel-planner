"""Process uploaded GPX files into route data."""

from typing import Dict, List, Optional

from routes.exceptions import RouteProcessingError, InvalidGPXFileError, GeocodingError
from routes.services.gpx_parser import GPXParser
from routes.services.helpers import m_to_km_round
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

            trackpoints = gpx_data['trackpoints']

            waypoints = self.gpx_parser.generate_waypoints(
                trackpoints,
                waypoint_interval_km
            )

            waypoints = self.gpx_parser.inject_borders_and_geocode(
                waypoints,
                trackpoints,
                self._safe_geocode
            )

            countries = self._extract_ordered_countries(waypoints)
            segments = self._generate_segments(waypoints)

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
                'total_distance_km': m_to_km_round(gpx_data['total_distance_m']),
                'waypoints': waypoints,
                'segments': segments,
                'countries': countries
            }

        except (InvalidGPXFileError, GeocodingError) as e:
            raise RouteProcessingError(e)
        except Exception as e:
            raise RouteProcessingError(f"Route processing failed: {str(e)}")

    def _safe_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        Inject geocoder function into parser
        """
        try:
            return self.geocoder.get_country(lat, lng)['country_code']
        except GeocodingError:
            return None

    @staticmethod
    def _extract_ordered_countries(waypoints: List[Dict]) -> List[str]:
        """
        Extract list of ordered countries from waypoints.
        """
        seen = set()
        ordered = []
        for wp in waypoints:
            cc = wp.get('country_code')
            if cc and cc not in seen:
                seen.add(cc)
                ordered.append(cc)
        return ordered

    def _generate_segments(self, waypoints: List[Dict]) -> List[Dict]:
        """Tworzy zbiór bloków krajowych na podstawie geokodowanych waypointów i granic."""
        if not waypoints:
            return []

        segments = []
        start_wp = waypoints[0]
        current_country = start_wp['country_code']

        for i in range(1, len(waypoints)):
            wp = waypoints[i]
            if wp.get('country_code') != current_country:
                segments.append({
                    'country_code': current_country,
                    'start_distance_km': round(start_wp['distance_from_start_km'], 2),
                    'end_distance_km': round(wp['distance_from_start_km'], 2),
                    'distance_km': round(wp['distance_from_start_km'] - start_wp['distance_from_start_km'], 2),
                    'entry_lat': start_wp.get('lat'),
                    'entry_lng': start_wp.get('lng')
                })
                current_country = wp['country_code']
                start_wp = wp

        # Zamykamy ostatni segment trasy
        last_wp = waypoints[-1]
        segments.append({
            'country_code': current_country,
            'start_distance_km': round(start_wp['distance_from_start_km'], 2),
            'end_distance_km': round(last_wp['distance_from_start_km'], 2),
            'distance_km': round(last_wp['distance_from_start_km'] - start_wp['distance_from_start_km'], 2),
            'entry_lat': start_wp.get('lat'),
            'entry_lng': start_wp.get('lng')
        })
        return segments