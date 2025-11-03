"""Tests for offline geocoder service."""

import pytest

from routes.exceptions import GeocodingError
from routes.services.offline_geocoder import OfflineGeocoder


@pytest.mark.django_db
class TestOfflineGeocoder:
    """Test suite for OfflineGeocoder."""

    def test_get_country_for_warsaw(self):
        """Test country detection for Warsaw, Poland coordinates."""
        geocoder = OfflineGeocoder()
        result = geocoder.get_country(52.2297, 21.0122)

        assert result['country_code'] == 'PL'
        assert result['country_name'] == 'Poland'

    def test_get_country_for_berlin(self):
        """Test country detection for Berlin, Germany coordinates."""
        geocoder = OfflineGeocoder()
        result = geocoder.get_country(52.5200, 13.4050)

        assert result['country_code'] == 'DE'
        assert result['country_name'] == 'Germany'

    def test_get_country_for_paris(self):
        """Test country detection for Paris, France coordinates."""
        geocoder = OfflineGeocoder()
        result = geocoder.get_country(48.8566, 2.3522)

        assert result['country_code'] == 'FR'
        assert result['country_name'] == 'France'

    def test_get_country_ocean_raises_error(self):
        """Test that coordinates in ocean raise GeocodingError."""
        geocoder = OfflineGeocoder()
        
        # Middle of Atlantic Ocean
        with pytest.raises(GeocodingError, match="No country found"):
            geocoder.get_country(0.0, -30.0)

    def test_get_country_invalid_coordinates_raises_error(self):
        """Test that invalid coordinates raise GeocodingError."""
        geocoder = OfflineGeocoder()
        
        # Invalid latitude (> 90)
        with pytest.raises(GeocodingError):
            geocoder.get_country(100.0, 0.0)

    def test_country_code_is_uppercase(self):
        """Test that country codes are returned in uppercase."""
        geocoder = OfflineGeocoder()
        result = geocoder.get_country(52.2297, 21.0122)

        assert result['country_code'].isupper()
        assert len(result['country_code']) == 2

    def test_geocoder_caching(self):
        """Test that geocoder caches Natural Earth data."""
        geocoder1 = OfflineGeocoder()
        geocoder2 = OfflineGeocoder()

        # Both should use the same cached data
        assert OfflineGeocoder._world_data is not None
        assert geocoder1._world_data is geocoder2._world_data

    def test_multiple_lookups_with_same_geocoder(self):
        """Test multiple country lookups with same geocoder instance."""
        geocoder = OfflineGeocoder()
        
        pl_result = geocoder.get_country(52.2297, 21.0122)
        de_result = geocoder.get_country(52.5200, 13.4050)
        fr_result = geocoder.get_country(48.8566, 2.3522)

        assert pl_result['country_code'] == 'PL'
        assert de_result['country_code'] == 'DE'
        assert fr_result['country_code'] == 'FR'