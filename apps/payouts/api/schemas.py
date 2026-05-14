"""Payout API Schemas — Django Ninja request/response validators."""
from decimal import Decimal
from datetime import datetime
from typing import Optional, List

from ninja import Schema


class BankAccountOut(Schema):
    """Serializer for BankAccount list/detail responses."""
    id: int
    bank_code: str
    bank_display: str
    account_number: str
    account_type: str
    account_holder_name: str
    is_active: bool
    is_default: bool


class BankAccountCreate(Schema):
    """Schema for creating a new bank account."""
    company_id: int
    bank_code: str
    account_number: str
    account_type: str = 'checking'
    account_holder_name: str
    rut: Optional[str] = ''
    is_active: bool = True
    is_default: bool = False


class BankAccountUpdate(Schema):
    """Schema for updating an existing bank account."""
    bank_code: Optional[str] = None
    account_number: Optional[str] = None
    account_type: Optional[str] = None
    account_holder_name: Optional[str] = None
    rut: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class BankOut(Schema):
    """Static bank choice entry."""
    code: str
    display: str


class PayoutItemOut(Schema):
    """Serializer for PayoutItem (line item) responses."""
    id: int
    order_id: Optional[int]
    purchase_order_id: Optional[int]
    gross_amount: Decimal
    retention_amount: Decimal
    net_amount: Decimal
    commission_type: str
    description: str


class PayoutOut(Schema):
    """Serializer for Payout list/detail responses."""
    id: int
    reference: str
    company_id: int
    bank_account: BankAccountOut
    total_amount: Decimal
    currency: str
    status: str
    description: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    paid_at: Optional[datetime]
    bank_reference: str
    item_count: int
    created_at: datetime


class PayoutCreate(Schema):
    """Schema for creating a payout from pending commission records."""
    company_id: int
    bank_account_id: int
    description: str = ''
    item_ids: List[int]  # CommissionRecord IDs to include


class PayoutFilter(Schema):
    """Query parameters for filtering payouts list."""
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    company_id: Optional[int] = None


class CommissionRecordOut(Schema):
    """Serializer for CommissionRecord responses."""
    id: int
    order_id: Optional[int]
    purchase_order_id: Optional[int]
    company_id: int
    gross_amount: Decimal
    retention_amount: Decimal
    net_amount: Decimal
    status: str
    commission_module: str  # from commission_rule.module
    created_at: datetime


class CommissionPendingFilter(Schema):
    """Query parameters for pending commissions."""
    company_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CommissionCreateFromOrders(Schema):
    """Schema for bulk creating commission records from orders."""
    order_ids: List[int]


class MessageResponse(Schema):
    """Generic message response."""
    message: str


class PayoutActionResponse(Schema):
    """Response for payout actions (approve, cancel, retry)."""
    message: str
    status: str
    reference: Optional[str] = None
    error: Optional[str] = None
