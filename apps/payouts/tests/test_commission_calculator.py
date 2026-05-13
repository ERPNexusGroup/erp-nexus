"""Comprehensive tests for CommissionCalculator service."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone

from apps.core_companies.models import Company
from apps.facturacion.models import Customer
from apps.sales.models import Order
from apps.purchases.models import PurchaseOrder, Supplier
from apps.payouts.models import CommissionRule, CommissionRecord, PayoutConfig
from apps.payouts.services import CommissionCalculator


class CommissionCalculatorTestCase(TestCase):
    """Base test case with common fixtures."""

    @classmethod
    def setUpTestData(cls):
        # Create company
        cls.company = Company.objects.create(
            name='Test Company',
            slug='test-company',
            tax_id='1234567890001',
            email='test@test.com'
        )

        # Create customer for orders
        cls.customer = Customer.objects.create(
            company=cls.company,
            identification_type='05',
            identification_number='1723456789',
            name='Customer Test',
            email='customer@test.com'
        )

        # Create supplier for purchase orders
        cls.supplier_customer = Customer.objects.create(
            company=cls.company,
            identification_type='04',
            identification_number='0999999999001',
            name='Supplier Customer',
            razon_social='Supplier Company S.A.'
        )
        cls.supplier = Supplier.objects.create(
            customer=cls.supplier_customer,
            vendor_number='SUP-001',
            rating=5
        )

        # Create PayoutConfig with 10% retention
        cls.payout_config = PayoutConfig.objects.create(
            company=cls.company,
            retention_rate=Decimal('10.0'),
            retain_until_threshold=Decimal('100.0')
        )


class TestOrderCommissionCalculation(CommissionCalculatorTestCase):
    """Tests for calculate_for_order method."""

    def setUp(self):
        # Ensure each test gets fresh data: create a new active rule
        self.rule = CommissionRule.objects.create(
            module='sales',
            commission_type='percentage',
            percentage=Decimal('10.00'),
            is_active=True
        )

    def test_calculate_percentage_commission(self):
        """Calcular comisión porcentual 10% sobre $1120 total = $112."""
        order = Order.objects.create(
            order_number=f'ORD-{timezone.now().timestamp()}',
            customer=self.customer,
            issue_date=timezone.now().date(),
            delivery_date=timezone.now().date() + timedelta(days=7),
            status='completed',
            subtotal=Decimal('1000.00'),
            tax=Decimal('120.00'),
            total=Decimal('1120.00')
        )

        record = CommissionCalculator.calculate_for_order(order)
        self.assertIsNotNone(record)
        self.assertEqual(record.gross_amount, Decimal('112.00'))  # 10% of 1120 total
        self.assertEqual(record.retention_amount, Decimal('11.20'))  # 10% of 112 = 11.2
        self.assertEqual(record.net_amount, Decimal('100.80'))
        self.assertEqual(record.status, 'pending')
        self.assertEqual(record.company, self.company)
        self.assertEqual(record.commission_rule.module, 'sales')

    def test_calculate_fixed_commission(self):
        """Calcular comisión fija."""
        self.rule.delete()
        CommissionRule.objects.create(
            module='sales',
            commission_type='fixed',
            fixed_amount=Decimal('50.00'),
            is_active=True
        )
        order = Order.objects.create(
            order_number=f'ORD-{timezone.now().timestamp()}-FIXED',
            customer=self.customer,
            issue_date=timezone.now().date(),
            delivery_date=timezone.now().date() + timedelta(days=7),
            status='completed',
            subtotal=Decimal('1000.00'),
            tax=Decimal('120.00'),
            total=Decimal('1120.00')
        )

        record = CommissionCalculator.calculate_for_order(order)
        self.assertIsNotNone(record)
        self.assertEqual(record.gross_amount, Decimal('50.00'))
        self.assertEqual(record.retention_amount, Decimal('5.00'))  # 10% retention
        self.assertEqual(record.net_amount, Decimal('45.00'))

    def test_min_amount_threshold(self):
        """Comisión por debajo del mínimo debe ser $0."""
        self.rule.delete()
        CommissionRule.objects.create(
            module='sales',
            commission_type='percentage',
            percentage=Decimal('10.00'),
            min_amount=Decimal('50.00'),
            is_active=True
        )
        order = Order.objects.create(
            order_number=f'ORD-{timezone.now().timestamp()}-MIN',
            customer=self.customer,
            issue_date=timezone.now().date(),
            delivery_date=timezone.now().date() + timedelta(days=7),
            status='completed',
            subtotal=Decimal('100.00'),
            tax=Decimal('12.00'),
            total=Decimal('112.00')
        )

        record = CommissionCalculator.calculate_for_order(order)
        # gross = 10% of 112 = 11.2, which is < min 50 => gross = 0
        self.assertEqual(record.gross_amount, Decimal('0.00'))
        self.assertEqual(record.retention_amount, Decimal('0.00'))
        self.assertEqual(record.net_amount, Decimal('0.00'))

    def test_max_amount_cap(self):
        """Comisión por encima del máximo debe ser limitada."""
        self.rule.delete()
        CommissionRule.objects.create(
            module='sales',
            commission_type='percentage',
            percentage=Decimal('10.00'),
            max_amount=Decimal('80.00'),
            is_active=True
        )
        order = Order.objects.create(
            order_number=f'ORD-{timezone.now().timestamp()}-MAX',
            customer=self.customer,
            issue_date=timezone.now().date(),
            delivery_date=timezone.now().date() + timedelta(days=7),
            status='completed',
            subtotal=Decimal('1000.00'),
            tax=Decimal('120.00'),
            total=Decimal('1120.00')
        )

        record = CommissionCalculator.calculate_for_order(order)
        # gross = 10% of 1120 = 112, but capped at max 80
        self.assertEqual(record.gross_amount, Decimal('80.00'))
        self.assertEqual(record.retention_amount, Decimal('8.00'))
        self.assertEqual(record.net_amount, Decimal('72.00'))

    def test_no_active_rule_returns_none(self):
        """Si no hay regla activa, retorna None."""
        # Deactivate all rules
        self.rule.delete()

        order = Order.objects.create(
            order_number=f'ORD-{timezone.now().timestamp()}-NORULE',
            customer=self.customer,
            issue_date=timezone.now().date(),
            delivery_date=timezone.now().date() + timedelta(days=7),
            status='completed',
            subtotal=Decimal('1000.00'),
            tax=Decimal('120.00'),
            total=Decimal('1120.00')
        )

        record = CommissionCalculator.calculate_for_order(order)
        self.assertIsNone(record)

    def test_multiple_rules_uses_first_active(self):
        """Con múltiples reglas activas, usa la más reciente (ordenada por created_at descendente)."""
        # Since we create self.rule in setUp, create another earlier one
        old_rule = CommissionRule.objects.create(
            module='sales',
            commission_type='percentage',
            percentage=Decimal('5.00'),
            is_active=True,
            created_at=timezone.now() - timedelta(days=1)
        )
        # self.rule is newer and has 15% but we need to change it
        self.rule.delete()
        rule2 = CommissionRule.objects.create(
            module='sales',
            commission_type='percentage',
            percentage=Decimal('15.00'),
            is_active=True,
            created_at=timezone.now()
        )

        order = Order.objects.create(
            order_number=f'ORD-{timezone.now().timestamp()}-MULTI',
            customer=self.customer,
            issue_date=timezone.now().date(),
            delivery_date=timezone.now().date() + timedelta(days=7),
            status='completed',
            subtotal=Decimal('1000.00'),
            tax=Decimal('120.00'),
            total=Decimal('1120.00')
        )

        record = CommissionCalculator.calculate_for_order(order)
        # Should use the most recent rule (15%)
        self.assertEqual(record.commission_rule, rule2)
        self.assertEqual(record.gross_amount, Decimal('168.00'))  # 15% of 1120

    def test_default_retention_when_no_config(self):
        """Retención por defecto 10% si no existe PayoutConfig."""
        # Delete config ONLY, keep rule
        self.payout_config.delete()

        order = Order.objects.create(
            order_number=f'ORD-{timezone.now().timestamp()}-DEFRET',
            customer=self.customer,
            issue_date=timezone.now().date(),
            delivery_date=timezone.now().date() + timedelta(days=7),
            status='completed',
            subtotal=Decimal('1000.00'),
            tax=Decimal('120.00'),
            total=Decimal('1120.00')
        )

        record = CommissionCalculator.calculate_for_order(order)
        self.assertIsNotNone(record)
        self.assertEqual(record.retention_amount, Decimal('11.20'))  # 10% of 112


class TestPurchaseOrderCommissionCalculation(CommissionCalculatorTestCase):
    """Tests for calculate_for_purchase_order method."""

    def setUp(self):
        self.rule = CommissionRule.objects.create(
            module='purchases',
            commission_type='percentage',
            percentage=Decimal('5.00'),
            is_active=True
        )

    def test_calculate_purchase_commission_percentage(self):
        """Calcular comisión para PO con porcentaje."""
        po = PurchaseOrder.objects.create(
            po_number=f'PO-{timezone.now().timestamp()}',
            supplier=self.supplier,
            order_date=timezone.now().date(),
            expected_delivery=timezone.now().date() + timedelta(days=7),
            status='received',
            subtotal=Decimal('2000.00'),
            tax=Decimal('240.00'),
            total=Decimal('2240.00')
        )

        record = CommissionCalculator.calculate_for_purchase_order(po)
        self.assertIsNotNone(record)
        self.assertEqual(record.gross_amount, Decimal('112.00'))  # 5% of 2240
        self.assertEqual(record.retention_amount, Decimal('11.20'))
        self.assertEqual(record.net_amount, Decimal('100.80'))
        self.assertEqual(record.purchase_order, po)
        self.assertEqual(record.company, self.company)

    def test_calculate_purchase_fixed_commission(self):
        """Calcular comisión fija para PO."""
        self.rule.delete()
        CommissionRule.objects.create(
            module='purchases',
            commission_type='fixed',
            fixed_amount=Decimal('25.00'),
            is_active=True
        )
        po = PurchaseOrder.objects.create(
            po_number=f'PO-{timezone.now().timestamp()}-FIXED',
            supplier=self.supplier,
            order_date=timezone.now().date(),
            expected_delivery=timezone.now().date() + timedelta(days=7),
            status='received',
            subtotal=Decimal('500.00'),
            tax=Decimal('60.00'),
            total=Decimal('560.00')
        )

        record = CommissionCalculator.calculate_for_purchase_order(po)
        self.assertEqual(record.gross_amount, Decimal('25.00'))
        self.assertEqual(record.net_amount, Decimal('22.50'))


class TestGetPendingCommissions(CommissionCalculatorTestCase):
    """Tests for get_pending_commissions method."""

    def setUp(self):
        self.rule = CommissionRule.objects.create(
            module='sales',
            commission_type='percentage',
            percentage=Decimal('10.00'),
            is_active=True
        )

    def test_get_pending_commissions_returns_only_pending(self):
        """Retorna solo registros pendientes."""
        # Create a paid record first (in a separate test to avoid cross-test contamination)
        yesterday = timezone.now() - timedelta(days=1)
        order1 = Order.objects.create(
            order_number=f'ORD-{timezone.now().timestamp()}-PEND1',
            customer=self.customer,
            issue_date=yesterday.date(),
            delivery_date=yesterday.date() + timedelta(days=7),
            status='completed',
            subtotal=Decimal('1000.00'),
            tax=Decimal('120.00'),
            total=Decimal('1120.00')
        )
        rec1 = CommissionRecord.objects.create(
            order=order1,
            company=self.company,
            commission_rule=self.rule,
            gross_amount=Decimal('100.00'),
            retention_amount=Decimal('10.00'),
            net_amount=Decimal('90.00'),
            status='pending',
            created_at=yesterday
        )

        order2 = Order.objects.create(
            order_number=f'ORD-{timezone.now().timestamp()}-PAID',
            customer=self.customer,
            issue_date=timezone.now().date(),
            delivery_date=timezone.now().date() + timedelta(days=7),
            status='completed',
            subtotal=Decimal('500.00'),
            tax=Decimal('60.00'),
            total=Decimal('560.00')
        )
        rec2 = CommissionRecord.objects.create(
            order=order2,
            company=self.company,
            commission_rule=self.rule,
            gross_amount=Decimal('50.00'),
            retention_amount=Decimal('5.00'),
            net_amount=Decimal('45.00'),
            status='paid',
            created_at=timezone.now()
        )

        qs = CommissionCalculator.get_pending_commissions(self.company)
        self.assertEqual(qs.count(), 1)
        self.assertIn(rec1, qs)
        self.assertNotIn(rec2, qs)

    def test_get_pending_commissions_filter_by_date_range(self):
        """Filtra por rango de fechas usando fechas (date objects)."""
        from datetime import date as dt_date, datetime as dt_datetime

        # Use fixed UTC datetimes to avoid timezone ambiguity
        dt1 = timezone.make_aware(dt_datetime(2026, 5, 12, 12, 0, 0), timezone=timezone.UTC)
        dt2 = timezone.make_aware(dt_datetime(2026, 5, 13, 12, 0, 0), timezone=timezone.UTC)

        order1 = Order.objects.create(
            order_number='ORD-DATERANGE-1',
            customer=self.customer,
            issue_date=dt_date(2026, 5, 12),
            delivery_date=dt_date(2026, 5, 19),
            status='completed',
            subtotal=Decimal('1000.00'),
            tax=Decimal('120.00'),
            total=Decimal('1120.00')
        )
        rec1 = CommissionRecord.objects.create(
            order=order1,
            company=self.company,
            commission_rule=self.rule,
            gross_amount=Decimal('100.00'),
            retention_amount=Decimal('10.00'),
            net_amount=Decimal('90.00'),
            status='pending',
            created_at=dt1
        )

        order2 = Order.objects.create(
            order_number='ORD-DATERANGE-2',
            customer=self.customer,
            issue_date=dt_date(2026, 5, 13),
            delivery_date=dt_date(2026, 5, 20),
            status='completed',
            subtotal=Decimal('1000.00'),
            tax=Decimal('120.00'),
            total=Decimal('1120.00')
        )
        rec2 = CommissionRecord.objects.create(
            order=order2,
            company=self.company,
            commission_rule=self.rule,
            gross_amount=Decimal('100.00'),
            retention_amount=Decimal('10.00'),
            net_amount=Decimal('90.00'),
            status='pending',
            created_at=dt2
        )

        # Filter by date range for May 12
        qs = CommissionCalculator.get_pending_commissions(
            self.company,
            start_date=dt_date(2026, 5, 12),
            end_date=dt_date(2026, 5, 12)
        )
        self.assertEqual(qs.count(), 1)
        self.assertIn(rec1, qs)
        self.assertNotIn(rec2, qs)


class TestBulkCreateCommissions(CommissionCalculatorTestCase):
    """Tests for bulk_create_from_orders and bulk_create_from_purchase_orders."""

    def setUp(self):
        self.rule = CommissionRule.objects.create(
            module='sales',
            commission_type='percentage',
            percentage=Decimal('10.00'),
            is_active=True
        )

    def test_bulk_create_from_orders(self):
        """Crea múltiples registros en bulk."""
        orders = []
        for i in range(5):
            order = Order.objects.create(
                order_number=f'ORD-{timezone.now().timestamp()}-BULK-{i}',
                customer=self.customer,
                issue_date=timezone.now().date() + timedelta(days=i),
                delivery_date=timezone.now().date() + timedelta(days=i+7),
                status='completed',
                subtotal=Decimal('1000.00'),
                tax=Decimal('120.00'),
                total=Decimal('1120.00')
            )
            orders.append(order)

        records = CommissionCalculator.bulk_create_from_orders(orders)
        self.assertEqual(len(records), 5)

        # Verify in DB
        saved = CommissionRecord.objects.filter(order__in=orders)
        self.assertEqual(saved.count(), 5)

    def test_bulk_create_skips_orders_without_rule(self):
        """Omite órdenes si no hay regla activa."""
        CommissionRule.objects.all().delete()

        order = Order.objects.create(
            order_number=f'ORD-{timezone.now().timestamp()}-NORULEBULK',
            customer=self.customer,
            issue_date=timezone.now().date(),
            delivery_date=timezone.now().date() + timedelta(days=7),
            status='completed',
            subtotal=Decimal('1000.00'),
            tax=Decimal('120.00'),
            total=Decimal('1120.00')
        )

        records = CommissionCalculator.bulk_create_from_orders([order])
        self.assertEqual(len(records), 0)

    def test_bulk_create_from_purchase_orders(self):
        """Crea múltiples registros en bulk desde PurchaseOrders."""
        # Create active rule for purchases
        purchase_rule = CommissionRule.objects.create(
            module='purchases',
            commission_type='percentage',
            percentage=Decimal('5.00'),
            is_active=True
        )
        po_list = []
        for i in range(3):
            po = PurchaseOrder.objects.create(
                po_number=f'PO-{timezone.now().timestamp()}-BULK-{i}',
                supplier=self.supplier,
                order_date=timezone.now().date() + timedelta(days=i),
                expected_delivery=timezone.now().date() + timedelta(days=i+7),
                status='received',
                subtotal=Decimal('2000.00'),
                tax=Decimal('240.00'),
                total=Decimal('2240.00')
            )
            po_list.append(po)

        records = CommissionCalculator.bulk_create_from_purchase_orders(po_list)
        self.assertEqual(len(records), 3)
        saved = CommissionRecord.objects.filter(purchase_order__in=po_list)
        self.assertEqual(saved.count(), 3)

    def test_bulk_create_empty_list(self):
        """Lista vacía retorna lista vacía."""
        records = CommissionCalculator.bulk_create_from_orders([])
        self.assertEqual(len(records), 0)
        records_po = CommissionCalculator.bulk_create_from_purchase_orders([])
        self.assertEqual(len(records_po), 0)


class TestDecimalPrecision(CommissionCalculatorTestCase):
    """Tests for decimal rounding precision."""

    def setUp(self):
        self.rule = CommissionRule.objects.create(
            module='sales',
            commission_type='percentage',
            percentage=Decimal('11.11'),  # 11.11% of 1000 = 111.1
            is_active=True
        )

    def test_rounding_down_to_two_decimals(self):
        """Redondea hacia abajo a 2 decimales."""
        order = Order.objects.create(
            order_number=f'ORD-{timezone.now().timestamp()}-ROUND',
            customer=self.customer,
            issue_date=timezone.now().date(),
            delivery_date=timezone.now().date() + timedelta(days=7),
            status='completed',
            subtotal=Decimal('1000.00'),
            tax=Decimal('120.00'),
            total=Decimal('1120.00')
        )

        record = CommissionCalculator.calculate_for_order(order)
        # 1120 * 0.1111 = 124.432 -> 124.43 (ROUND_DOWN)
        self.assertEqual(record.gross_amount, Decimal('124.43'))
