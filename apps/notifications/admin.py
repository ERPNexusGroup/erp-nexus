from django.contrib import admin
from .models import Notification, NotificationTemplate, NotificationQueue


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "notification_type", "title", "is_read", "created_at", "delivered_at"]
    list_filter = ["notification_type", "is_read", "created_at"]
    search_fields = ["user__username", "title", "message"]
    readonly_fields = ["created_at", "delivered_at"]


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "notification_type", "subject"]
    search_fields = ["name", "subject"]


@admin.register(NotificationQueue)
class NotificationQueueAdmin(admin.ModelAdmin):
    list_display = ["notification_type", "recipient", "status", "attempts", "created_at", "processed_at"]
    list_filter = ["status", "notification_type", "created_at"]
    search_fields = ["recipient", "title"]
