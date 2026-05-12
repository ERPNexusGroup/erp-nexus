"""
Core Facturación Local — ERP Nexus

Este módulo contiene los modelos base de facturación SIN integración externa.
Es independiente de cualquier legislación específica (SRI Ecuador, AFIP Argentina, etc.)

Los plugins externos (ej: facturacion_ec) extienden estos modelos con campos
adicionales para cumplir límites fiscales locales.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Customer(models.Model):
    """
    Cliente/Local Partner.

    Datos fiscales básicos. Los plugins pueden extender con campos adicionales
    (ej: `facturacion_ec.CustomerSRIExtension`).
    """
    ID_TYPE_CHOICES = [
        ('04', 'RUC'),
        ('05', 'Cédula'),
        ('06', 'Pasaporte'),
        ('07', 'Consumidor final'),
        ('08', 'Identificación exterior'),
    ]

    company = models.ForeignKey(
        'core_companies.Company',
        on_delete=models.CASCADE,
        related_name='facturacion_customers'
    )
    identification_type = models.CharField(
        max_length=5,
        choices=ID_TYPE_CHOICES,
        default='05'
    )
    identification_number = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, max_length=254)
    phone = models.CharField(blank=True, max_length=50)
    address = models.TextField(blank=True)
    razon_social = models.CharField(
        blank=True,
        max_length=200,
        help_text='Razón social (para RUC)'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        unique_together = [('company', 'identification_type', 'identification_number')]
        indexes = [
            models.Index(fields=['identification_number'], name='idx_fact_customer_ident'),
            models.Index(fields=['company', 'is_active'], name='idx_fact_customer_co_active'),
        ]

    def __str__(self):
        return f"{self.name} ({self.identification_number})"


class Invoice(models.Model):
    """
    Factura local (sin envío a SRI por defecto).

    Para facturación electrónica Ecuador, usar el plugin `facturacion_ec`
    que crea una extensión OneToOne `InvoiceSRIExtension`.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('paid', 'Pagada'),
        ('cancelled', 'Anulada'),
        ('sent', 'Enviada (SRI)'),  # solo plugins
    ]

    company = models.ForeignKey(
        'core_companies.Company',
        on_delete=models.CASCADE,
        related_name='facturacion_invoices'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='facturacion_invoices'
    )
    number = models.CharField(
        max_length=30,
        help_text='Número factura (ej: 001-001-000000001)',
        unique=True
    )
    date = models.DateField(default=timezone.now)
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    tax_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    notes = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='facturas_created_facturacion'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-date', '-id']
        indexes = [
            models.Index(fields=['company', 'date'], name='idx_fact_invoice_co_date'),
            models.Index(fields=['status'], name='idx_fact_invoice_status'),
        ]

    def __str__(self):
        return f"Factura {self.number} — {self.customer.name}"


class InvoiceLine(models.Model):
    """
    Línea de factura.

    `product` apunta a `inventory.Product` (si existe módulo inventory).
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='facturacion_lines'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT,
        related_name='facturacion_invoice_lines'
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text='Descripción opcional (sobre escribe product.name)'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Precio unitario (sin impuestos)'
    )
    unit_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Descuento por unidad'
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='quantity × (unit_price − unit_discount)'
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=12.00,
        help_text='Porcentaje impuesto (ej: 12.00 para IVA Ecuador)'
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='subtotal × (tax_rate / 100)'
    )
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Descuento total sobre la línea'
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='subtotal + tax_amount − discount'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Línea de Factura'
        verbose_name_plural = 'Líneas de Factura'
        indexes = [
            models.Index(fields=['invoice'], name='idx_fact_line_invoice'),
        ]

    def __str__(self):
        return f"{self.product.code} × {self.quantity}"
