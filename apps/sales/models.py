"""
Models for sales module: Quote, QuoteLine, Order, OrderLine.
"""
from django.db import models
from django.utils import timezone


class Quote(models.Model):
    """Cotización de venta (no compromete stock)."""
    STATUS_CHOICES = [
        ("draft", "Borrador"),
        ("sent", "Enviada"),
        ("accepted", "Aceptada"),
        ("rejected", "Rechazada"),
        ("expired", "Expirada"),
    ]

    quote_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(
        "apps.facturacion.Customer",
        on_delete=models.PROTECT,
        related_name="quotes",
    )
    issue_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ["-issue_date"]

    def __str__(self):
        return f"Quote {self.quote_number} — {self.customer.name}"


class QuoteLine(models.Model):
    """Línea de cotización."""
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(
        "apps.inventory.Product",
        on_delete=models.PROTECT,
        related_name="quote_lines",
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Línea de Cotización"
        verbose_name_plural = "Líneas de Cotización"

    def __str__(self):
        return f"{self.product.sku} × {self.quantity}"


class Order(models.Model):
    """Orden de venta (compromete stock al confirmar)."""
    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("confirmed", "Confirmada"),
        ("partial", "Parcial"),
        ("completed", "Completada"),
        ("cancelled", "Cancelada"),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(
        "apps.facturacion.Customer",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    issue_date = models.DateField(default=timezone.now)
    delivery_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Orden de Venta"
        verbose_name_plural = "Órdenes de Venta"
        ordering = ["-issue_date"]

    def __str__(self):
        return f"Order {self.order_number} — {self.customer.name}"


class OrderLine(models.Model):
    """Línea de orden de venta."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(
        "apps.inventory.Product",
        on_delete=models.PROTECT,
        related_name="order_lines",
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Línea de Orden"
        verbose_name_plural = "Líneas de Orden"

    def __str__(self):
        return f"{self.product.sku} × {self.quantity}"
