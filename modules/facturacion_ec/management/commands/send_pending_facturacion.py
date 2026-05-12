"""
Management command: send_pending_facturacion

Envía facturas pendientes (core facturacion.Invoice con status=draft)
al SRI Ecuador usando el pipeline del plugin.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.facturacion.models import Invoice
from modules.facturacion_ec.services import send_invoice_to_sri, process_pending_invoices


class Command(BaseCommand):
    help = "Envía facturas pendientes a SRI Ecuador (plugin facturacion_ec)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Máximo número de facturas a enviar por ejecución'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar qué facturas se enviarían (no enviar)'
        )
        parser.add_argument(
            '--company',
            type=int,
            help='ID de empresa específica'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']
        company_id = options.get('company')

        # Buscar facturas pendientes (core facturacion)
        queryset = Invoice.objects.filter(status='draft').order_by('date', 'id')
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        pending = queryset[:limit]
        total = pending.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("✅ No hay facturas pendientes por enviar"))
            return

        self.stdout.write(f"📤 Enviando {total} facturas pendientes a SRI...")

        if dry_run:
            for inv in pending:
                self.stdout.write(f"  - {inv.number} ({inv.company.name})")
            return

        # Procesar por lote
        results = process_pending_invoices(limit=limit, company_id=company_id)

        for detail in results['details']:
            if 'OK' in detail or 'RECIBIDO' in detail:
                self.stdout.write(self.style.SUCCESS(f"  ✓ {detail}"))
            else:
                self.stdout.write(self.style.WARNING(f"  ✗ {detail}"))

        self.stdout.write("")
        self.stdout.write(f"Resumen: {results['success']} exitosas, {results['errors']} errores")
