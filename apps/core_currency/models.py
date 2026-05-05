# Módulo Core: Currency (Monedas)
from django.db import models


class Currency(models.Model):
    """Moneda soportada por el sistema"""
    code = models.CharField(max_length=3, unique=True, help_text="USD, EUR, COP, etc.")
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10, default="$")
    is_base = models.BooleanField(
        default=False,
        help_text="Moneda base del sistema (solo una puede ser base)"
    )
    decimal_places = models.IntegerField(default=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Moneda"
        verbose_name_plural = "Monedas"
        ordering = ["code"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class ExchangeRate(models.Model):
    """Histórico de tasas de cambio"""
    from_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="rates_from"
    )
    to_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="rates_to"
    )
    rate = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        help_text="1 unidad from_currency = rate to_currency"
    )
    date = models.DateField()
    source = models.CharField(
        max_length=50,
        default="manual",
        choices=[
            ("manual", "Manual"),
            ("bc", "Banco Central"),
            ("openexchangerates", "Open Exchange Rates"),
            ("fixer", "Fixer.io"),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tasa de Cambio"
        verbose_name_plural = "Tasas de Cambio"
        unique_together = ("from_currency", "to_currency", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.from_currency} → {self.to_currency}: {self.rate} ({self.date})"
