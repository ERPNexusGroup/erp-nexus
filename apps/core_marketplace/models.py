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
    python_dependencies = models.JSONField(default=dict, blank=True, help_text='Python package dependencies')
    system_dependencies = models.JSONField(default=dict, blank=True, help_text='System binary dependencies')
    documentation_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, default='', help_text='Descripción del módulo para marketplace y catálogo')

    # License metadata
    is_licensed = models.BooleanField(default=False, help_text='If True, module requires a valid license to install')
    license_required = models.BooleanField(default=False, help_text='If True, a license key is mandatory')
    trial_days = models.IntegerField(default=0, help_text='Number of trial days (0 = no trial)')
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text='Monthly subscription price')
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text='Yearly subscription price')

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


# ═══════════════════════════════════════════════════════════════
# License System — ModuleLicense
# ═══════════════════════════════════════════════════════════════
class ModuleLicense(models.Model):
    """License for a marketplace module.

    Supports: free, trial, paid, perpetual licenses.
    Tracks seat count and expiry.
    """

    LICENSE_TYPES = [
        ('free', 'Free / Open Source'),
        ('trial', 'Trial (30 days)'),
        ('paid', 'Paid Subscription'),
        ('perpetual', 'Perpetual License'),
    ]

    module = models.ForeignKey(
        ModuleCatalogItem,
        on_delete=models.CASCADE,
        related_name='licenses',
        help_text='Module this license applies to',
    )
    license_key = models.CharField(
        max_length=100,
        unique=True,
        help_text='Unique license key (auto-generated)',
    )
    license_type = models.CharField(
        max_length=20,
        choices=LICENSE_TYPES,
        default='free',
    )
    valid_from = models.DateTimeField(
        auto_now_add=True,
        help_text='License activation date',
    )
    valid_until = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Expiry date (null = perpetual)',
    )
    max_seats = models.IntegerField(
        default=1,
        help_text='Maximum number of installations/seats allowed',
    )
    used_seats = models.IntegerField(
        default=0,
        help_text='Current number of active installations',
    )
    company = models.ForeignKey(
        'core_companies.Company',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text='Company this license is assigned to',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether license can be used for new installs',
    )
    features = models.JSONField(
        default=dict,
        blank=True,
        help_text='Extra features {"support": "premium", "updates": true}',
    )
    notes = models.TextField(
        blank=True,
        default='',
        help_text='Internal notes about this license',
    )

    class Meta:
        verbose_name = 'Module License'
        verbose_name_plural = 'Module Licenses'
        ordering = ['-valid_from']
        indexes = [
            models.Index(fields=['license_key']),
            models.Index(fields=['module', 'is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.module.technical_name} — {self.license_key[:12]}... ({self.get_license_type_display()})"

    @property
    def is_valid(self) -> bool:
        """Check if license is currently valid (not expired, active, seats available)."""
        if not self.is_active:
            return False
        now = timezone.now()
        if self.valid_until and now > self.valid_until:
            return False
        if self.used_seats >= self.max_seats:
            return False
        return True

    @property
    def remaining_seats(self) -> int:
        """Number of remaining installations allowed."""
        return max(0, self.max_seats - self.used_seats)

    def increment_usage(self) -> None:
        """Increment used_seats (called on successful install)."""
        self.used_seats = models.F('used_seats') + 1
        self.save(update_fields=['used_seats'])

    def decrement_usage(self) -> None:
        """Decrement used_seats (called on uninstall)."""
        self.used_seats = models.F('used_seats') - 1
        self.save(update_fields=['used_seats'])


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
