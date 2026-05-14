"""API Endpoint Tests — Payouts v1."""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from ninja.testing import TestClient
from apps.core_api.api import api

from apps.payouts.models import (
    BankAccount, CommissionRecord, CommissionRule,
    Payout, PayoutItem, PayoutConfig
)
from apps.core_companies.models import Company

User = get_user_model()


def _auth_header(user):
    """Genera header Authorization JWT para Ninja TestClient."""
    import jwt
    from datetime import datetime, timezone, timedelta
    from django.conf import settings
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(hours=1),
        "jti": "test-jti",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


class PayoutAPITests(TestCase):
    """Tests para endpoints de Payouts API."""

    BASE_URL = "/payouts"

    def setUp(self):
        self.client = TestClient(api)
        self.admin = User.objects.create_superuser(
            username='admin', email='admin@test.com', password='admin123'
        )
        self.staff = User.objects.create_user(
            username='staff', email='staff@test.com',
            password='staff123', is_staff=True
        )
        self.user = User.objects.create_user(
            username='testuser', email='user@test.com', password='user123'
        )
        self.company = Company.objects.create(
            name="TestCo", tax_id="1234567890"
        )
        # Banco por defecto para tests que requieren Payout con bank_account
        self.bank = BankAccount.objects.create(
            company=self.company,
            bank_code="produbanco",
            account_number="9999999999",
            account_type="checking",
            account_holder_name="Test Bank",
            is_active=True,
            is_default=True
        )

    def _auth_admin(self):
        return _auth_header(self.admin)

    def _auth_staff(self):
        return _auth_header(self.staff)

    def _auth_user(self):
        return _auth_header(self.user)

    def test_list_payouts_requires_auth(self):
        response = self.client.get(f"{self.BASE_URL}/")
        self.assertEqual(response.status_code, 401)

    def test_list_payouts_admin_sees_all(self):
        Payout.objects.create(
            reference="PAY-TEST1", company=self.company,
            total_amount=Decimal("100.00"), status="draft",
            bank_account=self.bank
        )
        response = self.client.get(f"{self.BASE_URL}/", headers=self._auth_admin())
        self.assertEqual(response.status_code, 200)
        data = response.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)

    def test_list_payouts_filter_by_status(self):
        Payout.objects.create(
            reference="PAY-TEST1", company=self.company,
            total_amount=Decimal("100.00"), status="draft",
            bank_account=self.bank
        )
        Payout.objects.create(
            reference="PAY-TEST2", company=self.company,
            total_amount=Decimal("200.00"), status="approved",
            bank_account=self.bank
        )
        response = self.client.get(f"{self.BASE_URL}/?status=draft", headers=self._auth_admin())
        self.assertEqual(response.status_code, 200)
        data = response.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "draft")

    def test_get_payout_detail(self):
        payout = Payout.objects.create(
            reference="PAY-DETAIL", company=self.company,
            total_amount=Decimal("150.00"), status="draft",
            bank_account=self.bank
        )
        response = self.client.get(f"{self.BASE_URL}/{payout.id}/", headers=self._auth_admin())
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["reference"], "PAY-DETAIL")

    def test_create_payout_from_commissions(self):
        # CommissionRule sin campo 'name' — solo module, commission_type, percentage/fixed_amount
        rule = CommissionRule.objects.create(
            module="sales",
            commission_type="percentage",
            percentage=Decimal("10.00")
        )
        record = CommissionRecord.objects.create(
            company=self.company, commission_rule=rule,
            gross_amount=Decimal("1000.00"), retention_amount=Decimal("0.00"),
            net_amount=Decimal("100.00"), status="pending"
        )
        payload = {
            "company_id": self.company.id,
            "bank_account_id": self.bank.id,
            "description": "Pago de prueba",
            "item_ids": [record.id]
        }
        # Ninja 1.6.2 con Body(): enviar JSON plano al body (no wrapped)
        response = self.client.post(
            f"{self.BASE_URL}/", json=payload, headers=self._auth_admin()
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "draft")
        self.assertEqual(data["total_amount"], "100.00")
        payout = Payout.objects.get(id=data["id"])
        self.assertEqual(payout.items.count(), 1)
        record.refresh_from_db()
        # La comisión usada en el payout debe marcarse como 'paid'
        self.assertEqual(record.status, "paid")

    def test_approve_payout(self):
        payout = Payout.objects.create(
            reference="PAY-APPROVE", company=self.company,
            total_amount=Decimal("100.00"), status="draft",
            bank_account=self.bank
        )
        response = self.client.post(
            f"{self.BASE_URL}/{payout.id}/approve/", headers=self._auth_admin()
        )
        self.assertEqual(response.status_code, 200)
        payout.refresh_from_db()
        self.assertEqual(payout.status, "approved")
        self.assertIsNotNone(payout.approved_by)
        self.assertIsNotNone(payout.approved_at)

    def test_cancel_draft_payout(self):
        payout = Payout.objects.create(
            reference="PAY-CANCEL", company=self.company,
            total_amount=Decimal("100.00"), status="draft",
            bank_account=self.bank
        )
        response = self.client.post(
            f"{self.BASE_URL}/{payout.id}/cancel/", headers=self._auth_admin()
        )
        self.assertEqual(response.status_code, 200)
        payout.refresh_from_db()
        self.assertEqual(payout.status, "cancelled")

    def test_cancel_paid_payout_fails(self):
        payout = Payout.objects.create(
            reference="PAY-PAID", company=self.company,
            total_amount=Decimal("100.00"), status="paid",
            bank_account=self.bank
        )
        response = self.client.post(
            f"{self.BASE_URL}/{payout.id}/cancel/", headers=self._auth_admin()
        )
        self.assertEqual(response.status_code, 400)

    def test_bank_account_list(self):
        BankAccount.objects.create(
            bank_code="produbanco", account_number="1111111111",
            account_type="checking", account_holder_name="Holder 1",
            company=self.company, is_active=True
        )
        response = self.client.get(f"{self.BASE_URL}/bank-accounts/", headers=self._auth_admin())
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertGreaterEqual(len(results), 1)

    def test_create_bank_account(self):
        payload = {
            "company_id": self.company.id,
            "bank_code": "pichincha",
            "account_number": "2222222222",
            "account_type": "savings",
            "account_holder_name": "Test Holder",
            "is_active": True,
            "is_default": False
        }
        # Ninja 1.6.2 con Body(): enviar JSON plano al body usando json=
        response = self.client.post(
            f"{self.BASE_URL}/bank-accounts/", json=payload, headers=self._auth_admin()
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["bank_code"], "pichincha")
        self.assertTrue(data["is_active"])
        self.assertIn("bank_display", data)

    def test_update_bank_account(self):
        bank = BankAccount.objects.create(
            bank_code="produbanco", account_number="3333333333",
            account_type="checking", account_holder_name="Old Name",
            company=self.company, is_active=True
        )
        payload = {
            "account_holder_name": "New Name",
            "is_active": False
        }
        response = self.client.put(
            f"{self.BASE_URL}/bank-accounts/{bank.id}/", json=payload, headers=self._auth_admin()
        )
        self.assertEqual(response.status_code, 200)
        bank.refresh_from_db()
        self.assertEqual(bank.account_holder_name, "New Name")
        self.assertFalse(bank.is_active)

    def test_delete_bank_account_soft(self):
        bank = BankAccount.objects.create(
            bank_code="produbanco", account_number="4444444444",
            account_type="checking", account_holder_name="ToDelete",
            company=self.company, is_active=True
        )
        response = self.client.delete(
            f"{self.BASE_URL}/bank-accounts/{bank.id}/", headers=self._auth_admin()
        )
        self.assertEqual(response.status_code, 200)
        bank.refresh_from_db()
        self.assertFalse(bank.is_active)

    def test_list_available_banks(self):
        response = self.client.get(f"{self.BASE_URL}/banks/", headers=self._auth_admin())
        self.assertEqual(response.status_code, 200)
        banks = response.json()
        self.assertIsInstance(banks, list)
        codes = [b["code"] for b in banks]
        self.assertIn("produbanco", codes)
        self.assertIn("pichincha", codes)
        self.assertIn("guayaquil", codes)

    def test_list_pending_commissions(self):
        rule = CommissionRule.objects.create(
            module="sales",
            commission_type="percentage",
            percentage=Decimal("5.00")
        )
        CommissionRecord.objects.create(
            company=self.company, commission_rule=rule,
            gross_amount=Decimal("500.00"), retention_amount=Decimal("0.00"),
            net_amount=Decimal("25.00"), status="pending"
        )
        CommissionRecord.objects.create(
            company=self.company, commission_rule=rule,
            gross_amount=Decimal("300.00"), retention_amount=Decimal("0.00"),
            net_amount=Decimal("15.00"), status="paid"
        )
        response = self.client.get(
            f"{self.BASE_URL}/commissions/pending/?company_id={self.company.id}",
            headers=self._auth_admin()
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertEqual(len(results), 1)


class BankProviderFactoryTests(TestCase):
    def test_factory_produbanco(self):
        from apps.payouts.factory import BankProviderFactory
        from apps.payouts.providers.produbanco import ProdubancoProvider
        provider = BankProviderFactory('produbanco', api_key='test', api_secret='test')
        self.assertIsInstance(provider, ProdubancoProvider)

    def test_factory_unknown_raises(self):
        from apps.payouts.factory import BankProviderFactory
        with self.assertRaises(ValueError) as ctx:
            BankProviderFactory('unknown')
        self.assertIn('Banco no soportado', str(ctx.exception))

    def test_factory_case_insensitive(self):
        from apps.payouts.factory import BankProviderFactory
        provider = BankProviderFactory('PRODUBANCO', api_key='k', api_secret='s')
        self.assertIsNotNone(provider)


class PayoutConfigTests(TestCase):
    def test_payout_config_creation(self):
        from apps.core_companies.models import Company
        company = Company.objects.create(name="TestCo2", tax_id="0987654321")
        config = PayoutConfig.objects.create(
            company=company,
            auto_approve=False,
            retention_rate=Decimal("10.00"),
            retain_until_threshold=Decimal("100.00"),
            payout_schedule="weekly"
        )
        self.assertEqual(config.company, company)
        self.assertEqual(config.retention_rate, Decimal("10.00"))
        self.assertEqual(config.payout_schedule, "weekly")


class CommissionRuleTests(TestCase):
    def test_percentage_rule_str(self):
        rule = CommissionRule.objects.create(
            module="sales",
            commission_type="percentage",
            percentage=Decimal("5.00")
        )
        self.assertIn("5.00%", str(rule))

    def test_fixed_rule_str(self):
        rule = CommissionRule.objects.create(
            module="sales",
            commission_type="fixed",
            fixed_amount=Decimal("20.00")
        )
        self.assertIn("$20.00", str(rule))
