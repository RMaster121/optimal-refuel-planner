"""Django admin configuration for fuel price management.

This module configures the Django admin interface for managing countries
and fuel prices. It provides customized list views, filters, and search
functionality optimized for administrative tasks.

The admin interfaces support:
- Efficient searching and filtering of fuel price data
- Organized fieldsets for data entry
- Read-only fields for auto-generated timestamps
- Autocomplete for country selection in fuel prices
"""
from django.contrib import admin

from .models import Country, FuelPrice


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    """Admin interface for Country model.
    
    Provides a streamlined interface for managing the canonical list of
    supported countries. Countries are displayed sorted by name for easy
    browsing and can be searched by name or code.
    
    List Display:
        - name: Human-readable country name
        - code: ISO 3166-1 alpha-2 country code
    
    Features:
        - Search by country name or code
        - Alphabetically ordered by name
        - Simple single-fieldset layout
    
    Example:
        Access via Django admin at /admin/fuel_prices/country/
    """
    list_display = ("name", "code")
    search_fields = ("name", "code")
    ordering = ("name",)
    readonly_fields = ()
    fieldsets = (
        (None, {"fields": ("name", "code")}),
    )


@admin.register(FuelPrice)
class FuelPriceAdmin(admin.ModelAdmin):
    """Admin interface for FuelPrice model.
    
    Provides comprehensive tools for managing fuel price data with efficient
    filtering, searching, and organized data entry forms. The interface is
    optimized for bulk price updates and historical data review.
    
    List Display:
        - country: Related country (name and code)
        - fuel_type: Type of fuel (gasoline/diesel)
        - price_per_liter: Current price in EUR
        - scraped_at: When the price was collected
    
    Filters:
        - fuel_type: Filter by gasoline or diesel
        - country: Filter by specific country
    
    Search:
        - Search by country name or country code
    
    Features:
        - Autocomplete country selection for efficient data entry
        - Read-only scraped_at timestamp (auto-set on creation)
        - Organized fieldsets separating country, pricing, and metadata
        - Ordered by country name and fuel type for easy browsing
    
    Fieldsets:
        1. Basic Info: Country and fuel type selection
        2. Pricing: Price per liter entry
        3. Metadata: Auto-generated timestamp (read-only)
    
    Example:
        Access via Django admin at /admin/fuel_prices/fuelprice/
        
        Adding a new price:
        1. Select country using autocomplete
        2. Choose fuel type
        3. Enter price per liter
        4. Save (scraped_at set automatically)
    """
    list_display = ("country", "fuel_type", "price_per_liter",  "scraped_at")
    list_filter = ("fuel_type", "country")
    search_fields = ("country__name", "country__code")
    ordering = ("country__name", "fuel_type")
    autocomplete_fields = ("country",)
    readonly_fields = ("scraped_at",)
    fieldsets = (
        (None, {"fields": ("country", "fuel_type")}),
        ("Pricing", {"fields": ("price_per_liter",)}),
        ("Metadata", {"fields": ("scraped_at",)}),
    )