import pytest
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.core_companies.models import Company
from apps.payouts.models import BankAccount, CommissionRule, Payout, PayoutItem, PayoutConfig


class TestBankAccountModel(TestCase):
    """Tests for BankAccount model"""

    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(
            name='Test Company',
            tax_id='1234567890',
            email='test@example.com'
        )

    def test_bank_account_requires_company(self):
        """BankAccount must have a company"""
        ba = BankAccount.objects.create(
            company=self.company,
            bank_code='pichincha',
            account_number='1234567890',
            account_type='checking',
            account_holder_name='Walter Cun'
        )
        self.assertEqual(ba.company, self.company)

    def test_bank_account_without_company_fails(self):
        """BankAccount without company should fail validation"""
        ba = BankAccount(
            bank_code='pichincha',
            account_number='1234567890',
            account_type='checking',
            account_holder_name='Test'
        )
        with self.assertRaises(ValidationError):
            ba.full_clean()

    def test_bank_account_str_representation(self):
        """BankAccount __str__ returns bank name and account number"""
        ba = BankAccount.objects.create(
            company=self.company,
            bank_code='pichincha',
            account_number='1234567890',
            account_type='checking',
            account_holder_name='Walter Cun'
        )
        self.assertEqual(str(ba), "Banco Pichincha - 1234567890")

    def test_bank_account_defaults(self):
        """Test default values for BankAccount"""
        ba = BankAccount.objects.create(
            company=self.company,
            bank_code='produbanco',
            account_number='9999999999',
            account_type='savings',
            account_holder_name='Test Holder'
        )
        self.assertTrue(ba.is_active)
        self.assertFalse(ba.is_default)
        self.assertEqual(ba.rut, '')

    def test_bank_account_ordering(self):
        """BankAccounts are ordered by is_default desc and created_at desc"""
        ba1 = BankAccount.objects.create(
            company=self.company,
            bank_code='pichincha',
            account_number='1111',
            account_type='checking',
            account_holder_name='Test1'
        )
        ba2 = BankAccount.objects.create(
            company=self.company,
            bank_code='guayaquil',
            account_number='2222',
            account_type='checking',
            account_holder_name='Test2',
            is_default=True
        )
        accounts = list(BankAccount.objects.all())
        self.assertTrue(accounts[0].is_default)


class TestCommissionRuleModel(TestCase):
    """Tests for CommissionRule model"""

    def test_commission_rule_creation(self):
        """Test basic commission rule creation"""
        rule = CommissionRule.objects.create(
            module='sales',
            commission_type='percentage',
            percentage=Decimal('5.50'),
            min_amount=Decimal('0'),
            created_by='admin'
        )
        self.assertEqual(rule.module, 'sales')
        self.assertEqual(rule.commission_type, 'percentage')
        self.assertEqual(rule.percentage, Decimal('5.50'))

    def test_commission_rule_percentage_validation_valid(self):
        """Percentage between 0 and 100 is valid"""
        rule = CommissionRule(
            module='purchases',
            commission_type='percentage',
            percentage=Decimal('50.00'),
            min_amount=Decimal('0')
        )
        rule.full_clean()
        rule.save()
        self.assertIsNotNone(rule.pk)

    def test_commission_rule_percentage_validation_invalid_above(self):
        """Percentage above 100 should fail validation"""
        rule = CommissionRule(
            module='sales',
            commission_type='percentage',
            percentage=Decimal('101.00'),
            min_amount=Decimal('0')
        )
        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_commission_rule_percentage_validation_invalid_below(self):
        """Negative percentage should fail validation"""
        rule = CommissionRule(
            module='sales',
            commission_type='percentage',
            percentage=Decimal('-5.00'),
            min_amount=Decimal('0')
        )
        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_commission_rule_fixed_amount(self):
        """Fixed commission rule works correctly"""
        rule = CommissionRule.objects.create(
            module='marketplace',
            commission_type='fixed',
            fixed_amount=Decimal('25.00'),
            min_amount=Decimal('0')
        )
        self.assertEqual(rule.fixed_amount, Decimal('25.00'))
        self.assertEqual(rule.percentage, Decimal('0'))

    def test_commission_rule_str_representation_percentage(self):
        """String representation for percentage type"""
        rule = CommissionRule.objects.create(
            module='sales',
            commission_type='percentage',
            percentage=Decimal('10.00')
        )
        self.assertEqual(str(rule), "Ventas - 10.00%")

    def test_commission_rule_str_representation_fixed(self):
        """String representation for fixed type"""
        rule = CommissionRule.objects.create(
            module='purchases',
            commission_type='fixed',
            fixed_amount=Decimal('50.00')
        )
        self.assertEqual(str(rule), "Compras - $50.00")

    def test_commission_rule_with_max_amount(self):
        """Commission rule with max_amount works"""
        rule = CommissionRule.objects.create(
            module='sales',
            commission_type='percentage',
            percentage=Decimal('5.00'),
            min_amount=Decimal('100'),
            max_amount=Decimal('10000')
        )
        self.assertEqual(rule.max_amount, Decimal('10000'))

    def test_commission_rule_applies_to_jsonfield(self):
        """applies_to JSONField accepts lists"""
        rule = CommissionRule.objects.create(
            module='marketplace',
            commission_type='percentage',
            percentage=Decimal('3.00'),
            min_amount=Decimal('0'),
            applies_to=[1, 2, 3]
        )
        self.assertEqual(rule.applies_to, [1, 2, 3])


