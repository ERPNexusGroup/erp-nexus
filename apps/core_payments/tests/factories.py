# apps/core_payments/tests/factories.py
"""
Fixtures/Factory helpers para tests de core_payments.
"""

import factory
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import BankAccount, Payout, Commission, PayoutSchedule

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    is_active = True
    is_staff = False


class BankAccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BankAccount

    user = factory.SubFactory(UserFactory)
    bank_code = '01'
    bank_name = 'Banco Pichincha'
    account_type = 'SAVINGS'
    account_number = factory.Sequence(lambda n: str(1000000000 + n))
    holder_name = factory.Sequence(lambda n: f"Holder {n}")
    holder_identification = factory.Sequence(lambda n: f"172345678{n % 10}")
    is_verified = True
    is_default = False


class CommissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Commission

    user = factory.SubFactory(UserFactory)
    sale = None  # debe proveerse o mockearse
    amount = Decimal('100.00')
    currency = 'USD'
    status = Commission.Status.PENDING
    description = factory.Sequence(lambda n: f"Commission {n}")

    @factory.post_generation
    def payout(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.payout = extracted


class PayoutFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payout

    commission = factory.SubFactory(CommissionFactory)
    bank_account = factory.SubFactory(BankAccountFactory, user=factory.SelfAttribute('..commission.user'))
    amount = Decimal('100.00')
    currency = 'USD'
    status = Payout.Status.PENDING
    provider = Payout.Provider.SRI
    reference_number = ''
    provider_transaction_id = ''
    provider_response = None
    error_message = ''

    @factory.post_generation
    def set_paid(self, create, extracted, **kwargs):
        if extracted:
            self.status = Payout.Status.PAID
            self.paid_at = timezone.now()
            self.reference_number = kwargs.get('reference', 'TXN-001')
            self.save(update_fields=['status', 'paid_at', 'reference_number'])


class PayoutScheduleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PayoutSchedule

    user = factory.SubFactory(UserFactory)
    frequency = PayoutSchedule.ScheduleFrequency.DAILY
    min_payout_amount = Decimal('10.00')
    is_active = True
    next_run = None

    @factory.post_generation
    def calculate_next(self, create, extracted, **kwargs):
        if create and not self.next_run:
            self.next_run = self.calculate_next_run()
            self.save(update_fields=['next_run'])
