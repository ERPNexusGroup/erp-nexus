from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class BankAccount(models.Model):
    """Cuentas bancarias de la empresa para pagos"""
    BANK_CHOICES = [
        ('produbanco', 'Produbanco'),
        ('pichincha', 'Banco Pichincha'),
        ('guayaquil', 'Banco Guayaquil'),
        ('pacifico', 'Banco del Pacífico'),
        ('solidario', 'Banco Solidario'),
        ('internacional', 'Banco Internacional'),
        ('loja', 'Banco de Loja'),
        ('coops', 'Coops'),
    ]
    ACCOUNT_TYPE = [
        ('checking', 'Corriente'),
        ('savings', 'Ahorros'),
    ]

    company = models.ForeignKey(
        'core_companies.Company',
        on_delete=models.CASCADE,
        related_name='bank_accounts',
        db_index=True,
        help_text="Empresa propietaria de la cuenta"
    )
    bank_code = models.CharField(
        max_length=20,
        choices=BANK_CHOICES,
        help_text="Banco emisor de la cuenta"
    )
    account_number = models.CharField(
        max_length=50,
        help_text="Número de cuenta bancaria"
    )
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE,
        default='checking',
        help_text="Tipo de cuenta (Corriente/Ahorros)"
    )
    rut = models.CharField(
        max_length=20,
        blank=True,
        help_text="RUC o cédula del titular (opcional)"
    )
    account_holder_name = models.CharField(
        max_length=200,
        help_text="Nombre del titular de la cuenta"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si la cuenta está activa"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Cuenta predeterminada para pagos"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = 'Cuenta Bancaria'
        verbose_name_plural = 'Cuentas Bancarias'

    def __str__(self):
        return f"{self.get_bank_code_display()} - {self.account_number}"

    @property
    def bank_display(self) -> str:
        """Display name del banco (para API responses)."""
        return self.get_bank_code_display()


class CommissionRule(models.Model):
    """Reglas de comisión por módulo (ventas, compras, marketplace)"""
    MODULE_CHOICES = [
        ('sales', 'Ventas'),
        ('purchases', 'Compras'),
        ('marketplace', 'Marketplace'),
    ]
    COMMISSION_TYPE = [
        ('percentage', 'Porcentaje'),
        ('fixed', 'Fijo'),
    ]

    module = models.CharField(
        max_length=20,
        choices=MODULE_CHOICES,
        help_text="Módulo al que aplica la regla"
    )
    commission_type = models.CharField(
        max_length=20,
        choices=COMMISSION_TYPE,
        default='percentage',
        help_text="Tipo de comisión: porcentaje o monto fijo"
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Porcentaje de comisión (5.5 = 5.5%)"
    )
    fixed_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Monto fijo de comisión"
    )
    min_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Monto mínimo para aplicar la regla"
    )
    max_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Monto máximo para aplicar la regla (opcional)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si la regla está activa"
    )
    applies_to = models.JSONField(
        default=list,
        blank=True,
        help_text="IDs de categorías, proveedores, etc. a los que aplica"
    )
    created_by = models.CharField(
        max_length=150,
        blank=True,
        help_text="Usuario que creó la regla"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['module', '-created_at']
        verbose_name = 'Regla de Comisión'
        verbose_name_plural = 'Reglas de Comisión'

    def __str__(self):
        if self.commission_type == 'percentage':
            return f"{self.get_module_display()} - {self.percentage}%"
        return f"{self.get_module_display()} - ${self.fixed_amount}"


class Payout(models.Model):
    """Pagos generados a partir de comisiones"""
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('processing', 'Procesando'),
        ('paid', 'Pagado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]

    reference = models.CharField(
        max_length=100,
        unique=True,
        help_text="Referencia única del pago (ej: PAY-20260513-0001)"
    )
    company = models.ForeignKey(
        'core_companies.Company',
        on_delete=models.CASCADE,
        db_index=True,
        help_text="Empresa beneficiaria"
    )
    bank_account = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        help_text="Cuenta bancaria destino"
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Monto total del pago"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Moneda del pago (USD, EUR, etc.)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Estado actual del pago"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción o notas adicionales"
    )
    approved_by = models.ForeignKey(
        'auth.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_payouts',
        help_text="Usuario que aprobó el pago"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de aprobación"
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de pago efectivo"
    )
    bank_reference = models.CharField(
        max_length=200,
        blank=True,
        help_text="Referencia bancaria del pago"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Mensaje de error si el pago falla"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"{self.reference} - {self.company} (${self.total_amount})"


class PayoutItem(models.Model):
    """Líneas individuales de un pago (por orden o compra)"""
    payout = models.ForeignKey(
        Payout,
        on_delete=models.CASCADE,
        related_name='items',
        db_index=True,
        help_text="Pago al que pertenece esta línea"
    )
    order = models.ForeignKey(
        'sales.Order',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Orden de venta asociada (si aplica)"
    )
    purchase_order = models.ForeignKey(
        'purchases.PurchaseOrder',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Orden de compra asociada (si aplica)"
    )
    gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Monto bruto antes de retenciones"
    )
    retention_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Monto retenido"
    )
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Monto neto a pagar (bruto - retenciones)"
    )
    commission_type = models.CharField(
        max_length=50,
        help_text="Tipo de comisión aplicada"
    )
    description = models.CharField(
        max_length=200,
        help_text="Descripción breve del concepto"
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Línea de Pago'
        verbose_name_plural = 'Líneas de Pago'

    def __str__(self):
        return f"{self.payout.reference} - {self.description}"


class PayoutConfig(models.Model):
    """Configuración de pagos por empresa"""
    SCHEDULE_CHOICES = [
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
    ]

    company = models.OneToOneField(
        'core_companies.Company',
        on_delete=models.CASCADE,
        related_name='payout_config',
        primary_key=True,
        help_text="Empresa (relación uno a uno)"
    )
    auto_approve = models.BooleanField(
        default=False,
        help_text="Aprobar pagos automáticamente"
    )
    retention_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Porcentaje de retención (ej: 10.0 = 10%)"
    )
    retain_until_threshold = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=100.0,
        validators=[MinValueValidator(0)],
        help_text="Monto mínimo acumulado para generar pago"
    )
    payout_schedule = models.CharField(
        max_length=20,
        choices=SCHEDULE_CHOICES,
        default='weekly',
        help_text="Frecuencia de generación de pagos"
    )
    notify_emails = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de correos para notificaciones"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de Pagos'
        verbose_name_plural = 'Configuraciones de Pagos'

    def __str__(self):
        return f"Configuración - {self.company}"


