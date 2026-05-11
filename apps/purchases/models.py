"""
Models for purchases module: Supplier, PurchaseOrder, PurchaseOrderLine.
"""
from django.db import models
from django.utils import timezone


class Supplier(models.Model):
    """Proveedor (extiende Customer de facturación)."""
    customer = models.OneToOneField(
        "facturacion.Customer",
        on_delete=models.PROTECT,
        related_name="supplier_profile",
    )
    vendor_number = models.CharField(max_length=50, unique=True)
    rating = models.IntegerField(default=5)  # 1-5
    payment_terms_days = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["vendor_number"]

    def __str__(self):
        return f"{self.vendor_number} — {self.customer.name}"


class PurchaseOrder(models.Model):
    """Orden de compra."""
    STATUS_CHOICES = [
        ("draft", "Borrador"),
        ("sent", "Enviada"),
        ("received", "Recibida"),
        ("partial", "Parcial"),
        ("cancelled", "Cancelada"),
    ]

    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )
    order_date = models.DateField(default=timezone.now)
    expected_delivery = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"
        ordering = ["-order_date"]

    def __str__(self):
        return f"PO {self.po_number} — {self.supplier}"


class PurchaseOrderLine(models.Model):
    """Línea de orden de compra."""
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.PROTECT,
        related_name="po_lines",
    )
    quantity_ordered = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Línea de OC"
        verbose_name_plural = "Líneas de OC"

    def __str__(self):
        return f"{self.product.sku} × {self.quantity_ordered}"

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity_ordered * self.unit_price
        super().save(*args, **kwargs)
