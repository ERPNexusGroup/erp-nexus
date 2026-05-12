"""
apps.facturacion — Core de facturación local (independiente de SRI)

Responsabilidades:
- Modelos base: Customer, Invoice, InvoiceLine, Quote, QuoteLine
- Lógica de negocio local: numeración, cálculos de totales, estados
- API REST para facturas, cotizaciones, clientes
- Signals para auto-numeración y cálculos automáticos
- Admin integrado

NO incluye:
- Código SRI específico (ambi, tipo comprobante, firma digital, SOAP)
- Validaciones SRI (se delegan al plugin modules.facturacion_ec)
"""

from django.apps import AppConfig


class FacturacionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.facturacion"
    verbose_name = "Facturación Core"

    def ready(self):
        """Import signals para registrar handlers"""
        import apps.facturacion.signals  # noqa