class CommissionRecord(models.Model):
    """Registro individual de comisión generada por una orden/compra."""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('paid', 'Pagada'),
        ('cancelled', 'Cancelada'),
    ]

    order = models.ForeignKey(
        'sales.Order',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='commission_records'
    )
    purchase_order = models.ForeignKey(
        'purchases.PurchaseOrder',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='commission_records'
    )
    company = models.ForeignKey(
        'core_companies.Company',
        on_delete=models.CASCADE,
        db_index=True
    )
    commission_rule = models.ForeignKey(
        'CommissionRule',
        on_delete=models.PROTECT
    )
    gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Comisión antes de retención"
    )
    retention_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Retención SRI aplicada"
    )
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Neto a pagar"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    payout_item = models.ForeignKey(
        'PayoutItem',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='commission_records'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Fecha de creación del registro"
    )
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['company', 'status', 'created_at']),
        ]
        ordering = ['-created_at']
        verbose_name = 'Registro de Comisión'
        verbose_name_plural = 'Registros de Comisión'

    def __str__(self):
        if self.order:
            ref = f"Order {self.order.order_number}"
        elif self.purchase_order:
            ref = f"PO {self.purchase_order.po_number}"
        else:
            ref = "Sin referencia"
        return f"{ref} — {self.net_amount} ({self.status})"
