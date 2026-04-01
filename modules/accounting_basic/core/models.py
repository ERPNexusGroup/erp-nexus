"""
Modelos del módulo accounting_basic.

Cuentas contables y asientos (journal entries).
"""
from django.db import models
from django.utils import timezone


class Account(models.Model):
    """
    Plan de cuentas contable.
    """
    ACCOUNT_TYPES = [
        ("asset", "Activo"),
        ("liability", "Pasivo"),
        ("equity", "Patrimonio"),
        ("income", "Ingreso"),
        ("expense", "Gasto"),
    ]

    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Código de cuenta (ej: 1.1.01.001)",
    )
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "Cuenta"
        verbose_name_plural = "Cuentas"

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def balance(self):
        """Balance actual de la cuenta."""
        debit = self.entries.filter(entry_type="debit").aggregate(
            total=models.Sum("amount")
        )["total"] or 0
        credit = self.entries.filter(entry_type="credit").aggregate(
            total=models.Sum("amount")
        )["total"] or 0
        return float(debit - credit)


class JournalEntry(models.Model):
    """
    Asiento contable (diario general).
    Cada asiento tiene múltiples líneas (debit/credit).
    """
    reference = models.CharField(
        max_length=50,
        unique=True,
        help_text="Referencia única del asiento (ej: ASI-000001)",
    )
    date = models.DateField(default=timezone.now)
    description = models.TextField(help_text="Descripción del asiento")
    is_posted = models.BooleanField(
        default=False,
        help_text="Si el asiento ya fue contabilizado (no editable)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Asiento"
        verbose_name_plural = "Asientos"

    def __str__(self):
        return f"{self.reference} — {self.description[:50]}"

    @property
    def total_debit(self):
        return float(
            self.lines.filter(entry_type="debit").aggregate(
                total=models.Sum("amount")
            )["total"] or 0
        )

    @property
    def total_credit(self):
        return float(
            self.lines.filter(entry_type="credit").aggregate(
                total=models.Sum("amount")
            )["total"] or 0
        )

    @property
    def is_balanced(self):
        """Un asiento válido debe tener debito = credito."""
        return abs(self.total_debit - self.total_credit) < 0.01

    def post(self):
        """Contabiliza el asiento (lo vuelve inmutable)."""
        if not self.is_balanced:
            raise ValueError(
                f"Asiento desbalanceado: Debe={self.total_debit}, Haber={self.total_credit}"
            )
        self.is_posted = True
        self.save(update_fields=["is_posted"])

        # Emitir evento
        from apps.core_events.bus import EventBus
        EventBus.emit(
            "accounting.entry_posted",
            "accounting_basic",
            {
                "reference": self.reference,
                "date": str(self.date),
                "total_debit": self.total_debit,
                "total_credit": self.total_credit,
            },
        )


class JournalLine(models.Model):
    """
    Línea de un asiento contable (debe o haber).
    """
    ENTRY_TYPES = [
        ("debit", "Debe"),
        ("credit", "Haber"),
    ]

    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="entries",
    )
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        verbose_name = "Línea de asiento"
        verbose_name_plural = "Líneas de asiento"

    def __str__(self):
        return f"{self.entry_type}: {self.account.code} — ${self.amount}"
