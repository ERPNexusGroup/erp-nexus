"""
Page Builder — Sistema de páginas web drag & drop.

Componentes disponibles:
  - heading: Título
  - text: Párrafo de texto
  - image: Imagen
  - button: Botón
  - columns: Layout de columnas
  - spacer: Espacio en blanco
  - divider: Línea divisoria
  - html: HTML personalizado
"""
from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class Page(models.Model):
    """
    Página web creada con el page builder.
    """
    STATUS_CHOICES = [
        ("draft", "Borrador"),
        ("published", "Publicado"),
        ("archived", "Archivado"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Layout: lista de componentes en formato JSON
    # Ejemplo: [{"type": "heading", "props": {"text": "Hola", "level": 1}}, ...]
    layout = models.JSONField(
        default=list,
        help_text="Lista de componentes del layout (JSON)",
    )

    # Metadata SEO
    meta_title = models.CharField(max_length=200, blank=True, default="")
    meta_description = models.TextField(blank=True, default="")

    # Autor
    created_by = models.CharField(max_length=150, blank=True, default="")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Página"
        verbose_name_plural = "Páginas"

    def __str__(self):
        return f"{self.title} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def publish(self):
        """Publica la página."""
        self.status = "published"
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at"])

    @property
    def component_count(self):
        return len(self.layout) if self.layout else 0

    @property
    def url(self):
        return f"/pages/{self.slug}/"


class Component(models.Model):
    """
    Componente reutilizable del page builder.
    """
    COMPONENT_TYPES = [
        ("heading", "Título"),
        ("text", "Texto"),
        ("image", "Imagen"),
        ("button", "Botón"),
        ("columns", "Columnas"),
        ("spacer", "Espacio"),
        ("divider", "Divisor"),
        ("html", "HTML personalizado"),
    ]

    name = models.CharField(max_length=100, unique=True)
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    description = models.TextField(blank=True, default="")

    # Props por defecto del componente
    default_props = models.JSONField(
        default=dict,
        help_text="Propiedades por defecto del componente",
    )

    # Template HTML del componente
    template_html = models.TextField(
        blank=True, default="",
        help_text="Template HTML con variables {{ prop }}",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["component_type", "name"]
        verbose_name = "Componente"
        verbose_name_plural = "Componentes"

    def __str__(self):
        return f"{self.name} ({self.component_type})"
