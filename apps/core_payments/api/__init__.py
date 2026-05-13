# apps/core_payments/api/__init__.py
"""
Payout Automation API — Django Ninja Router.
Endpoints para gestión de cuentas bancarias, comisiones y pagos.
"""

from ninja import Router
from django.db import transaction
from django.utils import timezone

from ..models import BankAccount, Payout, Commission, PayoutSchedule
from .schemas import (
    BankAccountIn,
    BankAccountOut,
    PayoutOut,
    CommissionOut,
    PayoutBatchCreateIn,
    PayoutConfirmIn,
    PayoutScheduleIn,
    PayoutScheduleOut,
)

router = Router(tags=["Payments & Payouts"])


# ─── Bank Accounts ────────────────────────────────────────────────────────────
@router.get("/bank-accounts/", response=list[BankAccountOut], url_name="bankaccount-list")
def list_bank_accounts(request):
    """Lista cuentas bancarias del usuario."""
    qs = BankAccount.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    return qs


@router.post("/bank-accounts/", response=BankAccountOut, url_name="bankaccount-create")
def create_bank_account(request, payload: BankAccountIn):
    """Crea nueva cuenta bancaria."""
    data = payload.dict()
    # Si es primera cuenta, marcar como default
    if not BankAccount.objects.filter(user=request.user).exists():
        data['is_default'] = True
    account = BankAccount.objects.create(user=request.user, **data)
    return account


@router.get("/bank-accounts/{account_id}/", response=BankAccountOut, url_name="bankaccount-detail")
def get_bank_account(request, account_id: str):
    """Detalle de cuenta bancaria."""
    obj = BankAccount.objects.get(id=account_id, user=request.user)
    return obj


@router.delete("/bank-accounts/{account_id}/", url_name="bankaccount-delete")
def delete_bank_account(request, account_id: str):
    """Elimina cuenta bancaria (si no es default ni tiene payouts)."""
    account = BankAccount.objects.get(id=account_id, user=request.user)
    if account.is_default:
        return {"error": "No se puede eliminar la cuenta predeterminada"}, 400
    if Payout.objects.filter(bank_account=account, status__in=[Payout.Status.PENDING, Payout.Status.PROCESSING]).exists():
        return {"error": "No se puede eliminar cuenta con payouts pendientes o en proceso"}, 400
    account.delete()
    return {"success": True}


# ─── Commissions (solo lectura) ──────────────────────────────────────────────
@router.get("/commissions/", response=list[CommissionOut], url_name="commission-list")
def list_commissions(request, status: str = None):
    """Lista comisiones del usuario."""
    qs = Commission.objects.filter(user=request.user).select_related('sale')
    if status:
        qs = qs.filter(status=status)
    return qs.order_by('-created_at')


@router.get("/commissions/{commission_id}/", response=CommissionOut, url_name="commission-detail")
def get_commission(request, commission_id: str):
    """Detalle de comisión."""
    obj = Commission.objects.get(id=commission_id, user=request.user)
    return obj


# ─── Payouts ─────────────────────────────────────────────────────────────────
@router.get("/payouts/", response=list[PayoutOut], url_name="payout-list")
def list_payouts(request, status: str = None):
    """Lista pagos del usuario."""
    qs = Payout.objects.filter(commission__user=request.user).select_related('bank_account', 'commission')
    if status:
        qs = qs.filter(status=status)
    return qs.order_by('-created_at')


@router.get("/payouts/{payout_id}/", response=PayoutOut, url_name="payout-detail")
def get_payout(request, payout_id: str):
    """Detalle de pago."""
    obj = Payout.objects.get(id=payout_id, commission__user=request.user)
    return obj


@router.post("/payouts/batch-create/", url_name="payout-batch-create")
def batch_create_payouts(request, payload: PayoutBatchCreateIn):
    """
    Crea payouts en batch desde lista de commission_ids.
    Encola tarea Celery para procesar.
    """
    user = request.user
    commission_ids = payload.commission_ids
    bank_account_id = payload.bank_account_id

    # Validar comisiones
    commissions = Commission.objects.filter(
        id__in=commission_ids,
        user=user,
        status=Commission.Status.PENDING,
        payout__isnull=True
    )
    if len(commissions) != len(commission_ids):
        return {"error": "Algunas comisiones no son válidas o ya tienen payout"}, 400

    # Validar bank account
    try:
        bank_account = BankAccount.objects.get(id=bank_account_id, user=user, is_verified=True)
    except BankAccount.DoesNotExist:
        return {"error": "Cuenta bancaria no encontrada o no verificada"}, 404

    # Crear payouts
    created = []
    with transaction.atomic():
        for comm in commissions:
            payout = Payout.objects.create(
                commission=comm,
                bank_account=bank_account,
                amount=comm.amount,
                currency=comm.currency,
                status=Payout.Status.PENDING,
                provider=Payout.Provider.SRI,
            )
            comm.status = Commission.Status.PROCESSING
            comm.save(update_fields=['status'])
            created.append(str(payout.id))

    # Encolar tarea
    from ..tasks import process_payout_batch
    process_payout_batch.delay(created)

    return {"created": len(created), "payout_ids": created}


