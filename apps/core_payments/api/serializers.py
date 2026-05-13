# apps/core_payments/api/serializers.py
"""
Serializers para Payout Automation API.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from ..models import BankAccount, Payout, Commission, PayoutSchedule


User = get_user_model()


class BankAccountSerializer(serializers.ModelSerializer):
    """Serializa cuentas bancarias del usuario."""

    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = BankAccount
        fields = [
            'id', 'user_email', 'bank_code', 'bank_name', 'account_type',
            'account_number', 'holder_name', 'holder_identification',
            'is_verified', 'is_default', 'created_at'
        ]
        read_only_fields = ['id', 'user_email', 'is_verified', 'created_at']

    def validate_account_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Número de cuenta debe ser numérico")
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        # Si es la primera cuenta, marcarla como default automáticamente
        if not BankAccount.objects.filter(user=validated_data['user']).exists():
            validated_data['is_default'] = True
        return super().create(validated_data)


class CommissionSerializer(serializers.ModelSerializer):
    """Serializa comisiones (solo lectura)."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    sale_id = serializers.UUIDField(source='sale.id', read_only=True)

    class Meta:
        model = Commission
        fields = [
            'id', 'user_email', 'sale_id', 'amount', 'currency',
            'status', 'description', 'payout', 'paid_at', 'created_at'
        ]
        read_only_fields = fields


class PayoutSerializer(serializers.ModelSerializer):
    """Serializa payout (principal)."""

    user_email = serializers.EmailField(source='commission.user.email', read_only=True)
    bank_account_details = serializers.SerializerMethodField()
    associated_commissions = serializers.SerializerMethodField()

    class Meta:
        model = Payout
        fields = [
            'id', 'user_email', 'amount', 'currency', 'status', 'provider',
            'reference_number', 'provider_transaction_id',
            'bank_account', 'bank_account_details',
            'commission', 'associated_commissions',
            'error_message', 'paid_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'reference_number', 'provider_transaction_id',
            'provider_response', 'error_message', 'paid_at', 'created_at', 'updated_at'
        ]

    def get_bank_account_details(self, obj):
        return {
            'bank_name': obj.bank_account.bank_name,
            'account_number_masked': '****' + obj.bank_account.account_number[-4:],
            'holder_name': obj.bank_account.holder_name,
        }

    def get_associated_commissions(self, obj):
        # Por ahora solo la comisión principal
        return [str(obj.commission.id)]


class PayoutBatchCreateSerializer(serializers.Serializer):
    """Serializer para crear payout en batch."""

    commission_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100,
        help_text=_("Lista de IDs de comisiones a pagar")
    )
    bank_account_id = serializers.UUIDField(
        help_text=_("ID de la cuenta bancaria destino")
    )

    def validate_commission_ids(self, value):
        from ..models import Commission
        user = self.context['request'].user
        commissions = Commission.objects.filter(
            id__in=value,
            user=user,
            status=Commission.Status.PENDING,
            payout__isnull=True
        )
        if len(commissions) != len(value):
            raise serializers.ValidationError(_("Todas las comisiones deben ser pendientes y pertenecer al usuario"))
        return value

    def validate_bank_account_id(self, value):
        from ..models import BankAccount
        user = self.context['request'].user
        try:
            account = BankAccount.objects.get(id=value, user=user, is_verified=True)
            return account
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError(_("Cuenta bancaria no encontrada o no verificada"))


class PayoutConfirmSerializer(serializers.Serializer):
    """Serializer para confirmar pago desde webhook/admin."""

    reference_number = serializers.CharField(max_length=100, required=False)
    provider_transaction_id = serializers.CharField(max_length=100, required=False)
    paid_at = serializers.DateTimeField(required=False)


class PayoutScheduleSerializer(serializers.ModelSerializer):
    """Serializa schedule de pagos automáticos."""

    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = PayoutSchedule
        fields = [
            'id', 'user_email', 'frequency', 'min_payout_amount',
            'is_active', 'next_run', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_email', 'next_run', 'created_at', 'updated_at']
