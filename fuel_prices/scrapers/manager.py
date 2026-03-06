"""
Orchestrates the complete fuel price scraping workflow.

Workflow:
1. Initialize scraper
2. Fetch and parse data
3. Map country names to codes
4. Validate data
5. Load into database
6. Report results
"""

from typing import List, Dict, Type, Optional, Any
import logging

from .base import BaseScraper, ScrapedFuelPrice
from .html_table_scraper import HTMLTableScraper
from .country_mapper import CountryMapper
from .validators import FuelPriceValidator
from .data_loader import FuelPriceLoader
from .exceptions import ScraperException


class ScraperManager:
    """
    Manages the complete scraping workflow.
    
    This manager coordinates all components of the scraping system:
    - Initializes and runs scrapers
    - Maps country names to ISO codes
    - Validates scraped data
    - Loads data into database
    - Generates execution reports
    
    The manager handles the entire pipeline in a controlled manner,
    with comprehensive error handling and logging at each stage.
    
    Example:
        manager = ScraperManager()
        report = manager.run_scraping(
            source_url='https://example.com/prices',
            auto_create_countries=True
        )
        if report['success']:
            print(f"Loaded {report['loaded_stats']['created']} prices")
    """
    
    def __init__(
        self,
        scraper_class: Type[BaseScraper] = HTMLTableScraper,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize scraper manager.
        
        Args:
            scraper_class: Scraper class to use (default: HTMLTableScraper)
            logger: Optional logger instance. If None, creates logger for this module.
        """
        self.scraper_class = scraper_class
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize components
        self.mapper = CountryMapper(logger=self.logger)
        self.validator = FuelPriceValidator()
        self.loader = FuelPriceLoader(logger=self.logger)
    
    def run_scraping(
        self,
        source_url: str,
        auto_create_countries: bool = True,
        **scraper_kwargs
    ) -> Dict[str, Any]:
        """
        Execute complete scraping workflow.
        
        This method orchestrates all steps of the scraping process:
        1. Scrape data from source
        2. Map country names to ISO codes
        3. Validate scraped data
        4. Load valid data into database
        
        Args:
            source_url: URL to scrape data from
            auto_create_countries: If True, automatically create missing
                                  Country records in database
            **scraper_kwargs: Additional arguments passed to scraper constructor
            
        Returns:
            Report dictionary with execution statistics and results:
                - success (bool): Whether workflow completed successfully
                - scraped_count (int): Total records scraped
                - mapped_count (int): Records successfully mapped to countries
                - valid_count (int): Records passing validation
                - loaded_stats (dict): Database loading statistics
                - errors (list): List of error messages if any
                
        Example:
            >>> manager = ScraperManager()
            >>> report = manager.run_scraping('https://example.com/prices')
            >>> if report['success']:
            ...     print(f"Loaded {report['valid_count']} valid records")
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Fuel Price Scraping Workflow")
        self.logger.info("=" * 60)
        
        report = {
            'success': False,
            'scraped_count': 0,
            'mapped_count': 0,
            'valid_count': 0,
            'loaded_stats': {},
            'errors': [],
        }
        
        try:
            # Step 1: Scrape data
            self.logger.info("Step 1: Scraping data from source...")
            scraper = self._create_scraper(source_url, **scraper_kwargs)
            scraped_data = scraper.run()
            report['scraped_count'] = len(scraped_data)
            
            if not scraped_data:
                self.logger.warning("No data scraped. Aborting workflow.")
                report['errors'].append("No data scraped from source")
                return report
            
            self.logger.info(f"Successfully scraped {len(scraped_data)} records")
            
            # Step 2: Map countries
            self.logger.info("Step 2: Mapping country names to ISO codes...")
            mapped_data = self._map_countries(scraped_data)
            report['mapped_count'] = len(mapped_data)
            
            if not mapped_data:
                self.logger.error("No countries could be mapped. Aborting workflow.")
                report['errors'].append("Country mapping failed for all records")
                return report
            
            self.logger.info(f"Successfully mapped {len(mapped_data)} countries")
            
            # Step 3: Validate data
            self.logger.info("Step 3: Validating scraped data...")
            valid_data, invalid_data = self.validator.validate_batch(mapped_data)
            report['valid_count'] = len(valid_data)
            
            if invalid_data:
                self.logger.warning(f"Found {len(invalid_data)} invalid records")
                # Log first 5 invalid records for debugging
                for data, errors in invalid_data[:5]:
                    self.logger.warning(
                        f"Invalid: {data.country_name} {data.fuel_type} - {errors}"
                    )
            
            if not valid_data:
                self.logger.error("No valid data to load. Aborting workflow.")
                report['errors'].append("All records failed validation")
                return report
            
            self.logger.info(f"{len(valid_data)} records passed validation")
            
            # Step 4: Load into database
            self.logger.info("Step 4: Loading data into database...")
            load_stats = self.loader.load_batch(valid_data, auto_create_countries)
            report['loaded_stats'] = load_stats
            
            # Check if any data was actually loaded
            if load_stats['created'] == 0 and load_stats['updated'] == 0:
                self.logger.warning(
                    "No records were created or updated. "
                    f"Skipped: {load_stats['skipped']}, Errors: {load_stats['errors']}"
                )
            
            report['success'] = True
            self.logger.info("Workflow completed successfully")
            
        except ScraperException as e:
            self.logger.error(f"Scraping failed: {e}", exc_info=True)
            report['errors'].append(f"Scraper error: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Unexpected error during workflow: {e}", exc_info=True)
            report['errors'].append(f"Unexpected error: {str(e)}")
        
        finally:
            self._log_report(report)
        
        return report
    
    def _create_scraper(self, source_url: str, **kwargs) -> BaseScraper:
        """
        Create scraper instance.
        
        Args:
            source_url: URL to scrape
            **kwargs: Additional arguments for scraper
            
        Returns:
            Initialized scraper instance
        """
        return self.scraper_class(source_url, logger=self.logger, **kwargs)
    
    def _map_countries(
        self,
        scraped_data: List[ScrapedFuelPrice]
    ) -> List[ScrapedFuelPrice]:
        """
        Map country names to ISO codes.
        
        Attempts to map each country name to its ISO 3166-1 alpha-2 code.
        Records that cannot be mapped are excluded and logged.
        
        Args:
            scraped_data: List of ScrapedFuelPrice objects with country names
            
        Returns:
            List of ScrapedFuelPrice objects with country_code populated
        """
        mapped = []
        unmapped_countries = set()
        
        for data in scraped_data:
            code = self.mapper.map_to_code(data.country_name, fuzzy_match=True)
            
            if code:
                data.country_code = code
                mapped.append(data)
            else:
                unmapped_countries.add(data.country_name)
        
        if unmapped_countries:
            self.logger.warning(
                f"Unmapped countries ({len(unmapped_countries)}): "
                f"{', '.join(sorted(unmapped_countries))}"
            )
        
        return mapped
    
    def _log_report(self, report: Dict):
        """
        Log final execution report.
        
        Provides a comprehensive summary of the scraping workflow
        with statistics for each stage.
        
        Args:
            report: Report dictionary with workflow results
        """
        self.logger.info("=" * 60)
        self.logger.info("Scraping Workflow Report")
        self.logger.info("=" * 60)
        self.logger.info(f"Success: {report['success']}")
        self.logger.info(f"Scraped: {report['scraped_count']} records")
        self.logger.info(f"Mapped: {report['mapped_count']} records")
        self.logger.info(f"Valid: {report['valid_count']} records")
        
        if report['loaded_stats']:
            stats = report['loaded_stats']
            self.logger.info(
                f"Loaded: {stats.get('created', 0)} created, "
                f"{stats.get('updated', 0)} updated, "
                f"{stats.get('skipped', 0)} skipped, "
                f"{stats.get('errors', 0)} errors"
            )
        
        if report['errors']:
            self.logger.error(f"Errors encountered: {len(report['errors'])}")
            for error in report['errors']:
                self.logger.error(f"  - {error}")
        
        self.logger.info("=" * 60)