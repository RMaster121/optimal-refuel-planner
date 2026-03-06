"""
Unit tests for HTMLTableScraper.

Tests:
- HTML parsing
- Country name extraction
- Price extraction
- Missing data handling
- Error cases
"""

import pytest
from unittest.mock import Mock, patch
from fuel_prices.scrapers.html_table_scraper import HTMLTableScraper
from fuel_prices.scrapers.exceptions import ParsingException


class TestHTMLTableScraper:
    """Test suite for HTMLTableScraper class."""
    
    def test_parse_response_success(self, sample_scraper_html):
        """Test successful HTML parsing with sample fixture."""
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        
        mock_response = Mock()
        mock_response.text = sample_scraper_html
        
        results = scraper.parse_response(mock_response)
        
        # Should have 5 countries * 2 fuel types = 10 records
        assert len(results) == 10
        
        # Verify data structure
        assert all(hasattr(r, 'country_name') for r in results)
        assert all(hasattr(r, 'fuel_type') for r in results)
        assert all(hasattr(r, 'price_eur') for r in results)
    
    def test_extract_country_name_poland(self, sample_scraper_html):
        """Test country name extraction for Poland."""
        from bs4 import BeautifulSoup
        
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        soup = BeautifulSoup(sample_scraper_html, 'lxml')
        cells = soup.find_all('td', class_='tara')
        
        # First country should be Poland
        name = scraper._extract_country_name(cells[0])
        assert name == 'Poland'
    
    def test_extract_country_name_germany(self, sample_scraper_html):
        """Test country name extraction for Germany."""
        from bs4 import BeautifulSoup
        
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        soup = BeautifulSoup(sample_scraper_html, 'lxml')
        cells = soup.find_all('td', class_='tara')
        
        # Second country should be Germany
        name = scraper._extract_country_name(cells[1])
        assert name == 'Germany'
    
    def test_extract_country_name_with_nbsp(self):
        """Test that non-breaking spaces are handled correctly."""
        from bs4 import BeautifulSoup
        
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        html = '<td class="tara"><img src="flag.png">&nbsp; Poland</td>'
        cell = BeautifulSoup(html, 'lxml').find('td')
        
        name = scraper._extract_country_name(cell)
        assert name == 'Poland'
        assert '\xa0' not in name  # No nbsp in result
    
    def test_extract_price_valid(self):
        """Test valid price extraction."""
        from bs4 import BeautifulSoup
        
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        cell = BeautifulSoup('<td>1.397</td>', 'lxml').find('td')
        
        price = scraper._extract_price(cell)
        assert price == 1.397
    
    def test_extract_price_with_comma(self):
        """Test price extraction with comma decimal separator."""
        from bs4 import BeautifulSoup
        
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        cell = BeautifulSoup('<td>1,397</td>', 'lxml').find('td')
        
        price = scraper._extract_price(cell)
        assert price == 1.397
    
    def test_extract_price_missing_dash(self):
        """Test missing price extraction (dash indicator)."""
        from bs4 import BeautifulSoup
        
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        cell = BeautifulSoup('<td>–</td>', 'lxml').find('td')
        
        price = scraper._extract_price(cell)
        assert price is None
    
    def test_extract_price_missing_na(self):
        """Test missing price extraction (N/A indicator)."""
        from bs4 import BeautifulSoup
        
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        cell = BeautifulSoup('<td>N/A</td>', 'lxml').find('td')
        
        price = scraper._extract_price(cell)
        assert price is None
    
    def test_extract_price_empty(self):
        """Test missing price extraction (empty cell)."""
        from bs4 import BeautifulSoup
        
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        cell = BeautifulSoup('<td></td>', 'lxml').find('td')
        
        price = scraper._extract_price(cell)
        assert price is None
    
    def test_extract_price_invalid_format(self):
        """Test invalid price format raises ValueError."""
        from bs4 import BeautifulSoup
        
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        cell = BeautifulSoup('<td>abc</td>', 'lxml').find('td')
        
        with pytest.raises(ValueError, match='Invalid price format'):
            scraper._extract_price(cell)
    
    def test_extract_price_negative(self):
        """Test negative price raises ValueError."""
        from bs4 import BeautifulSoup
        
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        cell = BeautifulSoup('<td>-1.5</td>', 'lxml').find('td')
        
        with pytest.raises(ValueError):
            scraper._extract_price(cell)
    
    def test_extract_price_zero(self):
        """Test zero price raises ValueError."""
        from bs4 import BeautifulSoup
        
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        cell = BeautifulSoup('<td>0</td>', 'lxml').find('td')
        
        with pytest.raises(ValueError):
            scraper._extract_price(cell)
    
    def test_validate_response_success(self):
        """Test response validation with valid response."""
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        
        response = Mock()
        response.status_code = 200
        response.text = '<html><table></table></html>'
        
        assert scraper.validate_response(response) is True
    
    def test_validate_response_no_table(self):
        """Test response validation without table."""
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        
        response = Mock()
        response.status_code = 200
        response.text = '<html><div>No table here</div></html>'
        
        assert scraper.validate_response(response) is False
    
    def test_validate_response_error_status(self):
        """Test response validation with error status code."""
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        
        response = Mock()
        response.status_code = 404
        response.text = '<html><table></table></html>'
        
        assert scraper.validate_response(response) is False
    
    def test_parse_response_no_table(self):
        """Test parsing raises exception when table not found."""
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        
        response = Mock()
        response.text = '<html><div>No table</div></html>'
        
        with pytest.raises(ParsingException, match='Table not found'):
            scraper.parse_response(response)
    
    def test_parse_response_with_missing_prices(self, sample_scraper_html):
        """Test parsing handles missing prices correctly."""
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        
        response = Mock()
        response.text = sample_scraper_html
        
        results = scraper.parse_response(response)
        
        # Austria has missing diesel (–)
        austria_diesel = [
            r for r in results 
            if r.country_name == 'Austria' and r.fuel_type == 'diesel'
        ]
        assert len(austria_diesel) == 1
        assert austria_diesel[0].price_eur is None
        
        # France has missing gasoline (–)
        france_gasoline = [
            r for r in results 
            if r.country_name == 'France' and r.fuel_type == 'gasoline'
        ]
        assert len(france_gasoline) == 1
        assert france_gasoline[0].price_eur is None
    
    def test_parse_response_country_code_initially_none(self, sample_scraper_html):
        """Test that country_code is None after parsing (before mapping)."""
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        
        response = Mock()
        response.text = sample_scraper_html
        
        results = scraper.parse_response(response)
        
        # All country codes should be None (mapping happens later)
        assert all(r.country_code is None for r in results)
    
    def test_parse_response_fuel_types(self, sample_scraper_html):
        """Test that only gasoline and diesel are extracted."""
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        
        response = Mock()
        response.text = sample_scraper_html
        
        results = scraper.parse_response(response)
        
        fuel_types = {r.fuel_type for r in results}
        assert fuel_types == {'gasoline', 'diesel'}
        # LPG should not be included
        assert 'lpg' not in fuel_types
    
    @patch('requests.Session.get')
    def test_scrape_integration(self, mock_get, sample_scraper_html):
        """Test complete scrape workflow."""
        scraper = HTMLTableScraper(source_url='http://example.com/prices')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_scraper_html
        mock_response.content = sample_scraper_html.encode('utf-8')
        mock_get.return_value = mock_response
        
        results = scraper.scrape()
        
        assert len(results) > 0
        assert all(r.source_url == 'http://example.com/prices' for r in results)
    
    def test_custom_selectors(self):
        """Test scraper accepts custom CSS selectors via kwargs."""
        from fuel_prices.scrapers.config import ScraperConfig
        
        config = ScraperConfig()
        scraper = HTMLTableScraper(
            source_url='http://example.com/prices',
            config=config,
            table_selector='table.custom',
            country_class='country-cell'
        )
        
        assert scraper.table_selector == 'table.custom'
        assert scraper.country_class == 'country-cell'