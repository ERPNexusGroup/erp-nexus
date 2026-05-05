from django.contrib import admin
from .models import FiscalYear, FiscalPeriod


@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "start_date", "end_date", "is_current", "is_closed")
    list_filter = ("is_current", "is_closed", "company")
    search_fields = ("name", "company__name")
    date_hierarchy = "start_date"
    ordering = ("-name",)


@admin.register(FiscalPeriod)
class FiscalPeriodAdmin(admin.ModelAdmin):
    list_display = ("name", "fiscal_year", "start_date", "end_date", "sequence", "is_open", "is_closed")
    list_filter = ("is_open", "is_closed", "fiscal_year__company")
    search_fields = ("name", "fiscal_year__name")
    ordering = ("fiscal_year", "sequence")
