# apps/core_payments/api/views.py
"""
API Views para Payout Automation.
"""

from django.utils import timezone
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from ..models import BankAccount, Payout, Commission, PayoutSchedule
from .serializers import (
    BankAccountSerializer,
    PayoutSerializer,
    CommissionSerializer,
    PayoutBatchCreateSerializer,
    PayoutConfirmSerializer,
    PayoutScheduleSerializer,
)


class BankAccountViewSet(viewsets.ModelViewSet):
    """CRUD de cuentas bancarias del usuario."""
    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BankAccount.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommissionViewSet(viewsets.ReadOnlyModelViewSet):
    """Lista de comisiones del usuario (solo lectura)."""
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Commission.objects.all().select_related('user', 'sale')
        return Commission.objects.filter(user=user).select_related('user', 'sale')


class PayoutViewSet(viewsets.ModelViewSet):
    """Payouts — creación, listado, confirmación manual."""
    serializer_class = PayoutSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'provider', 'created_at']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payout.objects.all().select_related('commission__user', 'bank_account')
        return Payout.objects.filter(commission__user=user).select_related('commission__user', 'bank_account')

    def perform_create(self, serializer):
        # Solo admin puede crear directamente (normalmente se via batch)
        if not self.request.user.is_staff:
            raise PermissionDenied("Solo admin puede crear payouts manualmente")
        serializer.save()

    @action(detail=False, methods=['post'], url_path='batch-create')
    def batch_create(self, request):
        """
        Crea Payouts en batch desde lista de commission_ids.
        POST /api/payouts/batch-create/
        Body: { "commission_ids": [...], "bank_account_id": "uuid" }
        """
        serializer = PayoutBatchCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        commission_ids = serializer.validated_data['commission_ids']
        bank_account = serializer.validated_data['bank_account_id']

        from ..models import Commission
        commissions = Commission.objects.filter(
            id__in=commission_ids,
            user=request.user,
            status=Commission.Status.PENDING
        ).select_related('user')

        # TODO: agrupar por usuario (por ahora pago individual por comisión)
        created_payouts = []
        with transaction.atomic():
            for commission in commissions:
                payout = Payout.objects.create(
                    commission=commission,
                    bank_account=bank_account,
                    amount=commission.amount,
                    currency=commission.currency,
                    status=Payout.Status.PENDING,
                    provider=Payout.Provider.SRI,
                )
                # Marcar comisión como PROCESSING
                commission.status = Commission.Status.PROCESSING
                commission.save(update_fields=['status', 'updated_at'])
                created_payouts.append(payout)

        # Encolar tarea Celery para procesar batch
        from ..tasks import process_payout_batch
        process_payout_batch.delay([str(p.id) for p in created_payouts])

        return Response({
            'created': len(created_payouts),
            'payout_ids': [str(p.id) for p in created_payouts]
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """
        Confirma pago manualmente (admin) o vía webhook.
        POST /api/payouts/{id}/confirm/
        Body: { "reference_number": "...", "provider_transaction_id": "...", "paid_at": "..." }
        """
        payout = self.get_object()
        serializer = PayoutConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if payout.status != Payout.Status.PROCESSING:
            return Response(
                {'error': f'Payout no está en estado PROCESSING (está {payout.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        paid_at = serializer.validated_data.get('paid_at') or timezone.now()
        payout.mark_as_paid(
            reference_number=serializer.validated_data.get('reference_number', ''),
            provider_transaction_id=serializer.validated_data.get('provider_transaction_id', '')
        )
        payout.paid_at = paid_at
        payout.save(update_fields=['paid_at'])

        # Notificar al usuario
        from ..tasks import send_payout_confirmed_email
        send_payout_confirmed_email.delay(str(payout.id))

        return Response({'status': 'paid', 'paid_at': paid_at})

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Cancela payout (si no está pagado aún)."""
        payout = self.get_object()
        if payout.status in [Payout.Status.PAID, Payout.Status.CANCELLED]:
            return Response(
                {'error': f'No se puede cancelar payout en estado {payout.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payout.status = Payout.Status.CANCELLED
        payout.save(update_fields=['status', 'updated_at'])

        # Revertir comisión a PENDING
        payout.commission.status = Commission.Status.PENDING
        payout.commission.save(update_fields=['status', 'updated_at'])

        return Response({'status': 'cancelled'})


class PayoutScheduleViewSet(viewsets.ModelViewSet):
    """Configuración de schedule de pagos automáticos."""
    serializer_class = PayoutScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PayoutSchedule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='my-schedule')
    def my_schedule(self, request):
        """Obtiene o crea schedule del usuario actual."""
        schedule, created = PayoutSchedule.objects.get_or_create(
            user=request.user,
            defaults={'frequency': PayoutSchedule.ScheduleFrequency.DAILY}
        )
        serializer = self.get_serializer(schedule)
        return Response(serializer.data)
