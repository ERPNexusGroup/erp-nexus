"""Services for payout commission calculations."""
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, time
from django.utils import timezone

from .models import CommissionRule, CommissionRecord, PayoutConfig


class CommissionCalculator:
    """Servicio de cálculo de comisiones por orden/compra."""

    @staticmethod
    def calculate_for_order(order) -> CommissionRecord | None:
        """
        Calcula comisión para una Order de sales.
        Returns: CommissionRecord (sin guardar — caller debe .save())
        """
        rule = CommissionRule.objects.filter(
            module='sales',
            is_active=True
        ).first()

        if not rule:
            return None

        company = order.customer.company
        gross = CommissionCalculator._compute_gross(rule, order.total)
        retention = CommissionCalculator._compute_retention(company, gross)
        net = gross - retention

        return CommissionRecord(
            order=order,
            company=company,
            commission_rule=rule,
            gross_amount=gross,
            retention_amount=retention,
            net_amount=net,
            status='pending',
        )

    @staticmethod
    def calculate_for_purchase_order(purchase_order) -> CommissionRecord | None:
        """
        Calcula comisión para una PurchaseOrder de compras.
        Returns: CommissionRecord (sin guardar — caller debe .save())
        """
        rule = CommissionRule.objects.filter(
            module='purchases',
            is_active=True
        ).first()

        if not rule:
            return None

        company = purchase_order.supplier.customer.company
        gross = CommissionCalculator._compute_gross(rule, purchase_order.total)
        retention = CommissionCalculator._compute_retention(company, gross)
        net = gross - retention

        return CommissionRecord(
            purchase_order=purchase_order,
            company=company,
            commission_rule=rule,
            gross_amount=gross,
            retention_amount=retention,
            net_amount=net,
            status='pending',
        )

    @staticmethod
    def _compute_gross(rule: CommissionRule, base_amount: Decimal) -> Decimal:
        """Calcula monto bruto según regla (percentage o fixed)."""
        if rule.commission_type == 'percentage':
            gross = base_amount * (rule.percentage / Decimal('100'))
        else:  # fixed
            gross = rule.fixed_amount

        # Aplicar min/max
        if rule.min_amount and gross < rule.min_amount:
            gross = Decimal('0')
        if rule.max_amount and gross > rule.max_amount:
            gross = rule.max_amount

        return gross.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    @staticmethod
    def _compute_retention(company, gross_amount: Decimal) -> Decimal:
        """Calcula retención SRI según configuración de empresa."""
        try:
            config = company.payout_config
            rate = config.retention_rate / Decimal('100')
        except PayoutConfig.DoesNotExist:
            rate = Decimal('0.10')  # default 10%

        retention = gross_amount * rate
        return retention.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    @staticmethod
    def get_pending_commissions(company, start_date=None, end_date=None):
        """
        Retorna queryset de CommissionRecord pendientes para una empresa.
        Filtra por created_at rango si se proveen fechas (date or datetime).
        """
        qs = CommissionRecord.objects.filter(
            company=company,
            status='pending'
        ).select_related('order', 'purchase_order', 'commission_rule')

        if start_date and end_date:
            # Construir rango de datetimeaware para cubrir todo el día si son date objects
            if isinstance(start_date, datetime):
                start_dt = start_date if timezone.is_aware(start_date) else timezone.make_aware(start_date)
            else:
                # date → datetime 00:00:00 aware
                start_dt = timezone.make_aware(datetime.combine(start_date, time.min))

            if isinstance(end_date, datetime):
                end_dt = end_date if timezone.is_aware(end_date) else timezone.make_aware(end_date)
            else:
                # date → datetime 23:59:59.999999 aware
                end_dt = timezone.make_aware(datetime.combine(end_date, time.max))

            qs = qs.filter(created_at__gte=start_dt, created_at__lte=end_dt)
        elif start_date:
            if isinstance(start_date, datetime):
                start_dt = start_date if timezone.is_aware(start_date) else timezone.make_aware(start_date)
                qs = qs.filter(created_at__gte=start_dt)
            else:
                qs = qs.filter(created_at__date__gte=start_date)
        elif end_date:
            if isinstance(end_date, datetime):
                end_dt = end_date if timezone.is_aware(end_date) else timezone.make_aware(end_date)
                qs = qs.filter(created_at__lte=end_dt)
            else:
                qs = qs.filter(created_at__date__lte=end_date)

        return qs

    @staticmethod
    def bulk_create_from_orders(orders):
        """Crea CommissionRecords en bulk para lista de orders."""
        records = []
        for order in orders:
            record = CommissionCalculator.calculate_for_order(order)
            if record:
                records.append(record)
        return CommissionRecord.objects.bulk_create(records, ignore_conflicts=True)

    @staticmethod
    def bulk_create_from_purchase_orders(purchase_orders):
        """Crea CommissionRecords en bulk para lista de purchase orders."""
        records = []
        for po in purchase_orders:
            record = CommissionCalculator.calculate_for_purchase_order(po)
            if record:
                records.append(record)
        return CommissionRecord.objects.bulk_create(records, ignore_conflicts=True)
