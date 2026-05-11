from django.contrib import admin
from .models import Quote, QuoteLine, Order, OrderLine


class QuoteLineInline(admin.TabularInline):
    model = QuoteLine
    extra = 0


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ["quote_number", "customer", "issue_date", "expiry_date", "status", "total"]
    list_filter = ["status", "issue_date"]
    search_fields = ["quote_number", "customer__name"]
    inlines = [QuoteLineInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "customer", "issue_date", "delivery_date", "status", "total"]
    list_filter = ["status", "issue_date"]
    search_fields = ["order_number", "customer__name"]
    inlines = [OrderLineInline]


@admin.register(QuoteLine)
class QuoteLineAdmin(admin.ModelAdmin):
    list_display = ["quote", "product", "quantity", "unit_price", "subtotal"]
    search_fields = ["quote__quote_number", "product__sku"]


@admin.register(OrderLine)
class OrderLineAdmin(admin.ModelAdmin):
    list_display = ["order", "product", "quantity", "unit_price", "subtotal"]
    search_fields = ["order__order_number", "product__sku"]
