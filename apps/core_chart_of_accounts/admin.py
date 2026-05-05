from django.contrib import admin
from .models import AccountType, Account, JournalEntry, JournalEntryLine


@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "nature", "display_order", "is_active")
    search_fields = ("code", "name")
    ordering = ("display_order",)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "account_type", "parent", "is_active", "company")
    list_filter = ("account_type", "is_active", "company")
    search_fields = ("code", "name", "sri_code")
    ordering = ("code",)


class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 1
    fields = ("account", "description", "debit", "credit")


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "reference", "document_number", "is_posted", "company")
    list_filter = ("is_posted", "date", "company")
    search_fields = ("reference", "document_number")
    date_hierarchy = "date"
    inlines = [JournalEntryLineInline]


@admin.register(JournalEntryLine)
class JournalEntryLineAdmin(admin.ModelAdmin):
    list_display = ("journal_entry", "account", "debit", "credit")
    search_fields = ("journal_entry__reference", "account__code")
