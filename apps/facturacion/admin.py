from django.contrib import admin
from .models import (
    Customer, Product, Invoice, InvoiceLine,
    SriAmbiente, SriTipoComprobante, SriImpuesto,
    LicenseType, CompanyLicense,
    SRISendLog, ElectronicDocument
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "identification_number", "identification_type", "email", "company", "is_active")
    list_filter = ("is_active", "identification_type", "company")
    search_fields = ("name", "identification_number", "email")
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "unit_price", "tax_percent", "company", "is_active")
    list_filter = ("company", "is_active")
    search_fields = ("code", "name")
    ordering = ("code",)


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 1
    fields = ("product", "description", "quantity", "unit_price", "tax_rate", "total")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "number", "date", "customer", "total",
        "sri_status", "ambiente_display", "created_by"
    )
    list_filter = ("sri_status", "ambiente", "date", "company")
    search_fields = ("number", "customer__name", "customer__identification_number", "access_key")
    date_hierarchy = "date"
    inlines = [InvoiceLineInline]
    actions = ["send_to_sri_action"]

    def ambiente_display(self, obj):
        return "Pruebas" if obj.ambiente == 1 else "Producción"
    ambiente_display.short_description = "Ambiente"

    def send_to_sri_action(self, request, queryset):
        """Acción admin: enviar facturas seleccionadas a SRI"""
        from .services import send_invoice_to_sri
        count = 0
        for invoice in queryset.filter(sri_status="pending"):
            result = send_invoice_to_sri(invoice.id)
            if result.get("success"):
                count += 1
        self.message_user(request, f"Enviadas {count} facturas a SRI")
    send_to_sri_action.short_description = "Enviar a SRI (seleccionadas)"


@admin.register(SRISendLog)
class SRISendLogAdmin(admin.ModelAdmin):
    list_display = ("invoice", "timestamp", "success", "response_code")
    list_filter = ("success", "timestamp")
    search_fields = ("invoice__number", "error_message")
    readonly_fields = [f.name for f in SRISendLog._meta.fields]
    date_hierarchy = "timestamp"


@admin.register(ElectronicDocument)
class ElectronicDocumentAdmin(admin.ModelAdmin):
    list_display = ("document_type", "number", "date", "company", "pdf_generated")
    list_filter = ("document_type", "pdf_generated", "company")
    search_fields = ("number", "access_key")
    date_hierarchy = "date"
    readonly_fields = ("access_key", "xml_original", "xml_signed", "xml_autorizado")


@admin.register(LicenseType)
class LicenseTypeAdmin(admin.ModelAdmin):
    list_display = ("display_name", "plan_id", "price_monthly_equivalent", "max_invoices_per_month", "allows_updates", "is_active")
    list_filter = ("is_active", "allows_updates")
    ordering = ("plan_id",)


@admin.register(CompanyLicense)
class CompanyLicenseAdmin(admin.ModelAdmin):
    list_display = ("company", "license_type", "is_active", "is_trial", "expires_at", "invoices_this_month_display")
    list_filter = ("is_active", "is_trial", "license_type")
    search_fields = ("company__name", "transaction_id")

    def invoices_this_month_display(self, obj):
        limit = obj.license_type.max_invoices_per_month
        if limit == 0:
            return f"{obj.invoices_this_month} / ∞"
        return f"{obj.invoices_this_month} / {limit}"
    invoices_this_month_display.short_description = "Facturas este mes"


# Catalogos SRI (readonly)
@admin.register(SriAmbiente)
class SriAmbienteAdmin(admin.ModelAdmin):
    list_display = ("code", "name")


@admin.register(SriTipoComprobante)
class SriTipoComprobanteAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "description")


@admin.register(SriImpuesto)
class SriImpuestoAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "percent", "is_active")
