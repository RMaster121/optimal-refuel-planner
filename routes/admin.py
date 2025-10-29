from django.contrib import admin

from .models import Route


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = (
        "origin",
        "destination",
        "total_distance_km",
        "countries_display",
        "user",
        "created_at",
    )
    list_filter = ("user", "created_at")
    search_fields = ("origin", "destination", "user__username", "user__email")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    fieldsets = (
        (None, {"fields": ("user", "google_maps_url")}),
        ("Route details", {"fields": ("origin", "destination", "total_distance_km")}),
        ("Geographic data", {"fields": ("waypoints", "countries")}),
        ("Metadata", {"fields": ("created_at",)}),
    )

    @admin.display(description="Countries")
    def countries_display(self, obj: Route) -> str:
        if obj.countries:
            return ", ".join(obj.countries)
        return "-"