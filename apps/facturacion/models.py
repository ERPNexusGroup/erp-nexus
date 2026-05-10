# Módulo facturacion - Modelos
from django.conf import settings
from django.db import models
from django.utils import timezone


# ==================== CATÁLOGOS SRI ====================

class SriAmbiente(models.Model):
    """Ambiente SRI: 1=Pruebas, 2=Producción"""
    code = models.IntegerField(unique=True)
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Ambiente SRI"
        verbose_name_plural = "Ambientes SRI"

    def __str__(self):
        return f"{self.code} - {self.name}"


class SriTipoComprobante(models.Model):
    """Tipos de comprobante: 01=Factura, 04=Nota crédito, etc."""
    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Tipo Comprobante SRI"
        verbose_name_plural = "Tipos Comprobante SRI"

    def __str__(self):
        return f"{self.code} - {self.name}"


class SriImpuesto(models.Model):
    """Impuestos SRI: IVA=2, ICE=3, IRBP=5"""
    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=100)
    percent = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Impuesto SRI"
        verbose_name_plural = "Impuestos SRI"

    def __str__(self):
        return f"{self.code} - {self.name} ({self.percent}%)"


# ==================== LICENCIAMIENTO ====================

class LicenseType(models.Model):
    """
    Tipos de licencia del módulo facturacion.

    Planes definidos:
    - FREE: 10 facturas/mes (limitado)
    - MONTHLY_10: $10/mes, facturas ilimitadas
    - YEARLY_100: $100/año (~$8.33/mes), facturas ilimitadas
    - LIFETIME_3500: $3500 (pago único), todas las actualizaciones futuras
    - LIFETIME_750: $750 (pago único), SIN actualizaciones (soporte bug fixes)
    """
    PLAN_CHOICES = [
        ("free", "Free (10 facturas/mes)"),
        ("monthly_10", "Mensual $10/mes"),
        ("yearly_100", "Anual $100/año"),
        ("lifetime_3500", "Lifetime $3,500 (actualizaciones incluidas)"),
        ("lifetime_750", "Lifetime $750 (sin actualizaciones)"),
    ]

    plan_id = models.CharField(max_length=30, unique=True, choices=PLAN_CHOICES)
    display_name = models.CharField(max_length=100)
    description = models.TextField()
    price_monthly_equivalent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio equivalente mensual (para comparación)"
    )
    max_invoices_per_month = models.IntegerField(
        default=10,
        help_text="Límite de facturas por mes (0=ilimitado)"
    )
    allows_updates = models.BooleanField(
        default=False,
        help_text="Incluye actualizaciones de nuevas versiones"
    )
    priority_support = models.BooleanField(
        default=False,
        help_text="Soporte prioritario (email/chat directo)"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tipo de Licencia"
        verbose_name_plural = "Tipos de Licencia"

    def __str__(self):
        return f"{self.display_name} (${self.price_monthly_equivalent}/mes eq.)"


class CompanyLicense(models.Model):
    """
    Licencia activa de una empresa específica.

    Validación se hace en tiempo real:
    - checks if active_license
    - checks invoice_count_this_month <= max_invoices
    """
    company = models.ForeignKey("core_companies.Company", on_delete=models.CASCADE, related_name="facturacion_licenses")
    license_type = models.ForeignKey(LicenseType, on_delete=models.PROTECT)

    # Fechas
    activated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha vencimiento (NULL = lifetime)"
    )
    last_check = models.DateTimeField(auto_now=True)

    # Pago/Transacción referencias
    transaction_id = models.CharField(max_length=200, blank=True)
    payment_provider = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ("stripe", "Stripe"),
            ("paypal", "PayPal"),
            ("transfer", "Transferencia bancaria"),
            ("manual", "Manual (registrado a mano)"),
        ]
    )

    # Estado
    is_active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=False)
    trial_end_date = models.DateTimeField(null=True, blank=True)

    # Uso actual (cached para performance)
    invoices_this_month = models.IntegerField(default=0)
    current_month_year = models.CharField(max_length=7, blank=True)  # "2026-05"

    class Meta:
        verbose_name = "Licencia de Empresa"
        verbose_name_plural = "Licencias de Empresas"
        unique_together = ("company", "license_type")

    def __str__(self):
        return f"{self.company.name} - {self.license_type.display_name}"

    def is_valid(self):
        """Verifica si la licencia está activa y vigente"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        if self.is_trial and self.trial_end_date and self.trial_end_date < timezone.now():
            return False
        return True

    def can_create_invoice(self):
        """Verifica si puede crear factura (límite mensual)"""
        if not self.is_valid():
            return False, "Licencia no vigente"

        limit = self.license_type.max_invoices_per_month
        if limit == 0:  # ilimitado
            return True, "Límite ilimitado"

        # Reset contador si cambió el mes
        from django.utils import timezone
        current = timezone.now().strftime("%Y-%m")
        if self.current_month_year != current:
            self.invoices_this_month = 0
            self.current_month_year = current
            self.save(update_fields=["invoices_this_month", "current_month_year"])

        if self.invoices_this_month >= limit:
            return False, f"Límite mensual alcanzado ({limit} facturas)"

        return True, "Puede facturar"

    def increment_invoice_count(self):
        """Incrementa contador de facturas del mes"""
        from django.utils import timezone
        current = timezone.now().strftime("%Y-%m")
        if self.current_month_year != current:
            self.invoices_this_month = 0
            self.current_month_year = current

        self.invoices_this_month += 1
        self.save(update_fields=["invoices_this_month", "current_month_year"])


# ==================== FACTURACIÓN ====================

class Customer(models.Model):
    """Cliente para facturación (vincula a contacts en el futuro)"""
    IDENTIFICATION_TYPES = [
        ("04", "RUC"),
        ("05", "Cédula"),
        ("06", "Pasaporte"),
        ("07", "Consumidor final"),
    ]

    company = models.ForeignKey("core_companies.Company", on_delete=models.CASCADE, related_name="customers")
    identification_type = models.CharField(max_length=5, choices=IDENTIFICATION_TYPES)
    identification_number = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    razon_social = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        unique_together = ("company", "identification_type", "identification_number")

    def __str__(self):
        return f"{self.name} ({self.identification_number})"


class Product(models.Model):
    """Producto para líneas de factura"""
    company = models.ForeignKey("core_companies.Company", on_delete=models.CASCADE, related_name="products")
    code = models.CharField(max_length=50, help_text="SKU o código interno")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_tariff = models.CharField(max_length=10, default="2", help_text="Código impuesto SRI: 2=IVA, 3=ICE, etc.")
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=12.00)
    unit_of_measure = models.CharField(max_length=10, default="N/A")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        unique_together = ("company", "code")

    def __str__(self):
        return f"{self.code} - {self.name}"


class Invoice(models.Model):
    """Factura electrónica principal"""
    SRITatus = [
        ("draft", "Borrador"),
        ("pending", "Pendiente envío"),
        ("sent", "Enviada a SRI"),
        ("accepted", "Aceptada SRI"),
        ("rejected", "Rechazada SRI"),
        ("cancelled", "Anulada"),
    ]

    company = models.ForeignKey("core_companies.Company", on_delete=models.CASCADE, related_name="invoices")
    number = models.CharField(max_length=30, help_text="001-001-0000000001")
    date = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="invoices")

    # Totales
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # SRI
    tipo_comprobante = models.ForeignKey(SriTipoComprobante, on_delete=models.PROTECT, default="01")
    ambiente = models.IntegerField(choices=[(1, "Pruebas"), (2, "Producción")], default=1)
    sri_status = models.CharField(max_length=20, choices=SRITatus, default="pending")
    sri_authorization_date = models.DateTimeField(null=True, blank=True)
    sri_message = models.TextField(blank=True, help_text="Mensaje respuesta SRI")
    sri_xml_autorizado = models.TextField(blank=True, help_text="XML autorizado por SRI")

    # Técnicos
    access_key = models.CharField(max_length=50, unique=True, help_text="Clave acceso SRI (49 dígitos)")
    xml_content = models.TextField(blank=True, help_text="XML firmado (enviado)")
    xml_original_hash = models.CharField(max_length=128, blank=True)
    guia_remision_number = models.CharField(max_length=50, blank=True, help_text="Número de guía de remisión")

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="facturas_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Factura Electrónica"
        verbose_name_plural = "Facturas Electrónicas"
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.number} - {self.customer.name} (${self.total})"


class InvoiceLine(models.Model):
    """Línea de factura"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    description = models.CharField(max_length=200, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Descuento en línea")
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Línea de Factura"
        verbose_name_plural = "Líneas de Factura"

    def __str__(self):
        return f"{self.product.code} x {self.quantity}"


