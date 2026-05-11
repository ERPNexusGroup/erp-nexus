from django.contrib import admin
from .models import Supplier, PurchaseOrder, PurchaseOrderLine


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 0


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["vendor_number", "customer", "rating", "payment_terms_days", "is_active"]
    search_fields = ["vendor_number", "customer__name"]
    list_filter = ["is_active", "rating"]


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ["po_number", "supplier", "order_date", "expected_delivery", "status", "total"]
    list_filter = ["status", "order_date"]
    search_fields = ["po_number", "supplier__vendor_number"]
    inlines = [PurchaseOrderLineInline]


@admin.register(PurchaseOrderLine)
class PurchaseOrderLineAdmin(admin.ModelAdmin):
    list_display = ["po", "product", "quantity_ordered", "quantity_received", "unit_price", "subtotal"]
    search_fields = ["po__po_number", "product__sku"]
