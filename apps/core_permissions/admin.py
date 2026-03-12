from django.contrib import admin

from .models import Permission


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "description")
    search_fields = ("code", "description")
