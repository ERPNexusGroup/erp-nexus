"""
Models for print_manager: templates and jobs.
"""
from django.db import models


class PrintTemplate(models.Model):
    """Plantilla HTML para generación de PDFs."""
    name = models.CharField(max_length=100, unique=True)
    template_key = models.CharField(max_length=50, unique=True)  # ej: 'invoice', 'purchase_order'
    html_template = models.TextField(help_text="HTML template (Django template syntax)")
    css_styles = models.TextField(blank=True, default="", help_text="CSS inline o enlace a static")
    default_filename = models.CharField(max_length=200, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plantilla de Impresión"
        verbose_name_plural = "Plantillas de Impresión"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.template_key})"


class PrintJob(models.Model):
    """Log de generación de PDFs."""
    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("processing", "Procesando"),
        ("completed", "Completado"),
        ("failed", "Fallido"),
    ]

    template = models.ForeignKey(PrintTemplate, on_delete=models.PROTECT, related_name="jobs")
    context = models.JSONField(default=dict, blank=True)  # Datos para el template
    output_format = models.CharField(max_length=20, default="pdf")  # pdf, png (futuro)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    file_path = models.CharField(max_length=500, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Trabajo de Impresión"
        verbose_name_plural = "Trabajos de Impresión"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.template.template_key} — {self.status}"
