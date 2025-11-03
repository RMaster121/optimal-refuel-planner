"""Offline country boundary detection using Natural Earth data."""

import os
from typing import Dict

import geopandas as gpd
from django.conf import settings
from shapely.geometry import Point

from routes.exceptions import GeocodingError


class OfflineGeocoder:
    """
    Offline country boundary detection using Natural Earth shapefile data.
    
    Uses Natural Earth's ISO_A2 field which contains ISO 3166-1 alpha-2 codes,
    compatible with our Country model's code field.
    
    Note: Natural Earth distinguishes between metropolitan (homeland) and 
    dependent/semi-independent portions. For most European routes, this provides
    accurate country detection using standard ISO codes.
    """

    _world_data = None

    def __init__(self):
        if OfflineGeocoder._world_data is None:
            self._load_boundaries()

    def _load_boundaries(self):
        """Load Natural Earth shapefile data once and cache."""
        try:
            data_path = os.path.join(
                settings.BASE_DIR,
                'routes', 'data', 'natural_earth',
                'ne_10m_admin_0_countries.shp'
            )

            if not os.path.exists(data_path):
                raise FileNotFoundError(
                    f"Natural Earth data not found at {data_path}. "
                )

            OfflineGeocoder._world_data = gpd.read_file(data_path)

        except Exception as e:
            raise GeocodingError(f"Failed to load Natural Earth data: {str(e)}")

    def get_country(self, lat: float, lng: float) -> Dict[str, str]:
        """
        Get country for given coordinates using offline boundary data.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            dict with 'country_code' (ISO 3166-1 alpha-2) and 'country_name'

        Raises:
            GeocodingError: If lookup fails or point not in any country
        """
        try:
            point = Point(lng, lat)

            mask = OfflineGeocoder._world_data.contains(point)
            country = OfflineGeocoder._world_data[mask]

            if not country.empty:
                row = country.iloc[0]
                country_code = row['ISO_A2']
                
                # Natural Earth uses '-99' for countries with complex sovereignty
                # (e.g., France with overseas territories). Use ISO_A2_EH as fallback.
                if country_code == '-99':
                    country_code = row.get('ISO_A2_EH', '-99')
                    
                if country_code == '-99' or not country_code:
                    raise GeocodingError(
                        f"No valid ISO country code for coordinates ({lat}, {lng})"
                    )
                
                return {
                    'country_code': country_code.upper(),
                    'country_name': row['NAME']
                }
            else:
                raise GeocodingError(
                    f"No country found for coordinates ({lat}, {lng})"
                )

        except Exception as e:
            if isinstance(e, GeocodingError):
                raise
            raise GeocodingError(f"Country lookup failed: {str(e)}")