"""
HTML Table scraper for European fuel prices.

Scrapes fuel price data from HTML table format with structure:
<tr>
    <td class="tara"><img>Country Name</td>
    <td>Gasoline Price</td>
    <td>Diesel Price</td>
</tr>
"""

from bs4 import BeautifulSoup
from decimal import Decimal, InvalidOperation
from typing import List, Optional
from django.utils import timezone

from .base import BaseScraper, ScrapedFuelPrice
from .exceptions import ParsingException


class HTMLTableScraper(BaseScraper):
    """
    Scraper for HTML table-based fuel price sources.
    
    This scraper is designed to parse HTML tables containing fuel price data
    with country names in the first column and prices in subsequent columns.
    
    Configuration:
        - source_url: URL of the HTML page
        - table_selector: CSS selector for table (default: "table")
        - row_selector: CSS selector for data rows (default: "tr")
        - country_class: CSS class for country cell (default: "tara")
        
    Expected HTML Structure:
        <table>
            <tr>
                <td class="tara"><img>Country Name</td>
                <td>Gasoline Price</td>
                <td>Diesel Price</td>
                <td>LPG Price</td>
            </tr>
        </table>
    """
    
    # Column mapping: (index, fuel_type)
    # Note: LPG is column 3 but we only scrape gasoline and diesel
    COLUMN_MAPPING = [
        (1, "gasoline"),  # Euro 95
        (2, "diesel"),
    ]
    
    # Indicators of missing price data
    MISSING_PRICE_INDICATORS = ["–", "-", "N/A", "n/a", ""]
    
    def __init__(self, source_url: str, config=None, logger=None, **kwargs):
        """
        Initialize HTML table scraper.
        
        Args:
            source_url: URL to scrape
            config: Optional ScraperConfig instance
            logger: Optional logger instance
            **kwargs: Additional configuration options:
                - table_selector: CSS selector for table
                - row_selector: CSS selector for rows
                - country_class: CSS class for country cells
        """
        # Extract scraper-specific kwargs before passing to parent
        self.table_selector = kwargs.pop('table_selector', 'table')
        self.row_selector = kwargs.pop('row_selector', 'tr')
        self.country_class = kwargs.pop('country_class', 'tara')
        
        # Now pass only config and logger to parent
        super().__init__(source_url, config=config, logger=logger)
    
    def validate_response(self, response) -> bool:
        """
        Validate that response contains expected HTML structure.
        
        Args:
            response: HTTP response object
            
        Returns:
            True if response appears valid, False otherwise
        """
        if response.status_code != 200:
            self.logger.warning(f"Invalid status code: {response.status_code}")
            return False
        
        # Quick check for table presence
        if '<table' not in response.text.lower():
            self.logger.warning("No <table> tag found in response")
            return False
        
        return True
    
    def scrape(self) -> List[ScrapedFuelPrice]:
        """
        Main scraping workflow.
        
        Returns:
            List of ScrapedFuelPrice objects
            
        Raises:
            ParsingException: If HTML parsing fails
        """
        response = self.fetch()
        return self.parse_response(response)
    
    def parse_response(self, response) -> List[ScrapedFuelPrice]:
        """
        Parse HTTP response into structured data.
        
        Args:
            response: HTTP response object with HTML content
            
        Returns:
            List of ScrapedFuelPrice objects
            
        Raises:
            ParsingException: If HTML parsing fails
        """
        try:
            soup = BeautifulSoup(response.text, 'lxml')
            table = soup.select_one(self.table_selector)
            
            if not table:
                raise ParsingException(
                    f"Table not found with selector: {self.table_selector}"
                )
            
            rows = table.find_all(self.row_selector)
            scraped_prices = []
            now = timezone.now()
            
            self.logger.info(f"Found {len(rows)} rows in table")
            
            for row_idx, row in enumerate(rows):
                try:
                    cells = row.find_all('td')
                    
                    # Skip rows without enough cells (header rows, etc.)
                    if not cells or len(cells) < 3:
                        self.logger.debug(f"Row {row_idx}: Skipping (insufficient cells)")
                        continue
                    
                    # Extract country name from first cell
                    country_cell = cells[0]
                    country_name = self._extract_country_name(country_cell)
                    
                    if not country_name:
                        self.logger.warning(
                            f"Row {row_idx}: Could not extract country name"
                        )
                        continue
                    
                    # Extract prices for each fuel type
                    for col_idx, fuel_type in self.COLUMN_MAPPING:
                        try:
                            if col_idx >= len(cells):
                                self.logger.warning(
                                    f"Row {row_idx}: Column {col_idx} not found for {fuel_type}"
                                )
                                continue
                            
                            price = self._extract_price(cells[col_idx])
                            
                            scraped_prices.append(ScrapedFuelPrice(
                                country_name=country_name,
                                country_code=None,  # Will be mapped later
                                fuel_type=fuel_type,
                                price_eur=price,
                                scraped_at=now,
                                source_url=self.source_url
                            ))
                            
                        except ValueError as e:
                            self.logger.warning(
                                f"Row {row_idx}, {country_name}, {fuel_type}: "
                                f"Failed to extract price: {e}"
                            )
                            # Still append with None price to track missing data
                            scraped_prices.append(ScrapedFuelPrice(
                                country_name=country_name,
                                country_code=None,
                                fuel_type=fuel_type,
                                price_eur=None,
                                scraped_at=now,
                                source_url=self.source_url
                            ))
                            
                except Exception as e:
                    self.logger.error(
                        f"Row {row_idx}: Unexpected error: {e}",
                        exc_info=True
                    )
                    continue
            
            self.logger.info(
                f"Parsed {len(scraped_prices)} fuel price records from HTML"
            )
            return scraped_prices
            
        except Exception as e:
            self.logger.error(f"HTML parsing failed: {e}", exc_info=True)
            raise ParsingException(f"Failed to parse HTML: {e}") from e
    
    def _extract_country_name(self, cell) -> Optional[str]:
        """
        Extract country name from table cell.
        
        Expected format:
        <td class="tara"><img...>&nbsp; Poland</td>
        
        The method removes all <img> tags and extracts the remaining text,
        cleaning up whitespace and non-breaking spaces.
        
        Args:
            cell: BeautifulSoup Tag object
            
        Returns:
            Cleaned country name or None if extraction fails
        """
        try:
            # Get text content, which automatically excludes img tags' content
            text = cell.get_text(strip=True)
            
            # Replace non-breaking space
            text = text.replace('\xa0', ' ')
            # Replace multiple spaces with single space
            text = ' '.join(text.split())
            text = text.strip()
            
            return text if text else None
            
        except Exception as e:
            self.logger.error(f"Failed to extract country name: {e}")
            return None
    
    def _extract_price(self, cell) -> Optional[float]:
        """
        Extract price from table cell.
        
        Handles:
        - Valid decimal prices (e.g., "1.397")
        - European decimal format with comma (e.g., "1,397")
        - Missing price indicators (e.g., "–", "N/A")
        
        Args:
            cell: BeautifulSoup Tag object
            
        Returns:
            Price as float or None if missing
            
        Raises:
            ValueError: If price format is invalid
        """
        text = cell.get_text(strip=True)
        
        # Check for missing price indicators
        if text in self.MISSING_PRICE_INDICATORS:
            return None
        
        try:
            # Convert to float, handle European decimal format
            # Replace comma with period for decimal separator
            price_str = text.replace(',', '.')
            price = float(price_str)
            
            if price <= 0:
                raise ValueError(f"Price must be positive, got: {price}")
            
            return price
            
        except (ValueError, InvalidOperation) as e:
            raise ValueError(f"Invalid price format: '{text}'") from e