# apps/core_payments/api/schemas.py
"""
Pydantic schemas para Payout Automation API.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from ninja import Schema
from pydantic import Field, validator


class BankAccountIn(Schema):
    """Input para crear/actualizar cuenta bancaria."""
    bank_code: str = Field(..., min_length=2, max_length=10, description="Código banco SRI (ej: '01')")
    bank_name: str = Field(..., min_length=2, max_length=100)
    account_type: str = Field(..., pattern="^(SAVINGS|CHECKING)$")
    account_number: str = Field(..., min_length=5, max_length=50)
    holder_name: str = Field(..., min_length=2, max_length=200)
    holder_identification: str = Field(..., min_length=5, max_length=20)

    @validator('account_number')
    def validate_account_number(cls, v):
        if not v.isdigit():
            raise ValueError('Número de cuenta debe ser numérico')
        return v


class BankAccountOut(Schema):
    """Output de cuenta bancaria."""
    id: UUID
    user_email: str
    bank_code: str
    bank_name: str
    account_type: str
    account_number: str  # enmascarado en el serializer si es necesario
    holder_name: str
    holder_identification: str
    is_verified: bool
    is_default: bool
    created_at: datetime


class CommissionOut(Schema):
    """Output de comisión."""
    id: UUID
    user_email: str
    sale_id: UUID
    amount: float
    currency: str
    status: str
    description: Optional[str] = None
    payout: Optional[UUID] = None
    paid_at: Optional[datetime] = None
    created_at: datetime


class PayoutOut(Schema):
    """Output de payout."""
    id: UUID
    user_email: str
    amount: float
    currency: str
    status: str
    provider: str
    reference_number: str
    provider_transaction_id: str
    bank_account_details: dict
    associated_commissions: list[UUID]
    error_message: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PayoutBatchCreateIn(Schema):
    """Input para crear payout en batch."""
    commission_ids: list[UUID] = Field(..., min_items=1, max_items=100)
    bank_account_id: UUID


class PayoutConfirmIn(Schema):
    """Input para confirmar pago."""
    reference_number: Optional[str] = Field(None, max_length=100)
    provider_transaction_id: Optional[str] = Field(None, max_length=100)
    paid_at: Optional[datetime] = None


class PayoutScheduleIn(Schema):
    """Input para configurar schedule."""
    frequency: str = Field(..., pattern="^(DAILY|WEEKLY|MONTHLY|MANUAL)$")
    min_payout_amount: float = Field(..., ge=0)
    is_active: bool = True


class PayoutScheduleOut(Schema):
    """Output de schedule."""
    id: UUID
    user_email: str
    frequency: str
    min_payout_amount: float
    is_active: bool
    next_run: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PayoutSummaryOut(Schema):
    """Resumen de pagos."""
    pending: float
    paid: float
    failed: float
    count_pending: int
    count_paid: int