class SRISendLog(models.Model):
    """Log de envíos a SRI (auditoría)"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="sri_logs")
    timestamp = models.DateTimeField(auto_now_add=True)
    endpoint = models.CharField(max_length=200)
    request_xml = models.TextField(blank=True)
    response_xml = models.TextField(blank=True)
    response_code = models.CharField(max_length=20, blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "Log Envío SRI"
        verbose_name_plural = "Logs Envíos SRI"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.invoice.number} - {'OK' if self.success else 'FAIL'}"


class ElectronicDocument(models.Model):
    """
    Documento electrónico generado (factura, nota crédito, retención).

    Guarda copia de todos los documentos generados para consulta.
    """
    DOCUMENT_TYPES = [
        ("01", "Factura"),
        ("04", "Nota de Crédito"),
        ("05", "Nota de Débito"),
        ("06", "Guía de Remisión"),
        ("07", "Comprobante de Retención"),
    ]

    company = models.ForeignKey("core_companies.Company", on_delete=models.CASCADE)
    document_type = models.CharField(max_length=2, choices=DOCUMENT_TYPES)
    access_key = models.CharField(max_length=50, unique=True)
    number = models.CharField(max_length=50)
    date = models.DateField()
    xml_original = models.TextField(help_text="XML original generado")
    xml_signed = models.TextField(help_text="XML firmado digitalmente")
    xml_autorizado = models.TextField(blank=True, help_text="XML devuelto por SRI")
    pdf_generated = models.BooleanField(default=False)
    pdf_path = models.CharField(max_length=500, blank=True)

    # Metadata
    created_from_invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="electronic_documents"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Documento Electrónico"
        verbose_name_plural = "Documentos Electrónicos"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.get_document_type_display()} {self.number}"
