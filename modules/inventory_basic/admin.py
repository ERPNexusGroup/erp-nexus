from django.contrib import admin
from .core.models import Category, Product, StockMovement


class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    readonly_fields = ["created_at"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active"]
    search_fields = ["code", "name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["sku", "name", "category", "unit_price", "stock_quantity", "min_stock", "is_low_stock"]
    list_filter = ["category", "is_active"]
    search_fields = ["sku", "name"]
    inlines = [StockMovementInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ["product", "movement_type", "quantity", "reference", "created_at"]
    list_filter = ["movement_type", "created_at"]
    search_fields = ["product__sku", "reference"]
