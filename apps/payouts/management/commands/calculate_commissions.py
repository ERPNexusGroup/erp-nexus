"""Management command to calculate pending commissions."""
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction

from sales.models import Order
from purchases.models import PurchaseOrder
from apps.payouts.services import CommissionCalculator


class Command(BaseCommand):
    help = 'Calcula comisiones pendientes por órdenes completadas o PO recibidas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Fecha específica YYYY-MM-DD (default: hoy)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar, no guardar'
        )
        parser.add_argument(
            '--module',
            type=str,
            choices=['sales', 'purchases', 'all'],
            default='all',
            help='Módulo a procesar: sales, purchases, o all (default: all)'
        )

    def handle(self, *args, **options):
        date_str = options.get('date')
        dry_run = options['dry_run']
        module = options['module']

        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Formato de fecha inválido. Use YYYY-MM-DD')
        else:
            target_date = timezone.now().date()

        self.stdout.write(f"Procesando comisiones para fecha: {target_date}")
        if dry_run:
            self.stdout.write(self.style.WARNING("MODO DRY-RUN — no se guardarán cambios"))

        total_created = 0

        if module in ['sales', 'all']:
            orders = Order.objects.filter(
                status='completed',
                updated_at__date=target_date
            )
            self.stdout.write(f"Órdenes de venta encontradas: {orders.count()}")

            for order in orders:
                # Verificar que no exista ya
                if order.commission_records.exists():
                    continue

                record = CommissionCalculator.calculate_for_order(order)
                if record:
                    if dry_run:
                        self.stdout.write(
                            f"[DRY-RUN] Order {order.order_number}: "
                            f"gross={record.gross_amount}, "
                            f"ret={record.retention_amount}, "
                            f"net={record.net_amount}"
                        )
                    else:
                        record.save()
                        total_created += 1

        if module in ['purchases', 'all']:
            po_list = PurchaseOrder.objects.filter(
                status='received',
                updated_at__date=target_date
            )
            self.stdout.write(f"Órdenes de compra encontradas: {po_list.count()}")

            for po in po_list:
                if po.commission_records.exists():
                    continue

                record = CommissionCalculator.calculate_for_purchase_order(po)
                if record:
                    if dry_run:
                        self.stdout.write(
                            f"[DRY-RUN] PO {po.po_number}: "
                            f"gross={record.gross_amount}, "
                            f"ret={record.retention_amount}, "
                            f"net={record.net_amount}"
                        )
                    else:
                        record.save()
                        total_created += 1

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry-run completado — sin cambios en BD"))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Comisiones calculadas y guardadas: {total_created} registros")
            )
