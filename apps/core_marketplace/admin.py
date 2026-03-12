from django.contrib import admin

from .models import ModuleCatalogItem


@admin.register(ModuleCatalogItem)
class ModuleCatalogItemAdmin(admin.ModelAdmin):
    list_display = ("id", "technical_name", "version", "is_active")
    search_fields = ("technical_name", "version")
