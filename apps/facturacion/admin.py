from django.contrib import admin
from .models import Customer, Invoice, InvoiceLine


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'identification_type', 'identification_number', 'company', 'is_active']
    list_filter = ['is_active', 'identification_type', 'company']
    search_fields = ['name', 'identification_number', 'email']
    readonly_fields = ['created_at', 'updated_at']


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0
    fields = ['product', 'description', 'quantity', 'unit_price', 'tax_rate', 'subtotal', 'tax_amount', 'total']
    readonly_fields = ['subtotal', 'tax_amount', 'total']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['number', 'company', 'customer', 'date', 'total', 'status']
    list_filter = ['status', 'date', 'company']
    search_fields = ['number', 'customer__name', 'customer__identification_number']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [InvoiceLineInline]


@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'product', 'quantity', 'unit_price', 'total']
    list_filter = ['invoice__company']
    search_fields = ['product__code', 'invoice__number']
