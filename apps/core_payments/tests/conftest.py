# apps/core_payments/tests/conftest.py
"""
Fixtures para tests de core_payments.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from ...models import BankAccount, Payout, Commission, PayoutSchedule


@pytest.fixture
def bank_account_factory(user_factory):
    """Factory para crear cuentas bancarias."""
    def make(**kwargs):
        user = kwargs.pop('user', user_factory())
        defaults = {
            'user': user,
            'bank_code': '01',
            'bank_name': 'Banco Pichincha',
            'account_type': 'SAVINGS',
            'account_number': '1234567890',
            'holder_name': 'Test User',
            'holder_identification': '1723456789',
            'is_verified': True,
            'is_default': False,
        }
        defaults.update(kwargs)
        return BankAccount.objects.create(**defaults)
    return make


@pytest.fixture
def commission_factory(user_factory):
    """Factory para crear comisiones."""
    def make(**kwargs):
        from unittest.mock import MagicMock
        user = kwargs.pop('user', user_factory())
        # Mock de Sale si no se provee
        sale = kwargs.pop('sale', MagicMock(id='00000000-0000-0000-0000-000000000000', total=Decimal('100.00')))
        defaults = {
            'user': user,
            'sale': sale,
            'amount': Decimal('100.00'),
            'currency': 'USD',
            'status': Commission.Status.PENDING,
        }
        defaults.update(kwargs)
        return Commission.objects.create(**defaults)
    return make


@pytest.fixture
def payout_factory(user_factory, bank_account_factory, commission_factory):
    """Factory para crear payouts."""
    def make(**kwargs):
        user = kwargs.pop('user', user_factory())
        bank = kwargs.pop('bank_account', bank_account_factory(user=user, is_verified=True))
        comm = kwargs.pop('commission', commission_factory(user=user))
        defaults = {
            'commission': comm,
            'bank_account': bank,
            'amount': Decimal('100.00'),
            'currency': 'USD',
            'status': Payout.Status.PENDING,
            'provider': Payout.Provider.SRI,
        }
        defaults.update(kwargs)
        return Payout.objects.create(**defaults)
    return make


@pytest.fixture
def payout_schedule_factory(user_factory):
    """Factory para crear payout schedule."""
    def make(**kwargs):
        user = kwargs.pop('user', user_factory())
        defaults = {
            'user': user,
            'frequency': PayoutSchedule.ScheduleFrequency.DAILY,
            'min_payout_amount': Decimal('10.00'),
            'is_active': True,
        }
        defaults.update(kwargs)
        return PayoutSchedule.objects.create(**defaults)
    return make
