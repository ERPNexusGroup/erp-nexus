from django.contrib import admin
from .models import BankAccount, CommissionRule, Payout, PayoutItem, PayoutConfig


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('company', 'bank_code', 'account_number', 'account_type', 'account_holder_name', 'is_active', 'is_default')
    list_filter = ('bank_code', 'account_type', 'is_active', 'is_default')
    search_fields = ('account_number', 'account_holder_name', 'rut')
    ordering = ('company', '-is_default', '-created_at')


@admin.register(CommissionRule)
class CommissionRuleAdmin(admin.ModelAdmin):
    list_display = ('module', 'commission_type', 'percentage', 'fixed_amount', 'min_amount', 'max_amount', 'is_active')
    list_filter = ('module', 'commission_type', 'is_active')
    search_fields = ('module', 'created_by')
    ordering = ('module', '-created_at')


class PayoutItemInline(admin.TabularInline):
    model = PayoutItem
    extra = 0
    readonly_fields = ('gross_amount', 'retention_amount', 'net_amount', 'commission_type', 'description')
    fields = ('order', 'purchase_order', 'gross_amount', 'retention_amount', 'net_amount', 'commission_type', 'description')
    can_delete = False


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('reference', 'company', 'bank_account', 'total_amount', 'currency', 'status', 'paid_at')
    list_filter = ('status', 'currency', 'company', 'bank_account__bank_code')
    search_fields = ('reference', 'bank_reference', 'company__name')
    readonly_fields = ('reference', 'created_at', 'updated_at')
    inlines = [PayoutItemInline]
    ordering = ('-created_at',)

    fieldsets = (
        ('Información General', {
            'fields': ('reference', 'company', 'bank_account', 'total_amount', 'currency', 'status', 'description')
        }),
        ('Aprobación', {
            'fields': ('approved_by', 'approved_at'),
            'classes': ('collapse',),
        }),
        ('Pago', {
            'fields': ('paid_at', 'bank_reference'),
            'classes': ('collapse',),
        }),
        ('Error', {
            'fields': ('error_message',),
            'classes': ('collapse',),
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ['paid', 'cancelled']:
            return self.readonly_fields + ('company', 'bank_account', 'total_amount', 'currency', 'description')
        return self.readonly_fields


@admin.register(PayoutItem)
class PayoutItemAdmin(admin.ModelAdmin):
    list_display = ('payout', 'description', 'gross_amount', 'retention_amount', 'net_amount')
    list_filter = ('payout__status', 'commission_type')
    search_fields = ('payout__reference', 'description')
    ordering = ('payout', 'id')


@admin.register(PayoutConfig)
class PayoutConfigAdmin(admin.ModelAdmin):
    list_display = ('company', 'auto_approve', 'retention_rate', 'retain_until_threshold', 'payout_schedule')
    list_filter = ('auto_approve', 'payout_schedule')
    search_fields = ('company__name',)
    ordering = ('company',)
