# Módulo Core: Chart of Accounts (Plan de Cuentas)
from django.conf import settings
from django.db import models


class AccountType(models.Model):
    """Tipo de cuenta contable (Activo, Pasivo, Patrimonio, Ingreso, Gasto)"""
    code = models.CharField(max_length=10, unique=True)  # 1, 2, 3, 4, 5, 6
    name = models.CharField(max_length=100)
    nature = models.CharField(
        max_length=20,
        choices=[
            ("debit", "Deudora"),
            ("credit", "Acreedora"),
        ]
    )
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tipo de Cuenta"
        verbose_name_plural = "Tipos de Cuenta"
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Account(models.Model):
    """
    Cuenta contable individual.

    Para Ecuador, sigue formato SRI:
    - 1.1.01.001 (Clasificación estándar)
    - Códigos SRI para formulario 103/104
    """
    company = models.ForeignKey(
        "core_companies.Company",
        on_delete=models.CASCADE,
        related_name="accounts",
        help_text="Empresa a la que pertenece esta cuenta"
    )
    code = models.CharField(max_length=30, help_text="Ej: 1.1.01.001")
    name = models.CharField(max_length=200)
    account_type = models.ForeignKey(
        AccountType,
        on_delete=models.PROTECT,
        related_name="accounts",
        help_text="Tipo de cuenta (activo, pasivo, etc.)"
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
        help_text="Cuenta padre (para jerarquía)"
    )
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(
        default=False,
        help_text="Cuenta del sistema (no eliminable)"
    )

    # Campos específicos Ecuador/SRI
    sri_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="Código SRI para formularios 103/104"
    )
    sri_form_103 = models.BooleanField(
        default=False,
        help_text="Aparece en formulario 103 (Impuesto Renta)"
    )
    sri_form_104 = models.BooleanField(
        default=False,
        help_text="Aparece en formulario 104 (IVA)"
    )

    # Control
    allow_manual_entry = models.BooleanField(
        default=True,
        help_text="Permite asientos manuales en esta cuenta"
    )
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cuenta Contable"
        verbose_name_plural = "Cuentas Contables"
        unique_together = ("company", "code")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_full_path(self):
        """Devuelve la ruta jerárquica completa de la cuenta"""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return " / ".join(path)


class JournalEntry(models.Model):
    """
    Asiento contable vinculado a empresa (empresa puede ser NULL = global).

    Permite movimientos contables entre cuentas.
    """
    company = models.ForeignKey(
        "core_companies.Company",
        on_delete=models.CASCADE,
        related_name="journal_entries",
        null=True,
        blank=True,
        help_text="Empresa que registra el asiento (NULL = asiento global)"
    )
    date = models.DateField()
    reference = models.CharField(max_length=100, help_text="Referencia/Concepto")
    document_type = models.CharField(
        max_length=20,
        blank=True,
        help_text="Tipo documento (factura, nota, etc.)"
    )
    document_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Número documento relacionado"
    )
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True, blank=True)

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="journal_entries_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Asiento Contable"
        verbose_name_plural = "Asientos Contables"
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} - {self.reference}"


class JournalEntryLine(models.Model):
    """Línea de asiento contable (débito/crédito)"""
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name="lines"
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="journal_lines"
    )
    description = models.CharField(max_length=200, blank=True)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Línea de Asiento"
        verbose_name_plural = "Líneas de Asiento"

    def __str__(self):
        return f"{self.account.code}: {self.debit} / {self.credit}"
