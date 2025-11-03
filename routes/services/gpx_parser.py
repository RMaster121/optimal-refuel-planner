"""
Parse GPX files to extract route information.

Distance calculations track the actual driven path, essential for fuel consumption.
Waypoint intervals balance performance vs accuracy:
- 50km default: Optimal for most European routes, all borders detected
- 25km optional: For small countries (Luxembourg, Liechtenstein) or complex tri-border areas
"""

from math import radians, sin, cos, sqrt, atan2
from typing import Dict, List

import gpxpy

from routes.exceptions import InvalidGPXFileError


class GPXParser:
    """Parse GPX files to extract route information."""

    def parse_gpx_file(self, gpx_file) -> Dict:
        """
        Parse uploaded GPX file.

        Args:
            gpx_file: File object from Django request.FILES

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

            for i in range(1, len(trackpoints)):
                prev = trackpoints[i-1]
                curr = trackpoints[i]
                total_distance += self._haversine_distance(
                    prev['lat'], prev['lng'],
                    curr['lat'], curr['lng']
                )

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

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Returns:
            Distance in meters
        """
        R = 6371008.8  # Earth radius in meters

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def generate_waypoints(self, trackpoints: List[Dict], interval_km: int = 50) -> List[Dict]:
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
            prev = trackpoints[i-1]
            curr = trackpoints[i]

            segment_distance = self._haversine_distance(
                prev['lat'], prev['lng'],
                curr['lat'], curr['lng']
            )
            cumulative_distance_m += segment_distance

            while cumulative_distance_m >= next_waypoint_m:
                waypoints.append({
                    'lat': curr['lat'],
                    'lng': curr['lng'],
                    'distance_from_start_km': round(next_waypoint_m / 1000, 2)
                })
                next_waypoint_m += interval_m

        last_distance = round(cumulative_distance_m / 1000, 2)
        if waypoints[-1]['distance_from_start_km'] < last_distance:
            waypoints.append({
                'lat': trackpoints[-1]['lat'],
                'lng': trackpoints[-1]['lng'],
                'distance_from_start_km': last_distance
            })

        return waypoints