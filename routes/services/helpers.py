from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.

        Returns:
            Distance in meters
        """
        R = 6371008.8  # Earth radius in meters

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        diff_lat = lat2 - lat1
        diff_lon = lon2 - lon1

        a = sin(diff_lat/2)**2 + cos(lat1) * cos(lat2) * sin(diff_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

def m_to_km_round(m: float) -> float:
    return round(m / 1000, 2)