class TestPayoutModel(TestCase):
    """Tests for Payout model"""

    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(
            name='Test Company',
            tax_id='1234567890',
            email='test@example.com'
        )
        cls.bank_account = BankAccount.objects.create(
            company=cls.company,
            bank_code='pichincha',
            account_number='1234567890',
            account_type='checking',
            account_holder_name='Walter Cun',
            is_default=True
        )

    def test_payout_creation(self):
        """Test basic payout creation"""
        payout = Payout.objects.create(
            reference='PAY-20260513-0002',
            company=self.company,
            bank_account=self.bank_account,
            total_amount=Decimal('5000.00'),
            currency='USD',
            status='draft',
            description='Monthly payouts'
        )
        self.assertEqual(payout.reference, 'PAY-20260513-0002')
        self.assertEqual(payout.status, 'draft')
        self.assertEqual(payout.total_amount, Decimal('5000.00'))

    def test_payout_str_representation(self):
        """Payout __str__ includes reference, company, and amount"""
        payout = Payout.objects.create(
            reference='PAY-TEST',
            company=self.company,
            bank_account=self.bank_account,
            total_amount=Decimal('1000.00')
        )
        expected = f"{payout.reference} - {payout.company} (${payout.total_amount})"
        self.assertEqual(str(payout), expected)

    def test_payout_status_choices(self):
        """Payout accepts all valid status choices"""
        statuses = ['draft', 'approved', 'processing', 'paid', 'failed', 'cancelled']
        for idx, status in enumerate(statuses):
            payout = Payout.objects.create(
                reference=f'PAY-TEST-{idx:04d}',
                company=self.company,
                bank_account=self.bank_account,
                total_amount=Decimal('100.00'),
                status=status
            )
            self.assertEqual(payout.status, status)

    def test_payout_ordering(self):
        """Payouts are ordered by -created_at"""
        p1 = Payout.objects.create(
            reference='PAY-001',
            company=self.company,
            bank_account=self.bank_account,
            total_amount=Decimal('100.00')
        )
        p2 = Payout.objects.create(
            reference='PAY-002',
            company=self.company,
            bank_account=self.bank_account,
            total_amount=Decimal('200.00')
        )
        payouts = list(Payout.objects.all())
        self.assertEqual(payouts[0].reference, 'PAY-002')

    def test_payout_with_approval(self):
        """Payout can be approved with user and timestamp"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='approver', password='test')
        payout = Payout.objects.create(
            reference='PAY-APPROVE',
            company=self.company,
            bank_account=self.bank_account,
            total_amount=Decimal('1000.00')
        )
        payout.approved_by = user
        payout.status = 'approved'
        payout.save()
        self.assertEqual(payout.approved_by, user)
        self.assertEqual(payout.status, 'approved')

    def test_payout_paid_fields(self):
        """Payout can store paid_at and bank_reference"""
        payout = Payout.objects.create(
            reference='PAY-PAID',
            company=self.company,
            bank_account=self.bank_account,
            total_amount=Decimal('5000.00'),
            status='paid'
        )
        payout.bank_reference = 'BANK-REF-12345'
        payout.save()
        self.assertEqual(payout.bank_reference, 'BANK-REF-12345')


class TestPayoutItemModel(TestCase):
    """Tests for PayoutItem model"""

    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(
            name='Test Company',
            tax_id='1234567890',
            email='test@example.com'
        )
        cls.bank_account = BankAccount.objects.create(
            company=cls.company,
            bank_code='pichincha',
            account_number='1234567890',
            account_type='checking',
            account_holder_name='Walter Cun'
        )
        cls.payout = Payout.objects.create(
            reference='PAY-001',
            company=cls.company,
            bank_account=cls.bank_account,
            total_amount=Decimal('1000.00')
        )

    def test_payout_item_creation(self):
        """Test basic payout item creation"""
        item = PayoutItem.objects.create(
            payout=self.payout,
            gross_amount=Decimal('1000.00'),
            retention_amount=Decimal('100.00'),
            net_amount=Decimal('900.00'),
            commission_type='sales_commission',
            description='Order #12345 commission'
        )
        self.assertEqual(item.payout, self.payout)
        self.assertEqual(item.gross_amount, Decimal('1000.00'))
        self.assertEqual(item.net_amount, Decimal('900.00'))

    def test_payout_item_net_equals_gross_minus_retention(self):
        """net_amount = gross_amount - retention_amount"""
        gross = Decimal('1500.00')
        retention = Decimal('150.00')
        item = PayoutItem.objects.create(
            payout=self.payout,
            gross_amount=gross,
            retention_amount=retention,
            net_amount=gross - retention,
            commission_type='percentage',
            description='Test item'
        )
        self.assertEqual(item.net_amount, item.gross_amount - item.retention_amount)

    def test_payout_item_str_representation(self):
        """PayoutItem __str__ shows payout reference and description"""
        item = PayoutItem.objects.create(
            payout=self.payout,
            gross_amount=Decimal('100.00'),
            retention_amount=Decimal('0'),
            net_amount=Decimal('100.00'),
            commission_type='fixed',
            description='Order commission'
        )
        expected = f"{self.payout.reference} - Order commission"
        self.assertEqual(str(item), expected)

    def test_payout_item_ordering(self):
        """PayoutItems are ordered by id"""
        item1 = PayoutItem.objects.create(
            payout=self.payout,
            gross_amount=Decimal('100.00'),
            retention_amount=Decimal('0'),
            net_amount=Decimal('100.00'),
            commission_type='test',
            description='First'
        )
        item2 = PayoutItem.objects.create(
            payout=self.payout,
            gross_amount=Decimal('200.00'),
            retention_amount=Decimal('0'),
            net_amount=Decimal('200.00'),
            commission_type='test',
            description='Second'
        )
        items = list(PayoutItem.objects.all())
        self.assertLess(items[0].id, items[1].id)

    def test_payout_item_nullable_foreign_keys(self):
        """order and purchase_order can be null"""
        item = PayoutItem.objects.create(
            payout=self.payout,
            gross_amount=Decimal('100.00'),
            retention_amount=Decimal('0'),
            net_amount=Decimal('100.00'),
            commission_type='test',
            description='Test without order'
        )
        self.assertIsNone(item.order)
        self.assertIsNone(item.purchase_order)


class TestPayoutConfigModel(TestCase):
    """Tests for PayoutConfig model"""

    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(
            name='Test Company',
            tax_id='1234567890',
            email='test@example.com'
        )

    def test_payout_config_creation_company_one_to_one(self):
        """PayoutConfig is one-to-one with Company"""
        config = PayoutConfig.objects.create(
            company=self.company,
            auto_approve=False,
            retention_rate=Decimal('10.00'),
            retain_until_threshold=Decimal('100.00'),
            payout_schedule='weekly'
        )
        self.assertEqual(config.company, self.company)
        self.assertEqual(config.pk, self.company.pk)

    def test_payout_config_company_unique_constraint(self):
        """Only one PayoutConfig per company allowed"""
        PayoutConfig.objects.create(
            company=self.company,
            retention_rate=Decimal('10.00'),
            retain_until_threshold=Decimal('100.00')
        )
        with self.assertRaises(Exception):
            PayoutConfig.objects.create(
                company=self.company,
                retention_rate=Decimal('15.00'),
                retain_until_threshold=Decimal('200.00')
            )

    def test_payout_config_defaults(self):
        """Test default values for PayoutConfig"""
        config = PayoutConfig.objects.create(company=self.company)
        self.assertFalse(config.auto_approve)
        self.assertEqual(config.retention_rate, Decimal('10.00'))
        self.assertEqual(config.retain_until_threshold, Decimal('100.00'))
        self.assertEqual(config.payout_schedule, 'weekly')
        self.assertEqual(config.notify_emails, [])

    def test_payout_config_schedule_choices(self):
        """PayoutConfig accepts all schedule choices"""
        schedules = ['daily', 'weekly', 'monthly']
        for idx, schedule in enumerate(schedules):
            company = Company.objects.create(
                name=f'Test Company {idx}',
                slug=f'test-company-{idx}-{schedule}',
                tax_id=f'{idx}1234567890',
                email=f'test{idx}@example.com'
            )
            config = PayoutConfig.objects.create(
                company=company,
                payout_schedule=schedule,
                retention_rate=Decimal('10.00'),
                retain_until_threshold=Decimal('100.00')
            )
            self.assertEqual(config.payout_schedule, schedule)

    def test_payout_config_str_representation(self):
        """PayoutConfig __str__ shows company name"""
        config = PayoutConfig.objects.create(company=self.company)
        expected = f"Configuración - {self.company}"
        self.assertEqual(str(config), expected)

    def test_payout_config_jsonfield_emails(self):
        """notify_emails JSONField stores list of emails"""
        emails = ['admin@example.com', 'finance@example.com']
        config = PayoutConfig.objects.create(
            company=self.company,
            notify_emails=emails,
            retention_rate=Decimal('10.00'),
            retain_until_threshold=Decimal('100.00')
        )
        self.assertEqual(config.notify_emails, emails)

    def test_payout_config_retention_rate_bounds(self):
        """Retention rate should be between 0 and 100"""
        # Valid: 0%
        config = PayoutConfig(
            company=self.company,
            retention_rate=Decimal('0.00'),
            retain_until_threshold=Decimal('100.00')
        )
        config.full_clean()

        # Valid: 100%
        config.retention_rate = Decimal('100.00')
        config.full_clean()

        # Invalid: > 100%
        config.retention_rate = Decimal('101.00')
        with self.assertRaises(ValidationError):
            config.full_clean()
