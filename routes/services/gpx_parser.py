"""
Parse GPX files to extract route information.

Distance calculations track the actual driven path, essential for fuel consumption.
Waypoint intervals balance performance vs accuracy:
- 50km default: Optimal for most European routes, all borders detected
- 25km optional: For small countries (Luxembourg, Liechtenstein) or complex tri-border areas
"""

from typing import Dict, List, Callable, Optional

import gpxpy

from routes.exceptions import InvalidGPXFileError
from routes.services.helpers import haversine_distance, m_to_km_round


class GPXParser:
    """Parse GPX files to extract route information."""
    DIST_FROM_START = 'distance_from_start_km'

    def parse_gpx_file(self, gpx_file) -> Dict:
        """
        Parse uploaded GPX file.

        Args:
            gpx_file: File object from Django request.

        Returns:
            dict - {
                'name': str,
                'trackpoints': list of {lat, lng},
                'total_distance_m': float
            }

        Raises:
            InvalidGPXFileError: If file is invalid
        """
        try:
            gpx_content = gpx_file.read()
            if isinstance(gpx_content, bytes):
                gpx_content = gpx_content.decode('utf-8')

            gpx = gpxpy.parse(gpx_content)

            trackpoints = []
            total_distance = 0.0

            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        trackpoints.append({
                            'lat': float(point.latitude),
                            'lng': float(point.longitude)
                        })

            for route in gpx.routes:
                for point in route.points:
                    trackpoints.append({
                        'lat': float(point.latitude),
                        'lng': float(point.longitude)
                    })

            if not trackpoints:
                raise InvalidGPXFileError("No trackpoints found in GPX file")

            trackpoints[0][self.DIST_FROM_START] = 0

            for i in range(1, len(trackpoints)):
                prev = trackpoints[i-1]
                curr = trackpoints[i]
                total_distance += haversine_distance(
                    prev['lat'], prev['lng'],
                    curr['lat'], curr['lng']
                )
                curr[self.DIST_FROM_START] = m_to_km_round(total_distance)

            name = "Uploaded Route"
            if gpx.tracks and gpx.tracks[0].name:
                name = gpx.tracks[0].name
            elif gpx.routes and gpx.routes[0].name:
                name = gpx.routes[0].name

            return {
                'name': name,
                'trackpoints': trackpoints,
                'total_distance_m': total_distance
            }

        except gpxpy.gpx.GPXException as e:
            raise InvalidGPXFileError(f"Invalid GPX format: {str(e)}")
        except Exception as e:
            if isinstance(e, InvalidGPXFileError):
                raise
            raise InvalidGPXFileError(f"Failed to parse GPX: {str(e)}")

    @staticmethod
    def generate_waypoints(trackpoints: List[Dict], interval_km: int = 50) -> List[Dict]:
        """
        Generate waypoints from trackpoints at specified intervals.

        Args:
            trackpoints: All trackpoints from GPX
            interval_km: Distance between waypoints in km (default: 50)
                        - 50km: Recommended for most routes (>500km), large countries
                        - 25km: For small countries or complex tri-border areas

        Returns:
            list of {lat, lng, distance_from_start_km}
        """
        if not trackpoints:
            return []

        waypoints = []
        cumulative_distance_m = 0.0
        interval_m = interval_km * 1000

        waypoints.append({
            'lat': trackpoints[0]['lat'],
            'lng': trackpoints[0]['lng'],
            'distance_from_start_km': 0.0
        })

        next_waypoint_m = interval_m

        for i in range(1, len(trackpoints)):
            prev = trackpoints[i - 1]
            curr = trackpoints[i]

            segment_distance = haversine_distance(
                prev['lat'], prev['lng'],
                curr['lat'], curr['lng']
            )
            cumulative_distance_m += segment_distance

            while cumulative_distance_m >= next_waypoint_m:
                waypoints.append({
                    'lat': curr['lat'],
                    'lng': curr['lng'],
                    'distance_from_start_km': m_to_km_round(next_waypoint_m)
                })
                next_waypoint_m += interval_m

        last_distance = m_to_km_round(cumulative_distance_m)
        if waypoints[-1]['distance_from_start_km'] < last_distance:
            waypoints.append({
                'lat': trackpoints[-1]['lat'],
                'lng': trackpoints[-1]['lng'],
                'distance_from_start_km': last_distance
            })

        return waypoints

    def inject_borders_and_geocode(
            self,
            waypoints: List[Dict],
            trackpoints: List[Dict],
            geocode_func: Callable[[float, float], Optional[str]]
    ) -> List[Dict]:
        if not waypoints or not trackpoints:
            return waypoints

        enhanced_waypoints = []

        prev_wp = waypoints[0]
        prev_country = geocode_func(prev_wp['lat'], prev_wp['lng'])
        prev_wp['country_code'] = prev_country
        enhanced_waypoints.append(prev_wp)

        for i in range(1, len(waypoints)):
            curr_wp = waypoints[i]
            curr_country = geocode_func(curr_wp['lat'], curr_wp['lng'])
            curr_wp['country_code'] = curr_country

            if curr_country and prev_country and curr_country != prev_country:
                border_wp = self._binary_search_border(
                    prev_wp, curr_wp, prev_country, curr_country,
                    trackpoints, geocode_func
                )
                if border_wp:
                    enhanced_waypoints.append(border_wp)

            enhanced_waypoints.append(curr_wp)
            prev_wp = curr_wp
            prev_country = curr_country

        return enhanced_waypoints

    @staticmethod
    def _binary_search_border(
            wp_a: Dict,
            wp_b: Dict,
            country_a: str,
            country_b: str,
            trackpoints: List[Dict],
            geocode_func: Callable[[float, float], Optional[str]]
    ) -> Optional[Dict]:
        """
        Binary search on dense trackpoints to find the exact border crossing.
        """
        dist_a = wp_a.get('distance_from_start_km', 0.0)
        dist_b = wp_b.get('distance_from_start_km', 0.0)

        segment = [
            tp for tp in trackpoints
            if dist_a <= tp.get('distance_from_start_km', 0.0) <= dist_b
        ]

        if not segment:
            return None

        left, right = 0, len(segment) - 1
        border_idx = right

        while left <= right:
            mid = (left + right) // 2
            mid_tp = segment[mid]
            mid_country = geocode_func(mid_tp['lat'], mid_tp['lng'])

            if mid_country == country_a:
                left = mid + 1
            else:
                border_idx = mid
                right = mid - 1

        border_tp = segment[border_idx]
        return {
            'lat': border_tp['lat'],
            'lng': border_tp['lng'],
            'distance_from_start_km': border_tp.get('distance_from_start_km', dist_a),
            'country_code': country_b,
            'is_border': True
        }