"""
Django management command to run fuel price scraping.

Usage:
    python manage.py scrape_fuel_prices [options]
    
Options:
    --source-url URL       Override default source URL
    --no-auto-create      Disable auto-creation of missing countries
    --verbose             Enable verbose logging
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import logging
import os

from fuel_prices.scrapers.manager import ScraperManager
from fuel_prices.scrapers.html_table_scraper import HTMLTableScraper


class Command(BaseCommand):
    """
    Django management command to scrape fuel prices from external sources.
    """
    
    help = 'Scrape fuel prices from configured sources'
    
    def add_arguments(self, parser):
        """
        Define command-line arguments.
        
        Args:
            parser: ArgumentParser instance
        """
        parser.add_argument(
            '--source-url',
            type=str,
            help='Override default source URL for scraping'
        )
        
        parser.add_argument(
            '--no-auto-create',
            action='store_true',
            help='Disable automatic creation of missing Country records'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose logging output'
        )
    
    def handle(self, *args, **options):
        """
        Execute the scraping command.
        
        Args:
            *args: Positional arguments (unused)
            **options: Command options from argument parser
            
        Raises:
            CommandError: If scraping workflow fails or configuration is invalid
        """
        # Configure logging
        log_level = logging.DEBUG if options['verbose'] else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(levelname)s %(asctime)s %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Get source URL from options or environment/settings
        source_url = options.get('source_url') or os.environ.get(
            'FUEL_PRICE_SOURCE_URL'
        ) or getattr(
            settings,
            'FUEL_PRICE_SOURCE_URL',
            None
        )
        
        if not source_url:
            raise CommandError(
                "Source URL not configured. "
                "Set FUEL_PRICE_SOURCE_URL in settings/environment or use --source-url option"
            )
        
        # Get auto-create setting
        auto_create = not options['no_auto_create']
        
        # Display configuration
        self.stdout.write(self.style.NOTICE('Fuel Price Scraper'))
        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(f"Source URL: {source_url}")
        self.stdout.write(f"Auto-create countries: {auto_create}")
        self.stdout.write(f"Verbose logging: {options['verbose']}")
        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write('')
        
        # Run scraping
        self.stdout.write("Starting fuel price scraping workflow...")
        self.stdout.write('')
        
        try:
            manager = ScraperManager(scraper_class=HTMLTableScraper)
            report = manager.run_scraping(
                source_url=source_url,
                auto_create_countries=auto_create
            )
            
            # Display results
            self.stdout.write('')
            self.stdout.write(self.style.NOTICE('=' * 60))
            self.stdout.write(self.style.NOTICE('Scraping Results'))
            self.stdout.write(self.style.NOTICE('=' * 60))
            
            if report['success']:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Scraping completed successfully")
                )
                self.stdout.write('')
                self.stdout.write(f"Scraped records:  {report['scraped_count']}")
                self.stdout.write(f"Mapped countries: {report['mapped_count']}")
                self.stdout.write(f"Valid records:    {report['valid_count']}")
                
                stats = report.get('loaded_stats', {})
                if stats:
                    self.stdout.write('')
                    self.stdout.write("Database operations:")
                    self.stdout.write(
                        f"  Created:  {stats.get('created', 0)} new price records"
                    )
                    self.stdout.write(
                        f"  Updated:  {stats.get('updated', 0)} existing records"
                    )
                    self.stdout.write(
                        f"  Skipped:  {stats.get('skipped', 0)} unchanged/missing"
                    )
                    if stats.get('errors', 0) > 0:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Errors:   {stats.get('errors', 0)} failed loads"
                            )
                        )
                
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('Scraping workflow completed'))
                
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ Scraping workflow failed")
                )
                self.stdout.write('')
                
                if report.get('scraped_count', 0) > 0:
                    self.stdout.write(
                        f"Scraped {report['scraped_count']} records but workflow failed"
                    )
                
                if report.get('errors'):
                    self.stdout.write('')
                    self.stdout.write(self.style.ERROR("Errors:"))
                    for error in report['errors']:
                        self.stdout.write(self.style.ERROR(f"  - {error}"))
                
                raise CommandError("Scraping workflow failed. Check logs for details.")
        
        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f"✗ Unexpected error: {e}"))
            raise CommandError(f"Scraping failed: {e}")