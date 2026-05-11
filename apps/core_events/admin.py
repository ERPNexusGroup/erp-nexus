from django.contrib import admin
from .models import EventLog, EventSubscription


@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ["event_type", "source_module", "processed", "created_at"]
    list_filter = ["processed", "event_type", "source_module", "created_at"]
    search_fields = ["event_type", "source_module"]
    readonly_fields = ["id", "event_type", "source_module", "payload", "processed", "processed_at", "error_message", "created_at"]
    date_hierarchy = "created_at"


@admin.register(EventSubscription)
class EventSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["event_type", "subscriber_module", "active", "created_at"]
    list_filter = ["active", "event_type"]
    search_fields = ["event_type", "subscriber_module"]
