"""
Módulo Facturación Electrónica Ecuador — Plugin SRI

Este plugin extiende `apps.facturacion.Invoice` con campos para envío al SRI.
Requiere que `apps.facturacion` esté instalado.
"""
from django.db import models
from django.conf import settings


class InvoiceSRIExtension(models.Model):
    """
    Extensión SRI para Invoice core (OneToOne).
    """
    invoice = models.OneToOneField(
        'facturacion.Invoice',  # string reference evita import circular
        on_delete=models.CASCADE,
        related_name='sri_extension'
    )
    ambiente = models.IntegerField(
        choices=[(1, 'Pruebas'), (2, 'Producción')],
        default=1
    )
    tipo_comprobante = models.ForeignKey(
        'SriTipoComprobante',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    access_key = models.CharField(
        max_length=50,
        unique=True,
        help_text='Clave acceso SRI (49 dígitos)'
    )
    sri_status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Borrador'),
            ('pending', 'Pendiente envío'),
            ('sent', 'Enviada a SRI'),
            ('accepted', 'Aceptada SRI'),
            ('rejected', 'Rechazada SRI'),
            ('cancelled', 'Anulada'),
        ],
        default='pending'
    )
    sri_message = models.TextField(blank=True, help_text='Mensaje respuesta SRI')
    sri_xml_autorizado = models.TextField(blank=True, help_text='XML autorizado por SRI')
    sri_authorization_date = models.DateTimeField(blank=True, null=True)
    xml_content = models.TextField(blank=True, help_text='XML firmado (enviado)')
    xml_original_hash = models.CharField(blank=True, max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Extensión SRI Factura'
        verbose_name_plural = 'Extensiones SRI Facturas'
        indexes = [
            models.Index(fields=['sri_status']),
            models.Index(fields=['access_key']),
        ]

    def __str__(self):
        return f"SRI Ext — {self.invoice.number} [{self.sri_status}]"


class SriTipoComprobante(models.Model):
    """Catálogo tipos de comprobante SRI Ecuador."""
    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Tipo Comprobante SRI'
        verbose_name_plural = 'Tipos Comprobante SRI'

    def __str__(self):
        return f"{self.code} — {self.name}"


class SriAmbiente(models.Model):
    """Catálogo ambientes SRI (1=Pruebas, 2=Producción)."""
    code = models.IntegerField(unique=True)
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'Ambiente SRI'
        verbose_name_plural = 'Ambientes SRI'

    def __str__(self):
        return f"{self.code} — {self.name}"


class SriImpuesto(models.Model):
    """Catálogo impuestos SRI (IVA, ICE, etc.)."""
    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=100)
    percent = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Impuesto SRI'
        verbose_name_plural = 'Impuestos SRI'

    def __str__(self):
        return f"{self.code} — {self.name} ({self.percent}%)"


class SRISendLog(models.Model):
    """Log de envíos a SRI (request/response XML)."""
    invoice_extension = models.ForeignKey(
        InvoiceSRIExtension,
        on_delete=models.CASCADE,
        related_name='sri_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    endpoint = models.CharField(max_length=200)
    request_xml = models.TextField(blank=True)
    response_xml = models.TextField(blank=True)
    response_code = models.CharField(blank=True, max_length=20)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Log Envío SRI'
        verbose_name_plural = 'Logs Envíos SRI'
        ordering = ['-timestamp']


class CompanyLicense(models.Model):
    """
    Licencia por company para facturación electrónica.
    Límite de facturas por mes.
    """
    company = models.ForeignKey(
        'core_companies.Company',
        on_delete=models.CASCADE,
        related_name='facturacion_ec_licenses'
    )
    license_type = models.ForeignKey(
        SriTipoComprobante,
        on_delete=models.PROTECT
    )
    activated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=False)
    invoices_this_month = models.IntegerField(default=0)
    current_month_year = models.CharField(blank=True, max_length=7)

    class Meta:
        verbose_name = 'Licencia Facturación EC'
        verbose_name_plural = 'Licencias Facturación EC'
        indexes = [
            models.Index(fields=['company', 'is_active']),
        ]

    def increment_invoice_count(self):
        from django.utils import timezone
        now = timezone.now()
        month_year = now.strftime('%Y%m')
        if self.current_month_year != month_year:
            self.current_month_year = month_year
            self.invoices_this_month = 0
        self.invoices_this_month += 1
        self.save(update_fields=['current_month_year', 'invoices_this_month'])
