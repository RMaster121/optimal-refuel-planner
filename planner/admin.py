from django.contrib import admin

from .models import RefuelPlan, RefuelStop


class RefuelStopInline(admin.TabularInline):
    """Inline display of refuel stops within a plan."""

    model = RefuelStop
    extra = 0
    fields = (
        "stop_number",
        "country",
        "distance_from_start_km",
        "fuel_to_add_liters",
        "fuel_price",
        "total_cost",
        "latitude",
        "longitude",
    )
    readonly_fields = ("country", "fuel_price")
    ordering = ("stop_number",)


@admin.register(RefuelPlan)
class RefuelPlanAdmin(admin.ModelAdmin):
    list_display = (
        "route",
        "car",
        "optimization_strategy",
        "number_of_stops",
        "total_cost",
        "total_fuel_needed",
        "created_at",
    )
    list_filter = ("optimization_strategy", "car__fuel_type", "created_at")
    search_fields = (
        "route__origin",
        "route__destination",
        "car__name",
        "car__user__username",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    autocomplete_fields = ("route", "car")
    inlines = (RefuelStopInline,)
    fieldsets = (
        (None, {"fields": ("route", "car")}),
        (
            "Optimization parameters",
            {"fields": ("optimization_strategy", "reservoir_km")},
        ),
        (
            "Results",
            {"fields": ("total_cost", "total_fuel_needed", "number_of_stops")},
        ),
        ("Metadata", {"fields": ("created_at",)}),
    )


@admin.register(RefuelStop)
class RefuelStopAdmin(admin.ModelAdmin):
    list_display = (
        "plan",
        "stop_number",
        "get_country_code",
        "distance_from_start_km",
        "fuel_to_add_liters",
        "get_price_per_liter",
        "total_cost",
    )
    list_filter = ("country__code", "plan__optimization_strategy")
    search_fields = ("plan__route__origin", "plan__route__destination", "country__code")
    ordering = ("plan", "stop_number")
    autocomplete_fields = ("plan", "country", "fuel_price")
    fieldsets = (
        (None, {"fields": ("plan", "stop_number")}),
        ("Location", {"fields": ("country", "distance_from_start_km", "latitude", "longitude")}),
        ("Fuel details", {"fields": ("fuel_price", "fuel_to_add_liters", "total_cost")}),
    )

    @admin.display(description="Country", ordering="country__code")
    def get_country_code(self, obj):
        """Display country code."""
        return obj.country.code.upper() if obj.country else "-"

    @admin.display(description="Price/L", ordering="fuel_price__price_per_liter")
    def get_price_per_liter(self, obj):
        """Display price per liter."""
        return f"€{obj.fuel_price.price_per_liter}" if obj.fuel_price else "-"