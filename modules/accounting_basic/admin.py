from django.contrib import admin
from .core.models import Account, JournalEntry, JournalLine


class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 1


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "account_type", "is_active", "balance"]
    list_filter = ["account_type", "is_active"]
    search_fields = ["code", "name"]
    ordering = ["code"]


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ["reference", "date", "description", "is_posted", "total_debit", "total_credit"]
    list_filter = ["is_posted", "date"]
    search_fields = ["reference", "description"]
    inlines = [JournalLineInline]
    readonly_fields = ["reference"]
