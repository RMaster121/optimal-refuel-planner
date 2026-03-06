"""
Unit tests for CountryMapper.

Tests:
- Exact matching (case-insensitive)
- Alias resolution
- Fuzzy matching
- Invalid country handling
- Cache functionality
"""

import pytest
from fuel_prices.scrapers.country_mapper import CountryMapper


class TestCountryMapper:
    """Test suite for CountryMapper class."""
    
    def test_exact_match_poland(self):
        """Test exact match for Poland."""
        mapper = CountryMapper()
        code = mapper.map_to_code('Poland')
        assert code == 'PL'
    
    def test_exact_match_case_insensitive(self):
        """Test case-insensitive matching."""
        mapper = CountryMapper()
        assert mapper.map_to_code('poland') == 'PL'
        assert mapper.map_to_code('POLAND') == 'PL'
        assert mapper.map_to_code('PoLaNd') == 'PL'
    
    def test_exact_match_germany(self):
        """Test exact match for Germany."""
        mapper = CountryMapper()
        code = mapper.map_to_code('Germany')
        assert code == 'DE'
    
    def test_alias_czechia(self):
        """Test alias resolution for Czechia → Czech Republic."""
        mapper = CountryMapper()
        code = mapper.map_to_code('Czechia')
        assert code == 'CZ'
    
    def test_alias_uk(self):
        """Test alias resolution for UK → United Kingdom."""
        mapper = CountryMapper()
        assert mapper.map_to_code('UK') == 'GB'
        assert mapper.map_to_code('Great Britain') == 'GB'
        assert mapper.map_to_code('England') == 'GB'
    
    def test_alias_netherlands(self):
        """Test alias resolution for Netherlands variations."""
        mapper = CountryMapper()
        assert mapper.map_to_code('The Netherlands') == 'NL'
        assert mapper.map_to_code('Holland') == 'NL'
        assert mapper.map_to_code('Netherlands') == 'NL'
    
    def test_fuzzy_match_enabled(self):
        """Test fuzzy matching with typos."""
        mapper = CountryMapper()
        # Should match despite typo
        code = mapper.map_to_code('Polandd', fuzzy_match=True)
        assert code == 'PL'
    
    def test_fuzzy_match_disabled(self):
        """Test that fuzzy matching can be disabled."""
        mapper = CountryMapper()
        code = mapper.map_to_code('Polandd', fuzzy_match=False)
        assert code is None
    
    def test_fuzzy_match_threshold(self):
        """Test fuzzy matching respects threshold."""
        mapper = CountryMapper()
        # High threshold - should not match
        code = mapper.map_to_code('Polan', fuzzy_match=True, threshold=0.95)
        assert code is None
        
        # Lower threshold - should match
        code = mapper.map_to_code('Polan', fuzzy_match=True, threshold=0.7)
        assert code == 'PL'
    
    def test_unmapped_country(self):
        """Test handling of unmapped country."""
        mapper = CountryMapper()
        code = mapper.map_to_code('Atlantis')
        assert code is None
    
    def test_empty_string(self):
        """Test handling of empty string."""
        mapper = CountryMapper()
        code = mapper.map_to_code('')
        assert code is None
    
    def test_none_input(self):
        """Test handling of None input."""
        mapper = CountryMapper()
        code = mapper.map_to_code(None)
        assert code is None
    
    def test_whitespace_handling(self):
        """Test whitespace normalization."""
        mapper = CountryMapper()
        assert mapper.map_to_code('  Poland  ') == 'PL'
        assert mapper.map_to_code('Poland\t') == 'PL'
        assert mapper.map_to_code('\nPoland\n') == 'PL'
    
    def test_cache_functionality(self):
        """Test that cache is used for repeated lookups."""
        mapper = CountryMapper()
        
        # First lookup
        code1 = mapper.map_to_code('Poland')
        assert code1 == 'PL'
        
        # Check cache was populated
        assert 'poland' in mapper._normalize_cache
        
        # Second lookup should use cache
        code2 = mapper.map_to_code('Poland')
        assert code2 == 'PL'
    
    def test_get_canonical_name(self):
        """Test reverse lookup from code to name."""
        mapper = CountryMapper()
        
        assert mapper.get_canonical_name('PL') == 'Poland'
        assert mapper.get_canonical_name('DE') == 'Germany'
        assert mapper.get_canonical_name('CZ') == 'Czech Republic'
        
        # Case insensitive
        assert mapper.get_canonical_name('pl') == 'Poland'
    
    def test_get_canonical_name_invalid(self):
        """Test reverse lookup with invalid code."""
        mapper = CountryMapper()
        assert mapper.get_canonical_name('XX') is None
    
    def test_get_all_codes(self):
        """Test getting all supported codes."""
        mapper = CountryMapper()
        codes = mapper.get_all_codes()
        
        assert isinstance(codes, list)
        assert 'PL' in codes
        assert 'DE' in codes
        assert 'CZ' in codes
        assert len(codes) > 40  # Should have 40+ countries
    
    def test_get_mapping_stats(self):
        """Test getting mapping statistics."""
        mapper = CountryMapper()
        
        # Before any lookups
        stats = mapper.get_mapping_stats()
        assert stats['cache_size'] == 0
        assert stats['total_countries'] > 40
        assert stats['total_aliases'] > 5
        
        # After some lookups
        mapper.map_to_code('Poland')
        mapper.map_to_code('Germany')
        
        stats = mapper.get_mapping_stats()
        assert stats['cache_size'] == 2
    
    def test_all_european_countries(self):
        """Test mapping for all expected European countries."""
        mapper = CountryMapper()
        
        expected_mappings = {
            'Poland': 'PL',
            'Germany': 'DE',
            'France': 'FR',
            'Spain': 'ES',
            'Italy': 'IT',
            'Austria': 'AT',
            'Belgium': 'BE',
            'Netherlands': 'NL',
            'Switzerland': 'CH',
            'Denmark': 'DK',
            'Sweden': 'SE',
            'Norway': 'NO',
            'Finland': 'FI',
            'Czech Republic': 'CZ',
            'Slovakia': 'SK',
            'Hungary': 'HU',
            'Romania': 'RO',
            'Bulgaria': 'BG',
            'Croatia': 'HR',
            'Slovenia': 'SI',
            'Greece': 'GR',
            'Portugal': 'PT',
        }
        
        for country, expected_code in expected_mappings.items():
            code = mapper.map_to_code(country)
            assert code == expected_code, f"Failed for {country}"
    
    def test_normalize_name(self):
        """Test name normalization."""
        mapper = CountryMapper()
        
        assert mapper.normalize_name('Poland') == 'poland'
        assert mapper.normalize_name('  POLAND  ') == 'poland'
        assert mapper.normalize_name('PoLaNd') == 'poland'