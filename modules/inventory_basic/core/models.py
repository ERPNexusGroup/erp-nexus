"""
Modelos del módulo inventory_basic.

Productos, categorías y movimientos de inventario.
"""
from django.db import models
from django.utils import timezone


class Category(models.Model):
    """Categoría de productos."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="children",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Product(models.Model):
    """Producto en inventario."""
    sku = models.CharField(max_length=50, unique=True, help_text="Código único del producto")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products",
    )
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    min_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["sku"]

    def __str__(self):
        return f"{self.sku} — {self.name}"

    @property
    def stock_value(self):
        return float(self.stock_quantity * self.unit_price)

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.min_stock


class StockMovement(models.Model):
    """Movimiento de inventario (entrada/salida)."""
    MOVEMENT_TYPES = [
        ("in", "Entrada"),
        ("out", "Salida"),
        ("adjust", "Ajuste"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, default="", help_text="Referencia externa")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movement_type}: {self.product.sku} × {self.quantity}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Actualizar stock del producto
            if self.movement_type == "in":
                self.product.stock_quantity += self.quantity
            elif self.movement_type == "out":
                self.product.stock_quantity -= self.quantity
            else:  # adjust
                self.product.stock_quantity = self.quantity
            self.product.save(update_fields=["stock_quantity"])

            # Emitir evento si stock bajo
            if self.product.is_low_stock:
                from apps.core_events.bus import EventBus
                EventBus.emit(
                    "inventory.low_stock",
                    "inventory_basic",
                    {
                        "product_id": self.product.id,
                        "sku": self.product.sku,
                        "name": self.product.name,
                        "current_stock": float(self.product.stock_quantity),
                        "min_stock": float(self.product.min_stock),
                    },
                )
