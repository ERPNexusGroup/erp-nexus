from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "display_name", "is_active", "active_company")
    search_fields = ("display_name", "user__username", "user__email", "active_company__name")


User = get_user_model()
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email")
