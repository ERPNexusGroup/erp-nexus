# apps/core_payments/admin.py
"""
Admin interface para Payout Automation.
Permite a usuarios gestionar cuentas bancarias y a admins aprobar/revisar payouts.
"""

from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import BankAccount, Payout, Commission, PayoutSchedule


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'bank_name', 'account_number_masked', 'account_type', 'is_verified', 'is_default']
    list_filter = ['is_verified', 'is_default', 'bank_name']
    search_fields = ['user__email', 'account_number', 'holder_name']
    readonly_fields = ['created_at', 'updated_at']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = _('User')

    def account_number_masked(self, obj):
        # Enmascarar número de cuenta por seguridad
        if len(obj.account_number) > 4:
            return '****' + obj.account_number[-4:]
        return obj.account_number
    account_number_masked.short_description = _('Account Number')

    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Bank Info'), {'fields': ('bank_code', 'bank_name', 'account_type', 'account_number', 'holder_name', 'holder_identification')}),
        (_('Status'), {'fields': ('is_verified', 'is_default')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'user', 'amount', 'currency', 'status', 'provider', 'reference_number', 'paid_at', 'created_at']
    list_filter = ['status', 'provider', 'created_at', 'paid_at']
    search_fields = ['id', 'reference_number', 'commission__user__email', 'bank_account__account_number']
    readonly_fields = ['id', 'created_at', 'updated_at', 'provider_response_formatted']
    date_hierarchy = 'created_at'
    actions = ['mark_as_paid', 'mark_as_failed', 'mark_as_pending']

    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = _('ID')

    def user(self, obj):
        return obj.commission.user.email
    user.short_description = _('User')

    def provider_response_formatted(self, obj):
        if obj.provider_response:
            import json
            return format_html('<pre>{}</pre>', json.dumps(obj.provider_response, indent=2))
        return '-'
    provider_response_formatted.short_description = _('Provider Response')

    fieldsets = (
        (_('Identification'), {'fields': ('id', 'commission', 'bank_account')}),
        (_('Amount'), {'fields': ('amount', 'currency')}),
        (_('Provider'), {'fields': ('provider', 'reference_number', 'provider_transaction_id')}),
        (_('Status'), {'fields': ('status', 'error_message', 'paid_at')}),
        (_('Provider Response'), {'fields': ('provider_response_formatted',), 'classes': ('collapse',)}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def mark_as_paid(self, request, queryset):
        for payout in queryset:
            payout.status = Payout.Status.PAID
            payout.paid_at = timezone.now()
            payout.save(update_fields=['status', 'paid_at', 'updated_at'])
        self.message_user(request, _("Selected payouts marked as PAID"))
    mark_as_paid.short_description = _("Mark selected as PAID")

    def mark_as_failed(self, request, queryset):
        queryset.update(status=Payout.Status.FAILED)
        self.message_user(request, _("Selected payouts marked as FAILED"))
    mark_as_failed.short_description = _("Mark selected as FAILED")

    def mark_as_pending(self, request, queryset):
        queryset.update(status=Payout.Status.PENDING, paid_at=None, reference_number='')
        self.message_user(request, _("Selected payouts marked as PENDING"))
    mark_as_pending.short_description = _("Mark selected as PENDING")


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    """Admin para comisiones (readonly mostly, se generan automáticamente)."""
    list_display = ['id_short', 'user', 'amount', 'status', 'payout_link', 'paid_at', 'created_at']
    list_filter = ['status', 'created_at', 'paid_at']
    search_fields = ['user__email', 'sale__id']
    readonly_fields = ['id', 'sale', 'user', 'amount', 'currency', 'description', 'payout', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = _('ID')

    def payout_link(self, obj):
        if obj.payout:
            return format_html('<a href="/admin/core_payments/payout/{}/change/">{}</a>',
                               obj.payout.id, str(obj.payout.id)[:8])
        return '-'
    payout_link.short_description = _('Payout')


@admin.register(PayoutSchedule)
class PayoutScheduleAdmin(admin.ModelAdmin):
    list_display = ['user', 'frequency', 'min_payout_amount', 'is_active', 'next_run']
    list_filter = ['frequency', 'is_active']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not obj.next_run:
            obj.next_run = obj.calculate_next_run()
        super().save_model(request, obj, form, change)
