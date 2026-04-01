"""
API endpoints para accounting_basic.

Estos endpoints se registran automáticamente en /api/v1/accounting/
cuando el módulo está activo.
"""
from ninja import Router, Schema
from typing import Optional
from datetime import date

router = Router()


class AccountOut(Schema):
    id: int
    code: str
    name: str
    account_type: str
    is_active: bool
    balance: float


class JournalEntryOut(Schema):
    id: int
    reference: str
    date: date
    description: str
    is_posted: bool
    total_debit: float
    total_credit: float


class BalanceOut(Schema):
    account_code: str
    account_name: str
    account_type: str
    balance: float


@router.get("/accounts", response=list[AccountOut])
def list_accounts(request, account_type: str = None):
    """Lista plan de cuentas."""
    from accounting_basic.core.models import Account

    qs = Account.objects.filter(is_active=True)
    if account_type:
        qs = qs.filter(account_type=account_type)

    return [
        AccountOut(
            id=a.id,
            code=a.code,
            name=a.name,
            account_type=a.account_type,
            is_active=a.is_active,
            balance=a.balance,
        )
        for a in qs
    ]


@router.get("/journal", response=list[JournalEntryOut])
def list_entries(request, limit: int = 50):
    """Lista asientos contables."""
    from accounting_basic.core.models import JournalEntry

    qs = JournalEntry.objects.all()[:limit]
    return [
        JournalEntryOut(
            id=e.id,
            reference=e.reference,
            date=e.date,
            description=e.description,
            is_posted=e.is_posted,
            total_debit=e.total_debit,
            total_credit=e.total_credit,
        )
        for e in qs
    ]


@router.get("/balance", response=list[BalanceOut])
def balance_sheet(request):
    """Genera balance de cuentas."""
    from accounting_basic.core.models import Account

    accounts = Account.objects.filter(is_active=True).order_by("code")
    return [
        BalanceOut(
            account_code=a.code,
            account_name=a.name,
            account_type=a.account_type,
            balance=a.balance,
        )
        for a in accounts
    ]
