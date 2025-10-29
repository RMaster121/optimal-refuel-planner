from django.contrib import admin

from .models import Car


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    """Admin configuration for vehicle records."""

    list_display = (
        "name",
        "user",
        "fuel_type",
        "avg_consumption",
        "tank_capacity",
        "max_range_display",
        "created_at",
    )
    list_filter = ("fuel_type", "user")
    search_fields = ("name", "user__username", "user__email")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("user", "name", "fuel_type")}),
        ("Fuel characteristics", {"fields": ("avg_consumption", "tank_capacity")}),
        ("Audit information", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Max range (km)")
    def max_range_display(self, obj: Car) -> str:
        return f"{obj.max_range_km:.2f}"