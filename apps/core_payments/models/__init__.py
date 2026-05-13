# apps/core_payments/models.py
"""
Payout Automation — Modelos para pagos de comisiones via transferencia bancaria.

Flujo:
1. Sale generada → Commission creada (status=PENDING)
2. Batch diario crea Payout agrupado por usuario
3. SRI/Banco procesa transferencia → webhook confirma → Payout PAID
4. Commission marcada PAID + paid_at
"""

from datetime import timedelta, datetime

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BankAccount(models.Model):
    """Cuenta bancaria de un usuario para recibir comisiones."""

    class AccountType(models.TextChoices):
        SAVINGS = 'SAVINGS', _('Ahorros')
        CHECKING = 'CHECKING', _('Corriente')

    id = models.UUIDField(primary_key=True, default=settings.UUID_FIELD_DEFAULT, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bank_accounts'
    )
    bank_code = models.CharField(max_length=10, help_text=_("Código banco SRI (ej: '01' Banco Pichincha)"))
    bank_name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=AccountType.choices, default=AccountType.SAVINGS)
    account_number = models.CharField(max_length=50)
    holder_name = models.CharField(max_length=200)
    holder_identification = models.CharField(max_length=20, help_text=_("Cédula o RUC"))
    is_verified = models.BooleanField(
        default=False,
        help_text=_("Verificada por admin (se require para recibir pagos)")
    )
    is_default = models.BooleanField(
        default=False,
        help_text=_("Cuenta predeterminada para nuevos pagos")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Bank Account")
        verbose_name_plural = _("Bank Accounts")
        unique_together = [('user', 'is_default')]  # solo 1 default por usuario
        indexes = [
            models.Index(fields=['user', 'is_verified']),
            models.Index(fields=['bank_code', 'account_number']),
        ]

    def __str__(self):
        return f"{self.bank_name} — {self.account_number} ({self.user.email})"


class Commission(models.Model):
    """Comisión generada por una venta ( Marketplace )."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pendiente')
        PROCESSING = 'PROCESSING', _('Procesando')
        PAID = 'PAID', _('Pagada')
        FAILED = 'FAILED', _('Fallida')
        CANCELLED = 'CANCELLED', _('Cancelada')

    id = models.UUIDField(primary_key=True, default=settings.UUID_FIELD_DEFAULT, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='commissions'
    )
    sale = models.ForeignKey(
        'sales.Order',
        on_delete=models.PROTECT,
        related_name='commissions'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    description = models.CharField(max_length=255, blank=True)
    payout = models.ForeignKey(
        'Payout',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='commissions'
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Commission")
        verbose_name_plural = _("Commissions")
        indexes = [
            models.Index(fields=['user', 'status', 'created_at']),
            models.Index(fields=['sale']),
        ]

    def __str__(self):
        return f"Commission {self.id} — {self.amount} ({self.status})"


class Payout(models.Model):
    """Transferencia bancaria que agrupa una o varias comisiones."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pendiente')
        PROCESSING = 'PROCESSING', _('Procesando')
        PAID = 'PAID', _('Pagada')
        FAILED = 'FAILED', _('Fallida')
        CANCELLED = 'CANCELLED', _('Cancelada')

    class Provider(models.TextChoices):
        SRI = 'SRI', _('SRI (Transferencia Bancaria)')
        NUBI = 'NUBI', _('Nubi (Pago Móvil)')
        MANUAL = 'MANUAL', _('Pago Manual')

    id = models.UUIDField(primary_key=True, default=settings.UUID_FIELD_DEFAULT, editable=False)
    # Vincular a una comisión representativa (la primera del batch)
    commission = models.ForeignKey(
        Commission,
        on_delete=models.PROTECT,
        related_name='lead_payout',
        help_text=_("Comisión representativa del batch (para tracking)")
    )
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name='payouts'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    provider = models.CharField(max_length=20, choices=Provider.choices, default=Provider.SRI)
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Número de transisión asignado por el banco")
    )
    provider_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("ID de transacción en sistema del proveedor")
    )
    provider_response = models.JSONField(
        null=True,
        blank=True,
        help_text=_("Respuesta raw del proveedor (JSON/XML)")
    )
    error_message = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Payout")
        verbose_name_plural = _("Payouts")
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['commission']),
            models.Index(fields=['bank_account', 'status']),
        ]

    def __str__(self):
        return f"Payout {self.id} — {self.amount} ({self.status})"

    @property
    def associated_commissions(self):
        """Retorna todas las comisiones asociadas a este payout (misma fecha + usuario)."""
        # Por ahora solo la comisión vinculada directa
        return [self.commission]

    def mark_as_paid(self, reference_number: str, provider_transaction_id: str = None):
        """Marca payout como pagado y actualiza comisiones asociadas."""
        self.status = self.Status.PAID
        self.reference_number = reference_number
        self.provider_transaction_id = provider_transaction_id or reference_number
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'reference_number', 'provider_transaction_id', 'paid_at', 'updated_at'])

        # Marcar comisiones como PAID
        for comm in [self.commission]:  # TODO: extender a múltiples commissions
            comm.status = Commission.Status.PAID
            comm.paid_at = timezone.now()
            comm.save(update_fields=['status', 'paid_at', 'updated_at'])


class PayoutSchedule(models.Model):
    """Configuración de schedule automático de pagos por usuario."""

    class ScheduleFrequency(models.TextChoices):
        DAILY = 'DAILY', _('Diario')
        WEEKLY = 'WEEKLY', _('Semanal')
        MONTHLY = 'MONTHLY', _('Mensual')
        MANUAL = 'MANUAL', _('Manual')

    id = models.UUIDField(primary_key=True, default=settings.UUID_FIELD_DEFAULT, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payout_schedule'
    )
    frequency = models.CharField(max_length=20, choices=ScheduleFrequency.choices, default=ScheduleFrequency.DAILY)
    min_payout_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10.00,
        help_text=_("Mínimo acumulado para generar payout")
    )
    is_active = models.BooleanField(default=True)
    next_run = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Payout Schedule")
        verbose_name_plural = _("Payout Schedules")

    def __str__(self):
        return f"Schedule — {self.user.email} ({self.frequency})"

    def calculate_next_run(self) -> datetime:
        """Calcula próxima ejecución basada en frecuencia."""
        if self.frequency == self.ScheduleFrequency.DAILY:
            return timezone.now() + timedelta(days=1)
        elif self.frequency == self.ScheduleFrequency.WEEKLY:
            return timezone.now() + timedelta(weeks=1)
        elif self.frequency == self.ScheduleFrequency.MONTHLY:
            return timezone.now() + timedelta(days=30)
        return None
