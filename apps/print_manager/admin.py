from django.contrib import admin
from .models import PrintTemplate, PrintJob


@admin.register(PrintTemplate)
class PrintTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "template_key", "is_active", "created_at"]
    search_fields = ["name", "template_key"]
    list_filter = ["is_active"]


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    list_display = ["template", "status", "created_at", "completed_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["template__name"]
