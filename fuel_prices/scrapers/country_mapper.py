"""
Maps country names from scraped data to ISO 3166-1 alpha-2 codes.
"""

from typing import Optional, Dict
import logging
from difflib import get_close_matches


class CountryMapper:
    """
    Maps country names to ISO codes.
    
    Supports:
    - Exact matching (case-insensitive)
    - Alias resolution
    - Fuzzy matching with confidence threshold
    
    Example:
        mapper = CountryMapper()
        code = mapper.map_to_code("Poland")  # Returns "PL"
        code = mapper.map_to_code("Czechia")  # Returns "CZ" (via alias)
    """
    
    # Primary mapping: canonical name → code
    # Source: ISO 3166-1 alpha-2 standard
    COUNTRY_MAPPING: Dict[str, str] = {
        # Western Europe
        "Austria": "AT",
        "Belgium": "BE",
        "France": "FR",
        "Germany": "DE",
        "Luxembourg": "LU",
        "Netherlands": "NL",
        "Switzerland": "CH",
        
        # Southern Europe
        "Albania": "AL",
        "Andorra": "AD",
        "Bosnia and Herzegovina": "BA",
        "Croatia": "HR",
        "Cyprus": "CY",
        "Greece": "GR",
        "Italy": "IT",
        "Malta": "MT",
        "North Macedonia": "MK",
        "Portugal": "PT",
        "San Marino": "SM",
        "Serbia": "RS",
        "Slovenia": "SI",
        "Spain": "ES",
        
        # Eastern Europe
        "Belarus": "BY",
        "Bulgaria": "BG",
        "Czech Republic": "CZ",
        "Estonia": "EE",
        "Hungary": "HU",
        "Latvia": "LV",
        "Lithuania": "LT",
        "Moldova": "MD",
        "Poland": "PL",
        "Romania": "RO",
        "Russia": "RU",
        "Slovakia": "SK",
        "Ukraine": "UA",
        
        # Northern Europe
        "Denmark": "DK",
        "Finland": "FI",
        "Iceland": "IS",
        "Ireland": "IE",
        "Norway": "NO",
        "Sweden": "SE",
        "United Kingdom": "GB",
        
        # Additional European territories
        "Kosovo": "XK",  # Temporary code
        "Montenegro": "ME",
        "Liechtenstein": "LI",
        "Monaco": "MC",
        "Vatican City": "VA",
        
        # Turkey (transcontinental)
        "Turkey": "TR",
        "Türkiye": "TR",
    }
    
    # Aliases: alternative names → canonical name
    ALIASES: Dict[str, str] = {
        "UK": "United Kingdom",
        "Great Britain": "United Kingdom",
        "England": "United Kingdom",
        "Czechia": "Czech Republic",
        "The Netherlands": "Netherlands",
        "Holland": "Netherlands",
        "Bosnia": "Bosnia and Herzegovina",
        "Macedonia": "North Macedonia",
        "FYROM": "North Macedonia",
        "Turkiye": "Turkey",
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize country mapper.
        
        Args:
            logger: Optional logger instance for logging mapping operations
        """
        self.logger = logger or logging.getLogger(__name__)
        self._normalize_cache: Dict[str, str] = {}
    
    def normalize_name(self, name: str) -> str:
        """
        Normalize country name for matching.
        
        Converts to lowercase and strips whitespace for consistent comparison.
        
        Args:
            name: Country name to normalize
            
        Returns:
            Normalized country name
        """
        return name.strip().lower()
    
    def map_to_code(
        self,
        country_name: str,
        fuzzy_match: bool = True,
        threshold: float = 0.8
    ) -> Optional[str]:
        """
        Map country name to ISO 3166-1 alpha-2 code.
        
        Attempts matching in this order:
        1. Cache lookup (for performance)
        2. Exact match (case-insensitive)
        3. Alias resolution
        4. Fuzzy matching (if enabled)
        
        Args:
            country_name: Country name to map
            fuzzy_match: Enable fuzzy matching for close matches
            threshold: Minimum similarity score for fuzzy match (0-1, default 0.8)
            
        Returns:
            ISO 3166-1 alpha-2 code or None if not found
            
        Example:
            >>> mapper = CountryMapper()
            >>> mapper.map_to_code("Poland")
            'PL'
            >>> mapper.map_to_code("Czechia")
            'CZ'
            >>> mapper.map_to_code("Unknown Country")
            None
        """
        if not country_name:
            return None
        
        normalized = self.normalize_name(country_name)
        
        # Check cache first for performance
        if normalized in self._normalize_cache:
            return self._normalize_cache[normalized]
        
        # Try exact match
        code = self._exact_match(country_name)
        if code:
            self._normalize_cache[normalized] = code
            return code
        
        # Try alias resolution
        code = self._alias_match(country_name)
        if code:
            self._normalize_cache[normalized] = code
            self.logger.debug(f"Resolved alias '{country_name}' to code {code}")
            return code
        
        # Try fuzzy match if enabled
        if fuzzy_match:
            code = self._fuzzy_match(country_name, threshold)
            if code:
                self._normalize_cache[normalized] = code
                self.logger.info(f"Fuzzy matched '{country_name}' to code {code}")
                return code
        
        # Not found
        self.logger.warning(f"Could not map country name to code: '{country_name}'")
        return None
    
    def _exact_match(self, name: str) -> Optional[str]:
        """
        Case-insensitive exact match against canonical names.
        
        Args:
            name: Country name to match
            
        Returns:
            ISO code if found, None otherwise
        """
        normalized = self.normalize_name(name)
        
        for canonical_name, code in self.COUNTRY_MAPPING.items():
            if self.normalize_name(canonical_name) == normalized:
                return code
        
        return None
    
    def _alias_match(self, name: str) -> Optional[str]:
        """
        Match through alias resolution.
        
        Args:
            name: Country name to match
            
        Returns:
            ISO code if alias found, None otherwise
        """
        normalized = self.normalize_name(name)
        
        for alias, canonical in self.ALIASES.items():
            if self.normalize_name(alias) == normalized:
                return self.COUNTRY_MAPPING.get(canonical)
        
        return None
    
    def _fuzzy_match(self, name: str, threshold: float) -> Optional[str]:
        """
        Fuzzy string matching for close matches.
        
        Uses Python's difflib to find similar strings based on sequence matching.
        Only returns a match if similarity exceeds the threshold.
        
        Args:
            name: Country name to match
            threshold: Minimum similarity score (0-1)
            
        Returns:
            ISO code if close match found, None otherwise
        """
        all_names = list(self.COUNTRY_MAPPING.keys()) + list(self.ALIASES.keys())
        
        # Find closest match
        matches = get_close_matches(name, all_names, n=1, cutoff=threshold)
        
        if matches:
            matched_name = matches[0]
            
            # Check if matched name is an alias
            if matched_name in self.ALIASES:
                canonical = self.ALIASES[matched_name]
                return self.COUNTRY_MAPPING.get(canonical)
            
            return self.COUNTRY_MAPPING.get(matched_name)
        
        return None
    
    def get_all_codes(self) -> list:
        """
        Return all supported country codes.
        
        Returns:
            List of ISO 3166-1 alpha-2 codes
        """
        return list(self.COUNTRY_MAPPING.values())
    
    def get_canonical_name(self, code: str) -> Optional[str]:
        """
        Reverse lookup: code → canonical name.
        
        Args:
            code: ISO 3166-1 alpha-2 code
            
        Returns:
            Canonical country name or None if code not found
            
        Example:
            >>> mapper = CountryMapper()
            >>> mapper.get_canonical_name("PL")
            'Poland'
        """
        code = code.upper()
        for name, c in self.COUNTRY_MAPPING.items():
            if c == code:
                return name
        return None
    
    def get_mapping_stats(self) -> Dict[str, int]:
        """
        Get statistics about country mappings.
        
        Returns:
            Dictionary with mapping statistics:
            - total_countries: Total number of mapped countries
            - total_aliases: Total number of aliases
            - cache_size: Number of cached lookups
        """
        return {
            'total_countries': len(self.COUNTRY_MAPPING),
            'total_aliases': len(self.ALIASES),
            'cache_size': len(self._normalize_cache),
        }