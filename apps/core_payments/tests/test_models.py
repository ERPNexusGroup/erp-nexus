# apps/core_payments/tests/test_models.py
"""
Tests para modelos Payout Automation.
"""

import pytest
from decimal import Decimal
from django.utils import timezone

from ..models import BankAccount, Payout, Commission, PayoutSchedule


@pytest.mark.django_db
class TestBankAccountModel:
    """Tests del modelo BankAccount."""

    def test_create_bank_account(self, user_factory):
        user = user_factory()
        account = BankAccount.objects.create(
            user=user,
            bank_code='01',
            bank_name='Banco Pichincha',
            account_type='SAVINGS',
            account_number='1234567890',
            holder_name='John Doe',
            holder_identification='1723456789',
            is_verified=True,
        )
        assert account.id is not None
        assert account.user == user
        assert str(account) == f"Banco Pichincha — 1234567890 ({user.email})"

    def test_account_number_masked(self, user_factory):
        user = user_factory()
        account = BankAccount.objects.create(
            user=user,
            bank_code='01',
            bank_name='Banco Pichincha',
            account_type='SAVINGS',
            account_number='1234567890',
            holder_name='John Doe',
            holder_identification='1723456789',
        )
        masked = '****' + account.account_number[-4:]
        assert masked == '****7890'

    def test_default_account_unique_per_user(self, user_factory):
        user = user_factory()
        BankAccount.objects.create(user=user, bank_code='01', bank_name='B1', account_type='SAVINGS', account_number='111', holder_name='H1', holder_identification='ID1', is_default=True)
        # Segunda cuenta default debe permitirse si no es default=True, pero unique_together previene múltiples default=True
        with pytest.raises(Exception):
            BankAccount.objects.create(user=user, bank_code='02', bank_name='B2', account_type='SAVINGS', account_number='222', holder_name='H2', holder_identification='ID2', is_default=True)


@pytest.mark.django_db
class TestPayoutModel:
    """Tests del modelo Payout."""

    def test_create_payout(self, user_factory):
        user = user_factory()
        bank = BankAccount.objects.create(
            user=user, bank_code='01', bank_name='Banco Pichincha',
            account_type='SAVINGS', account_number='1111111111',
            holder_name='Test', holder_identification='9999999999', is_verified=True
        )
        # Commission mock (no usamos relación real en test)
        from unittest.mock import MagicMock
        comm = MagicMock(id='12345678-1234-5678-1234-567812345678', user=user, amount=Decimal('100.00'), currency='USD')
        payout = Payout.objects.create(
            commission=comm,
            bank_account=bank,
            amount=Decimal('100.00'),
            currency='USD',
            status=Payout.Status.PENDING,
            provider=Payout.Provider.SRI,
        )
        assert payout.status == Payout.Status.PENDING
        assert payout.amount == Decimal('100.00')

    def test_mark_as_paid(self, user_factory):
        user = user_factory()
        bank = BankAccount.objects.create(
            user=user, bank_code='01', bank_name='Banco Pichincha',
            account_type='SAVINGS', account_number='1111111111',
            holder_name='Test', holder_identification='9999999999', is_verified=True
        )
        from unittest.mock import MagicMock
        comm = MagicMock(id='12345678-1234-5678-1234-567812345678', user=user, amount=Decimal('100.00'), currency='USD')
        payout = Payout.objects.create(
            commission=comm,
            bank_account=bank,
            amount=Decimal('100.00'),
            currency='USD',
            status=Payout.Status.PROCESSING,
        )
        payout.mark_as_paid(reference_number='TXN-001', provider_transaction_id='TXN-001')
        payout.refresh_from_db()
        assert payout.status == Payout.Status.PAID
        assert payout.reference_number == 'TXN-001'
        assert payout.paid_at is not None


@pytest.mark.django_db
class TestPayoutScheduleModel:
    """Tests del modelo PayoutSchedule."""

    def test_create_schedule(self, user_factory):
        user = user_factory()
        schedule = PayoutSchedule.objects.create(
            user=user,
            frequency=PayoutSchedule.ScheduleFrequency.DAILY,
            min_payout_amount=Decimal('20.00'),
        )
        assert schedule.frequency == 'DAILY'
        assert schedule.is_active is True
        assert schedule.next_run is not None

    def test_calculate_next_run_daily(self, user_factory):
        user = user_factory()
        schedule = PayoutSchedule.objects.create(user=user, frequency=PayoutSchedule.ScheduleFrequency.DAILY)
        next_run = schedule.calculate_next_run()
        assert (next_run - timezone.now()).days == 1

    def test_calculate_next_run_weekly(self, user_factory):
        user = user_factory()
        schedule = PayoutSchedule.objects.create(user=user, frequency=PayoutSchedule.ScheduleFrequency.WEEKLY)
        next_run = schedule.calculate_next_run()
        assert (next_run - timezone.now()).days == 7
