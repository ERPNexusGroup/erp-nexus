# apps/core_payments/tests/test_api.py
"""
Tests para API de Payout Automation (Django Ninja).
"""

import pytest
from django.urls import reverse
from ninja.testing import TestClient

from ..models import BankAccount, Payout, PayoutSchedule
from .factories import BankAccountFactory, PayoutFactory  # TODO: crear factories


@pytest.mark.django_db
class TestBankAccountAPI:
    """Tests de endpoints /api/payments/bank-accounts/."""

    def test_list_bank_accounts(self, api_client, user_factory):
        user = user_factory()
        api_client.authenticate(user)
        BankAccount.objects.create(
            user=user, bank_code='01', bank_name='Banco Pichincha',
            account_type='SAVINGS', account_number='1234567890',
            holder_name='Test', holder_identification='9999999999'
        )
        response = api_client.get("/api/payments/bank-accounts/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_create_bank_account(self, api_client, user_factory):
        user = user_factory()
        api_client.authenticate(user)
        payload = {
            "bank_code": "01",
            "bank_name": "Banco Pichincha",
            "account_type": "SAVINGS",
            "account_number": "9876543210",
            "holder_name": "Jane Doe",
            "holder_identification": "1723456789",
        }
        response = api_client.post("/api/payments/bank-accounts/", payload)
        assert response.status_code == 201
        data = response.json()
        assert data['bank_code'] == '01'
        assert data['bank_name'] == 'Banco Pichincha'
        assert data['is_default'] is True  # primera cuenta = default

    def test_first_account_is_default(self, api_client, user_factory):
        user = user_factory()
        api_client.authenticate(user)
        payload = {
            "bank_code": "02",
            "bank_name": "Banco Guayaquil",
            "account_type": "CHECKING",
            "account_number": "1111111111",
            "holder_name": "Test",
            "holder_identification": "9999999999",
        }
        response = api_client.post("/api/payments/bank-accounts/", payload)
        assert response.status_code == 201
        assert response.json()['is_default'] is True

    def test_delete_bank_account_not_default(self, api_client, user_factory):
        user = user_factory()
        api_client.authenticate(user)
        account = BankAccount.objects.create(
            user=user, bank_code='01', bank_name='B1', account_type='SAVINGS',
            account_number='1111111111', holder_name='H', holder_identification='ID', is_default=False
        )
        # Crear cuenta default separada
        BankAccount.objects.create(
            user=user, bank_code='02', bank_name='B2', account_type='SAVINGS',
            account_number='2222222222', holder_name='H2', holder_identification='ID2', is_default=True
        )
        response = api_client.delete(f"/api/payments/bank-accounts/{account.id}/")
        assert response.status_code == 200
        assert BankAccount.objects.filter(id=account.id).count() == 0

    def test_delete_default_fails(self, api_client, user_factory):
        user = user_factory()
        api_client.authenticate(user)
        account = BankAccount.objects.create(
            user=user, bank_code='01', bank_name='B1', account_type='SAVINGS',
            account_number='1111111111', holder_name='H', holder_identification='ID', is_default=True
        )
        response = api_client.delete(f"/api/payments/bank-accounts/{account.id}/")
        assert response.status_code == 400
        assert 'predeterminada' in response.json().get('error', '').lower() or 'default' in response.json().get('error', '').lower()


@pytest.mark.django_db
class TestPayoutAPI:
    """Tests de endpoints /api/payouts/."""

    def test_list_payouts(self, api_client, user_factory):
        user = user_factory()
        api_client.authenticate(user)
        # Crear payout mock
        payout = PayoutFactory(user=user, amount=Decimal('50.00'), status=Payout.Status.PENDING)
        response = api_client.get("/api/payouts/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_payout_summary(self, api_client, user_factory):
        user = user_factory()
        api_client.authenticate(user)
        PayoutFactory(user=user, amount=Decimal('100.00'), status=Payout.Status.PAID)
        PayoutFactory(user=user, amount=Decimal('50.00'), status=Payout.Status.PENDING)
        response = api_client.get("/api/payouts/summary/")
        assert response.status_code == 200
        data = response.json()
        assert data['paid'] == 100.0
        assert data['pending'] == 50.0
        assert data['count_pending'] == 1
        assert data['count_paid'] == 1


@pytest.mark.django_db
class TestPayoutScheduleAPI:
    """Tests de schedule de pagos."""

    def test_get_or_create_schedule(self, api_client, user_factory):
        user = user_factory()
        api_client.authenticate(user)
        response = api_client.get("/api/payments/schedule/me/")
        assert response.status_code == 200
        data = response.json()
        assert data['frequency'] == 'DAILY'  # default
        assert data['min_payout_amount'] == 10.00

    def test_update_schedule(self, api_client, user_factory):
        user = user_factory()
        api_client.authenticate(user)
        # GET para crear
        api_client.get("/api/payments/schedule/me/")
        # PUT para actualizar
        payload = {"frequency": "WEEKLY", "min_payout_amount": 50.00, "is_active": True}
        response = api_client.put("/api/payments/schedule/me/", payload)
        assert response.status_code == 200
        assert response.json()['frequency'] == 'WEEKLY'
        assert response.json()['min_payout_amount'] == 50.00
