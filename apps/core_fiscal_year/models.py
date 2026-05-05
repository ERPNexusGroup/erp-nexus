# Módulo Core: Fiscal Year (Años Fiscales y Períodos)
from django.conf import settings
from django.db import models
from django.utils import timezone


class FiscalYear(models.Model):
    """
    Año fiscal de una empresa.

    Permite bloquear períodos cerrados y gestionar cierres contables.
    """
    company = models.ForeignKey(
        "core_companies.Company",
        on_delete=models.CASCADE,
        related_name="fiscal_years"
    )
    name = models.CharField(
        max_length=20,
        help_text="Ej: 2024, Año 2024"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(
        default=False,
        help_text="Si el año fiscal está cerrado (no se pueden crear más asientos)"
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fiscal_years_closed"
    )

    # Control de período actual
    is_current = models.BooleanField(
        default=False,
        help_text="Año fiscal activo/actual"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Año Fiscal"
        verbose_name_plural = "Años Fiscales"
        unique_together = ("company", "name")
        ordering = ["-name"]

    def __str__(self):
        return f"{self.company.name} - {self.name}"

    def save(self, *args, **kwargs):
        """Solo un año fiscal puede ser current por empresa"""
        if self.is_current:
            FiscalYear.objects.filter(
                company=self.company,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    @property
    def is_open(self):
        """Retorna True si el año no está cerrado"""
        return not self.is_closed


class FiscalPeriod(models.Model):
    """
    Período contable dentro de un año fiscal.

    Ejemplo: Enero 2024, Febrero 2024, Q1 2024, etc.
    """
    PERIOD_TYPES = [
        ("month", "Mensual"),
        ("quarter", "Trimestral"),
        ("semester", "Semestral"),
        ("custom", "Personalizado"),
    ]

    fiscal_year = models.ForeignKey(
        FiscalYear,
        on_delete=models.CASCADE,
        related_name="periods"
    )
    name = models.CharField(max_length=50, help_text="Ej: Enero 2024, Q1 2024")
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES, default="month")
    start_date = models.DateField()
    end_date = models.DateField()
    sequence = models.IntegerField(
        default=0,
        help_text="Orden dentro del año fiscal (1=Enero, 2=Febrero, etc.)"
    )

    # Control de cierre
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fiscal_periods_closed"
    )

    # Si es período abierto (permite asientos)
    is_open = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Período Fiscal"
        verbose_name_plural = "Períodos Fiscales"
        unique_together = ("fiscal_year", "name")
        ordering = ["sequence"]

    def __str__(self):
        return f"{self.fiscal_year.name} - {self.name}"

    def can_post_entries(self):
        """Retorna True si el período está abierto y el año no está cerrado"""
        return self.is_open and self.fiscal_year.is_open


def get_current_fiscal_year(company):
    """Helper: obtiene el año fiscal actual de una empresa"""
    return FiscalYear.objects.filter(
        company=company,
        is_current=True
    ).first()


def get_current_fiscal_period(company):
    """Helper: obtiene el período fiscal actual (mes)"""
    from datetime import date
    today = date.today()
    try:
        fy = FiscalYear.objects.get(company=company, is_current=True)
        return fy.periods.filter(
            start_date__lte=today,
            end_date__gte=today,
            is_open=True
        ).first()
    except FiscalYear.DoesNotExist:
        return None


def close_fiscal_period(period, user):
    """Cierra un período fiscal (no más asientos)"""
    if not period.is_open:
        return False, "Período ya cerrado"

    period.is_open = False
    period.is_closed = True
    period.closed_at = timezone.now()
    period.closed_by = user
    period.save()
    return True, "Período cerrado correctamente"


def reopen_fiscal_period(period, user):
    """Reabre un período cerrado (solo si el año no está cerrado)"""
    if period.fiscal_year.is_closed:
        return False, "No se puede reabrir: año fiscal cerrado"

    period.is_open = True
    period.is_closed = False
    period.closed_at = None
    period.closed_by = None
    period.save()
    return True, "Período reabierto"
