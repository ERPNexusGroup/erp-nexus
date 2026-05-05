from django.contrib import admin
from .models import ConfigKey, SystemConfig


@admin.register(ConfigKey)
class ConfigKeyAdmin(admin.ModelAdmin):
    list_display = ("key", "description", "value_type", "group", "is_system")
    list_filter = ("group", "value_type", "is_system")
    search_fields = ("key", "description")
    ordering = ("group", "key")


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ("key", "value_short", "company", "created_by", "updated_at")
    list_filter = ("company", "key__group")
    search_fields = ("key__key", "value")
    raw_id_fields = ("key",)

    def value_short(self, obj):
        return obj.value[:50] + "..." if len(obj.value) > 50 else obj.value
    value_short.short_description = "Valor"
