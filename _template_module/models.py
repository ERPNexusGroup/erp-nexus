"""
Modelos de mi_modulo.

Todos los modelos deben incluir `company` como ForeignKey obligatorio.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class CompanyBoundModel(models.Model):
    """
    Modelo base que incluye company + timestamps + created_by.
    Todos los modelos de negocio deben heredar de este.
    """
    company = models.ForeignKey(
        "core_companies.Company",
        on_delete=models.CASCADE,
        related_name="%(class)ss_lower"  # Auto: related_name='mi_modelos'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)ss_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


# Ejemplo: Modelo de negocio
class ExampleModel(CompanyBoundModel):
    """
    Ejemplo de modelo de negocio.
    Reemplazar por el modelo real del módulo.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Ejemplo"
        verbose_name_plural = "Ejemplos"
        unique_together = ("company", "name")

    def __str__(self):
        return self.name

    def calculate_total(self):
        """Método de ejemplo."""
        return self.amount * 1.12  # IVA 12%
