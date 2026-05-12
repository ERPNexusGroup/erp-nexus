"""
Migration: Facturación EC — Legacy → Core + Plugin SRI

Migra datos desde el esquema monolítico antiguo (modules.facturacion_ec.models)
hacia la arquitectura separada:
- apps.facturacion.* (core)
- modules.facturacion_ec.* (plugin SRI)

USO:
  uv run python manage.py migrate_facturacion_ec_data [--dry-run] [--company-id N]

PRECAUCIÓN:
  - Ejecutar DESPUÉS de aplicar migraciones de apps.facturacion
  - Hacer backup de BD antes de ejecutar
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

import sys


class Command(BaseCommand):
    help = "Migra datos facturacion_legacy → core facturacion + plugin SRI"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular migración sin guardar cambios'
        )
        parser.add_argument(
            '--company-id',
            type=int,
            help='Migrar solo para empresa específica'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Tamaño de lote para commit'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        company_id = options.get('company_id')
        batch_size = options['batch_size']

        self.stdout.write(self.style.NOTICE("="*60))
        self.stdout.write(self.style.NOTICE("MIGRACIÓN: facturacion_ec legacy → Core + Plugin SRI"))
        self.stdout.write(self.style.NOTICE("="*60))

        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  MODO DRY-RUN: no se guardarán cambios"))

        # Importar modelos legacy y nuevos
        try:
            # Legacy (tabla única modules_facturacion_ec)
            from modules.facturacion_ec.models import (
                LegacyInvoice,   # ← это старые модели, нужно переименовать
                LegacyInvoiceLine,
                LegacyCustomer,
                LegacyProduct,
                LegacySRISendLog,
                LegacyElectronicDocument,
            )
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"❌ No se pudieron importar modelos legacy: {e}"))
            self.stdout.write(self.style.NOTICE("Asegúrate de que las migraciones antiguas están aplicadas."))
            return

        from apps.facturacion.models import Invoice, Customer, Product, InvoiceLine
        from modules.facturacion_ec.models import InvoiceSRIExtension

        # Estadísticas
        stats = {
            'customers': 0,
            'products': 0,
            'invoices': 0,
            'lines': 0,
            'extensions': 0,
            'errors': 0,
        }

        # Paso 1: Migrar Customers
        self.stdout.write("\n📦 Paso 1/4 — Migrando Customers...")
        legacy_customers = LegacyCustomer.objects.all()
        if company_id:
            legacy_customers = legacy_customers.filter(company_id=company_id)

        total_customers = legacy_customers.count()
        self.stdout.write(f"  Encontrados: {total_customers}")

        for i, old_cust in enumerate(legacy_customers.iterator(), 1):
            try:
                new_cust, created = Customer.objects.get_or_create(
                    company=old_cust.company,
                    identification_type=old_cust.identification_type,
                    identification_number=old_cust.identification_number,
                    defaults={
                        'name': old_cust.name,
                        'email': old_cust.email or '',
                        'phone': old_cust.phone or '',
                        'address': old_cust.address or '',
                        'razon_social': old_cust.razon_social or '',
                        'is_active': old_cust.is_active,
                    }
                )
                if created and not dry_run:
                    stats['customers'] += 1
                if i % batch_size == 0:
                    self.stdout.write(f"    Progreso: {i}/{total_customers}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    ✗ Error migrando customer {old_cust.id}: {e}"))
                stats['errors'] += 1

        # Paso 2: Migrar Products
        self.stdout.write("\n📦 Paso 2/4 — Migrando Products...")
        legacy_products = LegacyProduct.objects.all()
        if company_id:
            legacy_products = legacy_products.filter(company_id=company_id)

        total_products = legacy_products.count()
        self.stdout.write(f"  Encontrados: {total_products}")

        for i, old_prod in enumerate(legacy_products.iterator(), 1):
            try:
                new_prod, created = Product.objects.get_or_create(
                    company=old_prod.company,
                    code=old_prod.code,
                    defaults={
                        'name': old_prod.name,
                        'description': old_prod.description or '',
                        'unit_price': old_prod.unit_price,
                        'tax_percent': old_prod.tax_percent,
                        'unit_of_measure': old_prod.unit_of_measure or 'N/A',
                        'is_active': old_prod.is_active,
                    }
                )
                if created and not dry_run:
                    stats['products'] += 1
                if i % batch_size == 0:
                    self.stdout.write(f"    Progreso: {i}/{total_products}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    ✗ Error migrando product {old_prod.id}: {e}"))
                stats['errors'] += 1

        # Paso 3: Migrar Invoices y Lines
        self.stdout.write("\n📦 Paso 3/4 — Migrando Invoices y Lines...")
        legacy_invoices = LegacyInvoice.objects.all().select_related('company', 'customer', 'tipo_comprobante')
        if company_id:
            legacy_invoices = legacy_invoices.filter(company_id=company_id)

        total_invoices = legacy_invoices.count()
        self.stdout.write(f"  Encontrados: {total_invoices} facturas")

        for i, old_inv in enumerate(legacy_invoices.iterator(), 1):
            try:
                with transaction.atomic():
                    # Crear Invoice core
                    new_inv = Invoice.objects.create(
                        company=old_inv.company,
                        number=old_inv.number,
                        date=old_inv.date,
                        customer_id=old_inv.customer_id,
                        subtotal=old_inv.subtotal,
                        tax_total=old_inv.tax_total,
                        total=old_inv.total,
                        status='sent' if old_inv.sri_status in ('accepted', 'sent') else 'draft',
                        created_by_id=old_inv.created_by_id,
                        created_at=old_inv.created_at,
                        updated_at=old_inv.updated_at,
                    )
                    stats['invoices'] += 1

                    # Migrar líneas
                    for old_line in LegacyInvoiceLine.objects.filter(invoice_id=old_inv.id):
                        try:
                            product = Product.objects.get(company=old_inv.company, code=old_line.product.code)
                        except Product.DoesNotExist:
                            # Crear product placeholder
                            product = Product.objects.create(
                                company=old_inv.company,
                                code=old_line.product.code or f"LEGACY-{old_line.product.id}",
                                name=old_line.product.name or "Producto legacy",
                                unit_price=old_line.unit_price or 0,
                                tax_percent=12.00,
                                is_active=True,
                            )
                        InvoiceLine.objects.create(
                            invoice=new_inv,
                            product=product,
                            description=old_line.description or '',
                            quantity=old_line.quantity,
                            unit_price=old_line.unit_price,
                            unit_discount=old_line.unit_discount or 0,
                            subtotal=old_line.subtotal,
                            tax_rate=old_line.tax_rate or 12.00,
                            tax_amount=old_line.tax_amount or 0,
                            discount=old_line.discount or 0,
                            total=old_line.total,
                        )
                        stats['lines'] += 1

                    # Crear extensión SRI
                    ext = InvoiceSRIExtension.objects.create(
                        invoice=new_inv,
                        tipo_comprobante=old_inv.tipo_comprobante,
                        ambiente=old_inv.ambiente,
                        access_key=old_inv.access_key,
                        xml_content=old_inv.xml_content or '',
                        xml_original_hash=old_inv.xml_original_hash or '',
                        sri_status=old_inv.sri_status,
                        sri_authorization_date=old_inv.sri_authorization_date,
                        sri_message=old_inv.sri_message or '',
                        sri_xml_autorizado=old_inv.sri_xml_autorizado or '',
                        guia_remision_number=old_inv.guia_remision_number or '',
                    )
                    stats['extensions'] += 1

                if i % batch_size == 0:
                    self.stdout.write(f"    Progreso: {i}/{total_invoices}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    ✗ Error migrando factura {old_inv.id}: {e}"))
                stats['errors'] += 1

        # Resumen
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("✅ MIGRACIÓN COMPLETADA"))
        self.stdout.write("="*60)
        self.stdout.write(f"  Customers migrados:    {stats['customers']}")
        self.stdout.write(f"  Products migrados:     {stats['products']}")
        self.stdout.write(f"  Invoices migrados:     {stats['invoices']}")
        self.stdout.write(f"  InvoiceLines migrados: {stats['lines']}")
        self.stdout.write(f"  Extensiones SRI:       {stats['extensions']}")
        self.stdout.write(f"  Errores:               {stats['errors']}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️  MODO DRY-RUN — Ningún cambio fue guardado"))
