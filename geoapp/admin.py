from django.contrib import admin
from .models import GeoServerWorkspace, GeoServerLayer


@admin.register(GeoServerWorkspace)
class GeoServerWorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(GeoServerLayer)
class GeoServerLayerAdmin(admin.ModelAdmin):
    list_display = ("title", "workspace", "layer_name", "is_visible", "layer_order")
    list_filter = ("workspace", "is_visible")
    search_fields = ("title", "name", "layer_name")
