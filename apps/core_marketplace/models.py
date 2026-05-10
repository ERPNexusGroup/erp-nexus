from django.db import models
from django.utils import timezone


class ModuleCatalogItem(models.Model):
    MODULE_TYPES = [
        ('essential', 'Essential (core)'),
        ('optional', 'Optional Plugin'),
        ('plugin', 'Third-party Plugin'),
    ]

    technical_name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200, blank=True)
    version = models.CharField(max_length=50)
    module_type = models.CharField(max_length=20, choices=MODULE_TYPES, default='optional')
    repo_url = models.URLField(max_length=500, blank=True, null=True)
    min_erp_version = models.CharField(max_length=50, blank=True, help_text='Minimum ERP version required')
    max_erp_version = models.CharField(max_length=50, blank=True, null=True, help_text='Maximum ERP version compatible')
    python_dependencies = models.JSONField(default=dict, blank=True, help_text='{"packages": ["celery", "redis"]}')
    system_dependencies = models.JSONField(default=dict, blank=True, help_text='{"bin": ["wkhtmltopdf"], "apt": []}')
    documentation_url = models.URLField(blank=True, null=True)
    installed_path = models.CharField(max_length=500, blank=True, null=True)
    installed_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, default='active')
    is_active = models.BooleanField(default=True)
    django_app = models.CharField(max_length=200, blank=True, null=True)
    admin_menu = models.JSONField(blank=True, null=True)

    def __str__(self) -> str:
        name = self.display_name or self.technical_name
        return f"{name} ({self.version})"

    def mark_inactive(self) -> None:
        self.status = 'inactive'
        self.is_active = False
        self.save(update_fields=['status', 'is_active'])

    def touch_installed(self) -> None:
        self.installed_at = timezone.now()
        self.status = 'active'
        self.is_active = True
        self.save(update_fields=['installed_at', 'status', 'is_active'])


class EnabledModule(models.Model):
    technical_name = models.CharField(max_length=100, unique=True)
    django_app = models.CharField(max_length=200)
    status = models.CharField(max_length=20, default='active')
    enabled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.technical_name} ({self.status})"


class ModuleDownload(models.Model):
    module_name = models.CharField(max_length=100, db_index=True)
    version = models.CharField(max_length=50)
    source = models.CharField(max_length=500)
    downloaded_by = models.CharField(max_length=150, blank=True, default='')
    downloaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('pending', 'Pending'),
        ],
        default='pending',
    )
    error_message = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Module Download'
        verbose_name_plural = 'Module Downloads'
        ordering = ['-downloaded_at']

    def __str__(self) -> str:
        return f"{self.module_name} v{self.version} ({self.status})"


class ModuleRegistry(models.Model):
    SOURCE_TYPES = [
        ('github', 'GitHub Repository'),
        ('git', 'Git Repository'),
        ('url', 'URL (JSON catalog)'),
        ('local', 'Local Path'),
    ]

    name = models.CharField(max_length=100, unique=True)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, default='github')
    url = models.URLField(help_text='URL del repositorio o catálogo', max_length=500)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    priority = models.IntegerField(default=50, help_text='Prioridad de búsqueda (mayor = primero)')
    cached_modules = models.JSONField(blank=True, default=dict)
    last_sync = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Module Registry'
        verbose_name_plural = 'Module Registries'
        ordering = ['-priority', 'name']

    def __str__(self) -> str:
        return f"{self.name} ({self.get_source_type_display()})"
