"""Payout API Endpoints — Django Ninja Router.

Endpoints:
  GET    /api/v1/payouts/                          — List payouts (filters)
  GET    /api/v1/payouts/{id}/                     — Payout detail + items
  POST   /api/v1/payouts/                          — Create payout from pending commissions
  POST   /api/v1/payouts/{id}/approve/             — Approve payout
  POST   /api/v1/payouts/{id}/cancel/              — Cancel payout (draft/approved only)
  POST   /api/v1/payouts/{id}/retry/               — Retry failed payout
  GET    /api/v1/payouts/bank-accounts/            — List bank accounts (by company)
  POST   /api/v1/payouts/bank-accounts/            — Create bank account
  PUT    /api/v1/payouts/bank-accounts/{id}/       — Update bank account
  DELETE /api/v1/payouts/bank-accounts/{id}/       — Soft delete (deactivate)
  GET    /api/v1/payouts/banks/                    — List available banks (static choices)
  GET    /api/v1/payouts/commissions/pending/      — List pending commission records
  POST   /api/v1/payouts/commissions/create-from-orders/ — Bulk create from orders
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from ninja import Router, Body
from ninja.params import Query
from ninja.errors import HttpError

from apps.core_api.auth import JWTAuth
from apps.core_api.permissions import require_staff, require_permission, require_company_access

from .schemas import (
    BankAccountOut,
    BankAccountCreate,
    BankAccountUpdate,
    BankOut,
    PayoutOut,
    PayoutItemOut,
    PayoutCreate,
    PayoutFilter,
    CommissionRecordOut,
    CommissionPendingFilter,
    CommissionCreateFromOrders,
    MessageResponse,
    PayoutActionResponse,
)
from ..models import (
    BankAccount,
    Payout,
    PayoutItem,
    CommissionRecord,
    PayoutConfig,
    CommissionRule,
)
from ..services import CommissionCalculator
from ..factory import BankProviderFactory
from ..exceptions import BankError, InsufficientFundsError
from apps.core_companies.models import Company


router = Router(auth=JWTAuth(), tags=['payouts'])


# ─── Bank Accounts ──────────────────────────────────────────────────

@router.get("/bank-accounts/", response=list[BankAccountOut])
def list_bank_accounts(request, company_id: Optional[int] = Query(None)):
    """
    Lista cuentas bancarias.
    - Staff: puede filtrar por company_id o ver todas.
    - No-staff: solo ve cuentas de su empresa activa.
    """
    qs = BankAccount.objects.all().select_related('company')

    user = request.auth
    if not user.is_staff and not user.is_superuser:
        # Restrict to user's active company
        try:
            active_company = user.erp_profile.active_company
        except Exception:
            raise HttpError(403, "Perfil no tiene empresa activa")
        qs = qs.filter(company=active_company)
    elif company_id:
        qs = qs.filter(company_id=company_id)

    return qs


@router.post("/bank-accounts/", response=BankAccountOut)
def create_bank_account(request, payload: BankAccountCreate = Body(...)):
    """Crea una nueva cuenta bancaria."""
    # Validate company access for non-staff
    if not request.auth.is_staff and not request.auth.is_superuser:
        try:
            active_company = request.auth.erp_profile.active_company
            if payload.company_id != active_company.id:
                raise HttpError(403, "No puede crear cuentas para otras empresas")
            company = active_company
        except Exception:
            raise HttpError(403, "Perfil no tiene empresa activa")
    else:
        # Staff: use provided company_id (validated via schema)
        company = get_object_or_404(Company, id=payload.company_id)

    # Create BankAccount
    bank_account = BankAccount.objects.create(
        company=company,
        bank_code=payload.bank_code,
        account_number=payload.account_number,
        account_type=payload.account_type,
        account_holder_name=payload.account_holder_name,
        rut=payload.rut or '',
        is_active=payload.is_active,
        is_default=payload.is_default,
    )
    # Build response dict including computed bank_display
    return {
        "id": bank_account.id,
        "bank_code": bank_account.bank_code,
        "bank_display": bank_account.get_bank_code_display(),
        "account_number": bank_account.account_number,
        "account_type": bank_account.account_type,
        "account_holder_name": bank_account.account_holder_name,
        "is_active": bank_account.is_active,
        "is_default": bank_account.is_default,
    }


@router.put("/bank-accounts/{id}/", response=BankAccountOut)
def update_bank_account(request, id: int, payload: BankAccountUpdate = Body(...)):
    """Actualiza una cuenta bancaria existente."""
    bank_account = get_object_or_404(BankAccount, id=id)

    # Check company access
    user = request.auth
    if not user.is_staff and not user.is_superuser:
        try:
            active_company = user.erp_profile.active_company
            if bank_account.company_id != active_company.id:
                raise HttpError(403, "No puede modificar cuentas de otras empresas")
        except Exception:
            raise HttpError(403, "Perfil no tiene empresa activa")

    # Apply updates
    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(bank_account, attr, value)

    bank_account.save()
    # Build response dict including computed bank_display
    return {
        "id": bank_account.id,
        "bank_code": bank_account.bank_code,
        "bank_display": bank_account.get_bank_code_display(),
        "account_number": bank_account.account_number,
        "account_type": bank_account.account_type,
        "account_holder_name": bank_account.account_holder_name,
        "is_active": bank_account.is_active,
        "is_default": bank_account.is_default,
    }


@router.delete("/bank-accounts/{id}/", response=MessageResponse)
def delete_bank_account(request, id: int):
    """Elimina (desactiva) una cuenta bancaria (soft delete)."""
    bank_account = get_object_or_404(BankAccount, id=id)

    # Check company access
    user = request.auth
    if not user.is_staff and not user.is_superuser:
        try:
            active_company = user.erp_profile.active_company
            if bank_account.company_id != active_company.id:
                raise HttpError(403, "No puede eliminar cuentas de otras empresas")
        except Exception:
            raise HttpError(403, "Perfil no tiene empresa activa")

    # Soft delete: set is_active=False
    bank_account.is_active = False
    bank_account.save()
    return MessageResponse(message="Cuenta bancaria desactivada")
    bank_account.save(update_fields=['is_active'])
    return {"message": "Cuenta bancaria desactivada"}


@router.get("/banks/")
def list_banks(request):
    """Lista los bancos disponibles (catálogo estático)."""
    banks = [
        {"code": code, "display": display}
        for code, display in BankAccount.BANK_CHOICES
    ]
    return banks


# ─── Payouts ────────────────────────────────────────────────────────

@router.get("/", response=list[PayoutOut])
def list_payouts(request, filters: PayoutFilter = Query(None)):
    """
    Lista pagos con filtros opcionales.
    - Staff: puede filtrar por cualquier empresa o ver todos.
    - No-staff: solo ve pagos de su empresa activa.
    """
    qs = Payout.objects.all().select_related('company', 'bank_account').prefetch_related('items')

    user = request.auth
    if not user.is_staff and not user.is_superuser:
        try:
            active_company = user.erp_profile.active_company
            qs = qs.filter(company=active_company)
        except Exception:
            raise HttpError(403, "Perfil no tiene empresa activa")

    if filters:
        if filters.status:
            qs = qs.filter(status=filters.status)
        if filters.company_id:
            if user.is_staff or user.is_superuser:
                qs = qs.filter(company_id=filters.company_id)
        if filters.start_date:
            qs = qs.filter(created_at__gte=filters.start_date)
        if filters.end_date:
            qs = qs.filter(created_at__lte=filters.end_date)

    qs = qs.order_by('-created_at')
    # Build response dicts manually to include computed fields (bank_display, item_count)
    results = []
    for p in qs:
        results.append({
            "id": p.id,
            "reference": p.reference,
            "company_id": p.company_id,
            "bank_account": {
                "id": p.bank_account.id,
                "bank_code": p.bank_account.bank_code,
                "bank_display": p.bank_account.get_bank_code_display(),
                "account_number": p.bank_account.account_number,
                "account_type": p.bank_account.account_type,
                "account_holder_name": p.bank_account.account_holder_name,
                "is_active": p.bank_account.is_active,
                "is_default": p.bank_account.is_default,
            } if p.bank_account else None,
            "total_amount": p.total_amount,
            "currency": p.currency,
            "status": p.status,
            "description": p.description or "",
            "approved_by": p.approved_by,
            "approved_at": p.approved_at,
            "paid_at": p.paid_at,
            "bank_reference": p.bank_reference or "",
            "item_count": p.items.count(),
            "created_at": p.created_at,
        })
    return results


@router.get("/{payout_id}/", response=PayoutOut)
def get_payout(request, payout_id: int):
    """Obtiene detalle de un pago incluyendo items."""
    payout = get_object_or_404(Payout.objects.select_related('company', 'bank_account').prefetch_related('items'), id=payout_id)

    # Check company access
    user = request.auth
    if not user.is_staff and not user.is_superuser:
        try:
            active_company = user.erp_profile.active_company
            if payout.company_id != active_company.id:
                raise HttpError(404, "Pago no encontrado")
        except Exception:
            raise HttpError(403, "Perfil no tiene empresa activa")

    # Build response dict manually to include computed fields
    return {
        "id": payout.id,
        "reference": payout.reference,
        "company_id": payout.company_id,
        "bank_account": {
            "id": payout.bank_account.id,
            "bank_code": payout.bank_account.bank_code,
            "bank_display": payout.bank_account.get_bank_code_display(),
            "account_number": payout.bank_account.account_number,
            "account_type": payout.bank_account.account_type,
            "account_holder_name": payout.bank_account.account_holder_name,
            "is_active": payout.bank_account.is_active,
            "is_default": payout.bank_account.is_default,
        },
        "total_amount": payout.total_amount,
        "currency": payout.currency,
        "status": payout.status,
        "description": payout.description or "",
        "approved_by": payout.approved_by,
        "approved_at": payout.approved_at,
        "paid_at": payout.paid_at,
        "bank_reference": payout.bank_reference or "",
        "item_count": payout.items.count(),
        "created_at": payout.created_at,
    }


@router.post("/", response=PayoutOut)
@transaction.atomic
def create_payout(request, payload: PayoutCreate = Body(...)):
    """
    Crea un pago desde registros de comisiones pendientes (bulk).
    Valida fondos, calcula total y crea Payout + PayoutItems.
    """
    # 1. Validate company access and bank account
    user = request.auth
    company = get_object_or_404(Company, id=payload.company_id)
    bank_account = get_object_or_404(BankAccount, id=payload.bank_account_id, is_active=True)

    # Non-staff can only create for their active company
    if not user.is_staff and not user.is_superuser:
        try:
            active_company = user.erp_profile.active_company
            if payload.company_id != active_company.id:
                raise HttpError(403, "No puede crear pagos para otras empresas")
        except Exception:
            raise HttpError(403, "Perfil no tiene empresa activa")

    # 2. Get pending commission records
    records = CommissionRecord.objects.filter(
        id__in=payload.item_ids,
        status='pending',
        company_id=payload.company_id
    ).select_related('order', 'purchase_order', 'commission_rule')

    if not records:
        raise HttpError(404, "No se encontraron registros de comisión válidos")

    # 3. Calculate total net amount
    total = sum(r.net_amount for r in records)

    # 4. Create Payout (draft)
    reference = f"PAY-{timezone.now().strftime('%Y%m%d-%H%M%S')}"
    payout = Payout.objects.create(
        reference=reference,
        company=company,
        bank_account=bank_account,
        total_amount=total,
        currency='USD',
        status='draft',
        description=payload.description or 'Pago automático de comisiones',
    )

    # 5. Create PayoutItems and link CommissionRecords
    payout_items = []
    for record in records:
        item = PayoutItem(
            payout=payout,
            order=record.order,
            purchase_order=record.purchase_order,
            gross_amount=record.gross_amount,
            retention_amount=record.retention_amount,
            net_amount=record.net_amount,
            commission_type=record.commission_rule.module,
            description=f"Comisión {record.commission_rule.get_module_display()}",
        )
        payout_items.append(item)
    
    PayoutItem.objects.bulk_create(payout_items)

    # Update CommissionRecords to point to payout items
    for item, record in zip(payout_items, records):
        record.payout_item = item
        record.status = 'paid'
        record.save(update_fields=['payout_item', 'status'])

    # Build response dict manually with computed fields
    return {
        "id": payout.id,
        "reference": payout.reference,
        "company_id": payout.company_id,
        "bank_account": {
            "id": payout.bank_account.id,
            "bank_code": payout.bank_account.bank_code,
            "bank_display": payout.bank_account.get_bank_code_display(),
            "account_number": payout.bank_account.account_number,
            "account_type": payout.bank_account.account_type,
            "account_holder_name": payout.bank_account.account_holder_name,
            "is_active": payout.bank_account.is_active,
            "is_default": payout.bank_account.is_default,
        },
        "total_amount": payout.total_amount,
        "currency": payout.currency,
        "status": payout.status,
        "description": payout.description or "",
        "approved_by": payout.approved_by,
        "approved_at": payout.approved_at,
        "paid_at": payout.paid_at,
        "bank_reference": payout.bank_reference or "",
        "item_count": len(payout_items),
        "created_at": payout.created_at,
    }


@router.post("/{payout_id}/approve/", response=PayoutActionResponse)
def approve_payout(request, payout_id: int):
    """
    Aprueba un pago (requiere staff/admin).
    Cambia estado de 'draft' a 'approved' y registra usuario/fecha.
    """
    # Only staff can approve
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Solo personal administrativo puede aprobar pagos")

    payout = get_object_or_404(Payout, id=payout_id)

    if payout.status != 'draft':
        raise HttpError(400, f"No se puede aprobar pago en estado '{payout.status}'")

    payout.status = 'approved'
    payout.approved_by = request.auth
    payout.approved_at = timezone.now()
    payout.save(update_fields=['status', 'approved_by', 'approved_at'])

    return PayoutActionResponse(
        message="Pago aprobado exitosamente",
        status=payout.status,
        reference=payout.reference
    )


@router.post("/{payout_id}/cancel/", response=PayoutActionResponse)
def cancel_payout(request, payout_id: int):
    """
    Cancela un pago (solo draft o approved).
    Revierte CommissionRecords a estado 'pending'.
    """
    payout = get_object_or_404(Payout, id=payout_id)

    # Check company access for non-staff
    user = request.auth
    if not user.is_staff and not user.is_superuser:
        try:
            active_company = user.erp_profile.active_company
            if payout.company_id != active_company.id:
                raise HttpError(404, "Pago no encontrado")
        except Exception:
            raise HttpError(403, "Perfil no tiene empresa activa")

    if payout.status not in ['draft', 'approved']:
        raise HttpError(400, f"No se puede cancelar pago en estado '{payout.status}'")

    payout.status = 'cancelled'
    payout.save(update_fields=['status'])

    # Revert CommissionRecords linked to this payout back to pending
    # And unlink payout_item
    CommissionRecord.objects.filter(payout_item__payout=payout).update(
        status='pending',
        payout_item=None
    )

    return PayoutActionResponse(
        message="Pago cancelado exitosamente",
        status=payout.status,
        reference=payout.reference
    )


@router.post("/{payout_id}/retry/", response=PayoutActionResponse)
def retry_payout(request, payout_id: int):
    """
    Reintenta un pago fallido (solo status='failed').
    Cambia estado a 'processing' para que el sistema bancario lo reintente.
    """
    payout = get_object_or_404(Payout, id=payout_id)

    # Check company access for non-staff
    user = request.auth
    if not user.is_staff and not user.is_superuser:
        try:
            active_company = user.erp_profile.active_company
            if payout.company_id != active_company.id:
                raise HttpError(404, "Pago no encontrado")
        except Exception:
            raise HttpError(403, "Perfil no tiene empresa activa")

    if payout.status != 'failed':
        raise HttpError(400, f" Solo pagos fallidos pueden ser reintentados (actual: {payout.status})")

    payout.status = 'processing'
    payout.error_message = ''  # Clear previous error
    payout.save(update_fields=['status', 'error_message'])

    # TODO: Enqueue bank transfer job (async via Celery)

    return PayoutActionResponse(
        message="Pago en cola para reintento",
        status=payout.status,
        reference=payout.reference
    )


# ─── Commission Records ──────────────────────────────────────────────

@router.get("/commissions/pending/")
def list_pending_commissions(request, filters: CommissionPendingFilter = Query(None)):
    """
    Lista registros de comisiones pendientes.
    Acepta filtros por company, rango de fechas.
    """
    user = request.auth
    company_id = filters.company_id if filters else None

    # Non-staff can only query their own company
    if not user.is_staff and not user.is_superuser:
        try:
            active_company = user.erp_profile.active_company
            if company_id and company_id != active_company.id:
                raise HttpError(403, "No puede ver comisiones de otras empresas")
            company_id = active_company.id
        except Exception:
            raise HttpError(403, "Perfil no tiene empresa activa")

    if not company_id:
        raise HttpError(400, "Se requiere company_id")

    qs = CommissionCalculator.get_pending_commissions(
        company_id,
        start_date=filters.start_date if filters else None,
        end_date=filters.end_date if filters else None
    )
    # Convertir a lista de dicts compatibles con CommissionRecordOut
    results = [
        {
            "id": r.id,
            "order_id": r.order_id,
            "purchase_order_id": r.purchase_order_id,
            "company_id": r.company_id,
            "gross_amount": r.gross_amount,
            "retention_amount": r.retention_amount,
            "net_amount": r.net_amount,
            "status": r.status,
            "commission_module": r.commission_rule.module if r.commission_rule_id else '',
            "created_at": r.created_at,
        }
        for r in qs
    ]
    return results


@router.post("/commissions/create-from-orders/", response=list[CommissionRecordOut])
def create_commissions_from_orders(request, payload: CommissionCreateFromOrders = Body(...)):
    """
    Crea registros de comisión en bulk a partir de órdenes de venta.
    Solo staff.
    """
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Solo personal administrativo puede generar comisiones")

    from apps.sales.models import Order

    orders = list(Order.objects.filter(id__in=payload.order_ids))
    records = CommissionCalculator.bulk_create_from_orders(orders)

    return records
