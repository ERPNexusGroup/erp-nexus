from django.contrib import admin
from .models import Installation, UsageMetric, SystemHealth


@admin.register(Installation)
class InstallationAdmin(admin.ModelAdmin):
    list_display = ["instance_id", "version", "environment", "total_users", "total_modules_active", "last_seen"]
    readonly_fields = ["id", "instance_id", "installed_at"]


@admin.register(UsageMetric)
class UsageMetricAdmin(admin.ModelAdmin):
    list_display = ["date", "metric_type", "value"]
    list_filter = ["metric_type", "date"]
    date_hierarchy = "date"


@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "db_status", "cache_status", "active_users_count"]
    readonly_fields = ["timestamp"]
