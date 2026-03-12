from django.contrib import admin

from .models import Company, Membership


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "company", "role", "status", "is_owner")
    list_filter = ("role", "status", "is_owner")
    search_fields = ("user__username", "company__name")