@router.post("/payouts/{payout_id}/confirm/", url_name="payout-confirm")
def confirm_payout(request, payout_id: str, payload: PayoutConfirmIn):
    """Confirma pago (webhook interno o admin)."""
    try:
        payout = Payout.objects.get(id=payout_id, commission__user=request.user)
    except Payout.DoesNotExist:
        return {"error": "Payout no encontrado"}, 404

    if payout.status != Payout.Status.PROCESSING:
        return {"error": f"Payout no está en PROCESSING (está {payout.status})"}, 400

    paid_at = payload.paid_at or timezone.now()
    payout.mark_as_paid(
        reference_number=payload.reference_number or '',
        provider_transaction_id=payload.provider_transaction_id or ''
    )
    payout.paid_at = paid_at
    payout.save(update_fields=['paid_at'])

    # Notificar usuario (async)
    from ..tasks import send_payout_confirmed_email
    send_payout_confirmed_email.delay(str(payout.id))

    return {"status": "paid", "paid_at": paid_at}


@router.post("/payouts/{payout_id}/cancel/", url_name="payout-cancel")
def cancel_payout(request, payout_id: str):
    """Cancela payout (rollback a PENDING)."""
    try:
        payout = Payout.objects.get(id=payout_id, commission__user=request.user)
    except Payout.DoesNotExist:
        return {"error": "Payout no encontrado"}, 404

    if payout.status in [Payout.Status.PAID, Payout.Status.CANCELLED]:
        return {"error": f"No se puede cancelar payout en estado {payout.status}"}, 400

    payout.status = Payout.Status.CANCELLED
    payout.save(update_fields=['status'])

    # Revertir comisión
    payout.commission.status = Commission.Status.PENDING
    payout.commission.save(update_fields=['status'])

    return {"status": "cancelled"}


# ─── Payout Schedule ──────────────────────────────────────────────────────────
@router.get("/schedule/me", response=PayoutScheduleOut, url_name="schedule-me")
def get_my_schedule(request):
    """Obtiene schedule de pagos del usuario actual."""
    schedule, _ = PayoutSchedule.objects.get_or_create(
        user=request.user,
        defaults={'frequency': PayoutSchedule.ScheduleFrequency.DAILY}
    )
    return schedule


@router.put("/schedule/me", response=PayoutScheduleOut, url_name="schedule-update")
def update_my_schedule(request, payload: PayoutScheduleIn):
    """Actualiza schedule de pagos."""
    schedule, _ = PayoutSchedule.objects.get_or_create(user=request.user)
    schedule.frequency = payload.frequency
    schedule.min_payout_amount = payload.min_payout_amount
    schedule.is_active = payload.is_active
    schedule.save(update_fields=['frequency', 'min_payout_amount', 'is_active', 'updated_at'])
    return schedule


# ─── Analytics (summary) ──────────────────────────────────────────────────────
@router.get("/summary/", url_name="payout-summary")
def get_summary(request):
    """Resumen de payouts del usuario."""
    user = request.user
    stats = Payout.objects.filter(commission__user=user).aggregate(
        total_pending=models.Sum('amount', filter=models.Q(status=Payout.Status.PENDING)),
        total_paid=models.Sum('amount', filter=models.Q(status=Payout.Status.PAID)),
        total_failed=models.Sum('amount', filter=models.Q(status=Payout.Status.FAILED)),
        count_pending=models.Count('id', filter=models.Q(status=Payout.Status.PENDING)),
        count_paid=models.Count('id', filter=models.Q(status=Payout.Status.PAID)),
    )
    return {
        "pending": stats['total_pending'] or 0,
        "paid": stats['total_paid'] or 0,
        "failed": stats['total_failed'] or 0,
        "count_pending": stats['count_pending'] or 0,
        "count_paid": stats['count_paid'] or 0,
    }
