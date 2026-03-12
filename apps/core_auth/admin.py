from django.contrib import admin

from .models import AuthPolicy


@admin.register(AuthPolicy)
class AuthPolicyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active")
    search_fields = ("name",)
