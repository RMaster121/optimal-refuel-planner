"""
Real-world integration test for Fuel Price Scraper.

This test makes actual HTTP requests to the live data source to verify:
1. Scraper can fetch real HTML
2. Parser extracts country names and prices correctly
3. Country mapper handles all real country names
4. Data validation passes for real data
5. Database loading works end-to-end

NOTE: This test requires internet connectivity and the source website to be accessible.
Mark as @pytest.mark.integration and run separately from unit tests.
"""

import pytest
from decimal import Decimal
from django.utils import timezone

from fuel_prices.scrapers import ScraperManager, HTMLTableScraper
from fuel_prices.models import Country, FuelPrice


@pytest.mark.integration
@pytest.mark.django_db
class TestScraperRealWebsite:
    """Integration tests against real fuel price website."""
    
    def test_scrape_real_website(self):
        """
        Test scraping from actual data source.
        
        This test verifies the complete scraper workflow against the real website.
        It should be run periodically to catch structural changes in the source HTML.
        
        Requirements:
        - Internet connectivity
        - Source website accessible
        - FUEL_PRICE_SOURCE_URL configured (defaults if not set)
        """
        # Use real source URL (or test URL if configured)
        source_url = 'https://www.cargopedia.net/europe-fuel-prices'
        
        # Run complete scraping workflow
        manager = ScraperManager(scraper_class=HTMLTableScraper)
        report = manager.run_scraping(
            source_url=source_url,
            auto_create_countries=True
        )
        
        # Verify workflow succeeded
        assert report['success'] is True, f"Scraping failed: {report.get('errors')}"
        
        # Verify data was scraped
        assert report['scraped_count'] > 0, "No data scraped from source"
        assert report['scraped_count'] >= 80, "Expected at least 80 records (40 countries × 2 fuel types)"
        
        # Verify country mapping worked
        assert report['mapped_count'] > 0, "No countries mapped"
        mapping_rate = report['mapped_count'] / report['scraped_count']
        assert mapping_rate >= 0.95, f"Low mapping rate: {mapping_rate:.1%}"
        
        # Verify validation passed
        assert report['valid_count'] > 0, "No valid records"
        validation_rate = report['valid_count'] / report['mapped_count']
        assert validation_rate >= 0.90, f"Low validation rate: {validation_rate:.1%}"
        
        # Verify database writes
        stats = report['loaded_stats']
        total_loaded = stats['created'] + stats['updated']
        assert total_loaded > 0, "No records loaded to database"
        
        # Log results for manual review
        print("\n" + "=" * 60)
        print("Real Website Scraping Results")
        print("=" * 60)
        print(f"Scraped:     {report['scraped_count']} records")
        print(f"Mapped:      {report['mapped_count']} countries")
        print(f"Valid:       {report['valid_count']} records")
        print(f"Created:     {stats['created']} new prices")
        print(f"Updated:     {stats['updated']} existing prices")
        print(f"Skipped:     {stats['skipped']} unchanged/missing")
        print(f"Errors:      {stats['errors']} failed")
        print("=" * 60)
    
    def test_real_data_quality(self):
        """
        Test quality of scraped data from real website.
        
        Runs scraping and validates:
        - Price ranges are reasonable
        - All expected countries are present
        - Fuel types are correct
        - Timestamps are recent
        """
        source_url = 'https://www.cargopedia.net/europe-fuel-prices'
        
        manager = ScraperManager()
        report = manager.run_scraping(source_url, auto_create_countries=True)
        
        assert report['success'] is True
        
        # Verify we have fuel prices in database
        fuel_prices = FuelPrice.objects.filter(
            scraped_at__date=timezone.now().date()
        )
        
        assert fuel_prices.count() > 0, "No fuel prices loaded"
        
        # Verify price ranges are reasonable (€0.10 - €10.00)
        for price in fuel_prices:
            assert price.price_per_liter >= Decimal('0.10')
            assert price.price_per_liter <= Decimal('10.00')
        
        # Verify we have both fuel types
        fuel_types = set(fuel_prices.values_list('fuel_type', flat=True))
        assert 'gasoline' in fuel_types
        assert 'diesel' in fuel_types
        
        # Verify common countries are present
        country_codes = set(fuel_prices.values_list('country__code', flat=True))
        expected_countries = {'PL', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT'}
        found_countries = expected_countries.intersection(country_codes)
        
        assert len(found_countries) >= 6, \
            f"Expected at least 6 common countries, found {len(found_countries)}: {found_countries}"
        
        print(f"\n✓ Verified {fuel_prices.count()} prices for {len(country_codes)} countries")
    
    def test_scraper_idempotency(self):
        """
        Test that running scraper twice produces consistent results.
        
        Verifies:
        - Second run updates prices (not creates duplicates)
        - Same countries are found
        - No database constraint violations
        """
        source_url = 'https://www.cargopedia.net/europe-fuel-prices'
        
        manager = ScraperManager()
        
        # First run
        report1 = manager.run_scraping(source_url, auto_create_countries=True)
        assert report1['success'] is True
        
        count_after_first = FuelPrice.objects.count()
        countries_after_first = Country.objects.count()
        
        # Second run (immediately after)
        report2 = manager.run_scraping(source_url, auto_create_countries=True)
        assert report2['success'] is True
        
        # Verify no duplicates created
        count_after_second = FuelPrice.objects.count()
        countries_after_second = Country.objects.count()
        
        assert count_after_second == count_after_first, "Duplicate prices created"
        assert countries_after_second == countries_after_first, "Duplicate countries created"
        
        # Second run should have mostly updates or skips
        stats2 = report2['loaded_stats']
        assert stats2['created'] == 0, "Should not create new prices on same day"
        assert stats2['updated'] >= 0  # May be 0 if prices unchanged
        assert stats2['skipped'] >= 0
        
        print(f"\n✓ Idempotency verified: {stats2['updated']} updated, {stats2['skipped']} skipped")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.django_db
class TestScraperPerformance:
    """Performance tests for real-world scraping."""
    
    def test_scraping_performance(self):
        """
        Test that scraping completes within acceptable time.
        
        Target: < 10 seconds for complete workflow
        """
        import time
        source_url = 'https://www.cargopedia.net/europe-fuel-prices'
        
        manager = ScraperManager()
        
        start_time = time.time()
        report = manager.run_scraping(source_url, auto_create_countries=True)
        duration = time.time() - start_time
        
        assert report['success'] is True
        assert duration < 10.0, f"Scraping took {duration:.1f}s (target: <10s)"
        
        print(f"\n✓ Scraping completed in {duration:.2f}s")


# Helper function to run integration tests manually
def run_integration_tests():
    """
    Run integration tests manually from Django shell or script.
    
    Usage:
        python manage.py shell
        >>> from tests.test_scraper_integration import run_integration_tests
        >>> run_integration_tests()
    """
    pytest.main([
        __file__,
        '-v',
        '-m', 'integration',
        '--tb=short'
    ])


if __name__ == '__main__':
    # Allow running this file directly for quick testing
    run_integration_tests()