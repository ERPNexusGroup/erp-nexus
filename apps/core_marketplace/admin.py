from django.contrib import admin

from .models import EnabledModule, ModuleCatalogItem


@admin.register(ModuleCatalogItem)
class ModuleCatalogItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "technical_name",
        "version",
        "status",
        "is_active",
        "installed_at",
        "django_app",
    )
    list_filter = ("status", "is_active")
    search_fields = ("technical_name", "version", "source", "installed_path", "django_app")


@admin.register(EnabledModule)
class EnabledModuleAdmin(admin.ModelAdmin):
    list_display = ("id", "technical_name", "django_app", "status", "enabled_at")
    list_filter = ("status",)
    search_fields = ("technical_name", "django_app")
