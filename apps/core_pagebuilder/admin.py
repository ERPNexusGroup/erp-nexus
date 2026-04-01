from django.contrib import admin
from .models import Page, Component


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "status", "component_count", "updated_at"]
    list_filter = ["status"]
    search_fields = ["title", "slug"]
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ["name", "component_type", "is_active"]
    list_filter = ["component_type", "is_active"]
    search_fields = ["name"]
