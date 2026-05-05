# Módulo Core: Config (Configuraciones Globales del Sistema)
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class ConfigKey(models.Model):
    """
    Define una clave de configuración disponible en el sistema.

    Ejemplo:
    - key: "default_currency"
    - value_type: "char"
    - default_value: "USD"
    """
    VALUE_TYPES = [
        ("string", "Texto"),
        ("char", "Carácter"),
        ("integer", "Número entero"),
        ("float", "Número decimal"),
        ("decimal", "Número decimal (precisión)"),
        ("boolean", "Booleano"),
        ("json", "JSON"),
        ("date", "Fecha"),
        ("datetime", "Fecha y hora"),
    ]

    key = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255)
    value_type = models.CharField(max_length=20, choices=VALUE_TYPES)
    default_value = models.TextField(blank=True, help_text="Valor por defecto")
    is_required = models.BooleanField(default=False)
    is_system = models.BooleanField(
        default=False,
        help_text="Clave del sistema (no eliminable)"
    )
    group = models.CharField(
        max_length=50,
        default="general",
        help_text="Grupo para organizar en UI (general, financial, sri, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Clave de Configuración"
        verbose_name_plural = "Claves de Configuración"
        ordering = ["group", "key"]

    def __str__(self):
        return f"{self.key} ({self.value_type})"


class SystemConfig(models.Model):
    """
    Valor concreto de configuración para empresa específica.

    Si company es NULL → valor global (todas las empresas)
    Si company tiene valor → override por empresa
    """
    key = models.ForeignKey(ConfigKey, on_delete=models.CASCADE)
    company = models.ForeignKey(
        "core_companies.Company",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="config_overrides"
    )
    value = models.TextField(help_text="Valor almacenado como texto, se cast según tipo")

    # Validación adicional según tipo
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadata extra (opciones, constraints)"
    )

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_configs"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="updated_configs"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
        unique_together = ("key", "company")
        ordering = ["key__group", "key__key"]

    def __str__(self):
        entity = self.company.name if self.company else "Global"
        return f"{self.key.key} = {self.value} ({entity})"

    def get_typed_value(self):
        """Devuelve el valor casteado al tipo definido"""
        vt = self.key.value_type
        raw = self.value

        try:
            if vt in ("string", "char"):
                return str(raw)
            elif vt == "integer":
                return int(raw)
            elif vt in ("float", "decimal"):
                return float(raw)
            elif vt == "boolean":
                return raw.lower() in ("true", "1", "yes", "on")
            elif vt == "json":
                import json
                return json.loads(raw)
            elif vt == "date":
                from datetime import datetime
                return datetime.strptime(raw, "%Y-%m-%d").date()
            elif vt == "datetime":
                from datetime import datetime
                return datetime.fromisoformat(raw)
            return raw
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.get_effective_value()

    def get_effective_value(self):
        """
        Obtiene el valor efectivo: lookup por empresa,
        fallback a global, fallback a default de ConfigKey.
        """
        from django.utils import timezone

        # 1. Buscar override por empresa específica
        if self.company:
            try:
                override = SystemConfig.objects.get(
                    key=self.key,
                    company=self.company
                )
                return override.value
            except SystemConfig.DoesNotExist:
                pass

        # 2. Buscar valor global
        try:
            global_val = SystemConfig.objects.get(
                key=self.key,
                company=None
            )
            return global_val.value
        except SystemConfig.DoesNotExist:
            pass

        # 3. Devolver default de la clave
        return self.key.default_value


def get_config(key_name, company=None, default=None):
    """
    Helper: obtiene un valor de configuración.

    Uso:
        get_config("default_currency") → "USD"
        get_config("tax_rate_iva", company=my_company) → "12"
    """
    try:
        config_key = ConfigKey.objects.get(key=key_name)
        qs = SystemConfig.objects.filter(key=config_key)
        if company:
            qs = qs.filter(company=company)
        else:
            qs = qs.filter(company=None)
        cfg = qs.first()
        if cfg:
            return cfg.get_typed_value()
    except ConfigKey.DoesNotExist:
        pass
    return default


# Configuraciones predefinidas por defecto (seed data)
DEFAULT_CONFIG_KEYS = [
    # Generales
    {
        "key": "default_currency",
        "description": "Moneda base del sistema",
        "value_type": "char",
        "default_value": "USD",
        "is_required": True,
        "group": "general",
    },
    {
        "key": "default_country",
        "description": "País por defecto (ISO 3166-1)",
        "value_type": "char",
        "default_value": "EC",
        "is_required": True,
        "group": "general",
    },
    {
        "key": "date_format",
        "description": "Formato de fecha (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD)",
        "value_type": "string",
        "default_value": "DD/MM/YYYY",
        "group": "general",
    },
    {
        "key": "decimal_separator",
        "description": "Separador decimal (',', '.')",
        "value_type": "char",
        "default_value": ",",
        "group": "general",
    },
    {
        "key": "thousands_separator",
        "description": "Separador de miles ('.', ',', ' ')",
        "value_type": "char",
        "default_value": ".",
        "group": "general",
    },
    # Financieros
    {
        "key": "default_tax_rate_iva",
        "description": "IVA por defecto (%)",
        "value_type": "integer",
        "default_value": "12",
        "group": "financial",
    },
    {
        "key": "default_tax_rate_ice",
        "description": "ICE por defecto (%) - Impuesto a Consumos Especiales",
        "value_type": "integer",
        "default_value": "0",
        "group": "financial",
    },
    {
        "key": "default_tax_rate_ir",
        "description": "Impuesto a la Renta retención en la fuente (%)",
        "value_type": "integer",
        "default_value": "2",
        "group": "financial",
    },
    # Facturación Ecuador (SRI)
    {
        "key": "sri_ambiente_default",
        "description": "Ambiente SRI por defecto (1=Pruebas, 2=Producción)",
        "value_type": "integer",
        "default_value": "1",
        "group": "sri",
    },
    {
        "key": "sri_certificate_expiry_warning_days",
        "description": "Días de antelación para alerta de vencimiento certificado",
        "value_type": "integer",
        "default_value": "30",
        "group": "sri",
    },
    # Email
    {
        "key": "smtp_host",
        "description": "Servidor SMTP para envío de emails",
        "value_type": "string",
        "default_value": "",
        "group": "email",
    },
    {
        "key": "smtp_port",
        "description": "Puerto SMTP",
        "value_type": "integer",
        "default_value": "587",
        "group": "email",
    },
]


def seed_default_config_keys():
    """Crea las claves de configuración por defecto (una sola vez)"""
    existing = set(ConfigKey.objects.values_list("key", flat=True))

    for cfg in DEFAULT_CONFIG_KEYS:
        if cfg["key"] not in existing:
            ConfigKey.objects.create(**cfg)
