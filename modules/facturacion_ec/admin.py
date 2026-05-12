"""
Admin — Plugin Facturación Electrónica Ecuador (SRI)
"""
from django.contrib import admin
from .models import (
    SriAmbiente, SriTipoComprobante, SriImpuesto,
    CompanyLicense, InvoiceSRIExtension,
    SRISendLog
)


@admin.register(SriAmbiente)
class SriAmbienteAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    readonly_fields = ("id",)


@admin.register(SriTipoComprobante)
class SriTipoComprobanteAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "description")
    search_fields = ("name", "code")


@admin.register(SriImpuesto)
class SriImpuestoAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "percent", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(CompanyLicense)
class CompanyLicenseAdmin(admin.ModelAdmin):
    list_display = (
        "company", "license_type", "is_active", "is_trial",
        "expires_at", "invoices_this_month_display"
    )
    list_filter = ("is_active", "is_trial", "license_type")
    search_fields = ("company__name",)
    readonly_fields = ("activated_at", "invoices_this_month", "current_month_year")

    def invoices_this_month_display(self, obj):
        limit = obj.license_type.max_invoices_per_month if obj.license_type else 0
        if limit == 0:
            return f"{obj.invoices_this_month} / ∞"
        return f"{obj.invoices_this_month} / {limit}"
    invoices_this_month_display.short_description = "Facturas este mes"


@admin.register(InvoiceSRIExtension)
class InvoiceSRIExtensionAdmin(admin.ModelAdmin):
    """
    Admin para extensiones SRI de facturas.

    Solo lectura — campos generados por el pipeline SRI.
    """
    list_display = (
        "invoice_number", "ambiente", "tipo_comprobante",
        "access_key", "sri_status", "sri_authorization_date"
    )
    list_filter = ("sri_status", "ambiente", "tipo_comprobante")
    search_fields = ("invoice__number", "access_key")
    readonly_fields = (
        "invoice", "tipo_comprobante", "ambiente", "access_key",
        "xml_content", "xml_original_hash", "sri_status",
        "sri_authorization_date", "sri_message", "sri_xml_autorizado",
        "created_at", "updated_at"
    )

    def invoice_number(self, obj):
        return obj.invoice.number
    invoice_number.short_description = "Factura"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SRISendLog)
class SRISendLogAdmin(admin.ModelAdmin):
    list_display = ("invoice_ref", "timestamp", "success", "response_code")
    list_filter = ("success", "timestamp")
    search_fields = ("invoice_extension__invoice__number", "endpoint")
    readonly_fields = ("timestamp",)

    def invoice_ref(self, obj):
        return obj.invoice_extension.invoice.number
    invoice_ref.short_description = "Factura"
