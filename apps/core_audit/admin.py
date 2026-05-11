from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "username", "action", "resource_type", "company_name", "ip_address"]
    list_filter = ["action", "resource_type", "created_at", "company_name"]
    search_fields = ["username", "description", "resource_id"]
    readonly_fields = [
        "id", "user_id", "username", "action", "resource_type", "resource_id",
        "description", "metadata", "ip_address", "user_agent",
        "company_id", "company_name", "created_at",
    ]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
