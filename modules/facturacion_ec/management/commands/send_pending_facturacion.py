# Management command: send_pending_facturacion
from django.core.management.base import BaseCommand
from django.utils import timezone
from modules.facturacion_ec.models import Invoice
from modules.facturacion_ec.services import (
    send_invoice_to_sri,  # función que implementaremos
    XMLGenerator,
    DigitalSigner,
)


class Command(BaseCommand):
    help = "Envía facturas pendientes a SRI Ecuador"

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

        # Buscar facturas pendientes
        queryset = Invoice.objects.filter(sri_status='pending').order_by('date', 'id')
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        pending = queryset[:limit]
        total = pending.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("✅ No hay facturas pendientes por enviar"))
            return

        self.stdout.write(f"📤 Enviando {total} facturas pendientes...")

        if dry_run:
            for inv in pending:
                self.stdout.write(f"  - {inv.number} ({inv.company.name})")
            return

        success_count = 0
        error_count = 0

        for invoice in pending:
            try:
                result = send_invoice_to_sri(invoice.id)
                if result.get('success'):
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ {invoice.number}: {result.get('estado')}")
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  ✗ {invoice.number}: {result.get('mensaje')}")
                    )
            except Exception as e:
                error_count += 1
                self.stderr.write(self.style.ERROR(f"  ✗ {invoice.number}: {str(e)})"))

        self.stdout.write("")
        self.stdout.write(f"Resumen: {success_count} exitosas, {error_count} errores")
