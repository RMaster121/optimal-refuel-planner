from django.contrib import admin

from .models import Country, FuelPrice


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")
    ordering = ("name",)
    readonly_fields = ()
    fieldsets = (
        (None, {"fields": ("name", "code")}),
    )


@admin.register(FuelPrice)
class FuelPriceAdmin(admin.ModelAdmin):
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