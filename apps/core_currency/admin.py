from django.contrib import admin
from .models import Currency, ExchangeRate


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "symbol", "is_base", "is_active")
    list_filter = ("is_active", "is_base")
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("from_currency", "to_currency", "rate", "date", "source")
    list_filter = ("source", "date")
    search_fields = ("from_currency__code", "to_currency__code")
    date_hierarchy = "date"
    ordering = ("-date",)
