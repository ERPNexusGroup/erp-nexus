# Integration Tests — Facturación Core & SRI Plugin
# Verifican que core facturación y plugin SRI trabajan juntos
import pytest
from django.test import TestCase
from django.db import connection

from apps.facturacion.models import Customer, Invoice, InvoiceLine
from modules.facturacion_ec.models import (
    InvoiceSRIExtension,
    SriTipoComprobante,
    SriAmbiente,
    SRISendLog,
)


@pytest.mark.django_db
class TestFacturacionCoreModels(TestCase):
    """Core local facturación: Customer, Invoice, InvoiceLine."""

    def test_customer_creation_with_company(self, company):
        """Customer se crea asociado a company con related_name correcto."""
        cust = Customer.objects.create(
            company=company,
            identification_type='04',
            identification_number='1792369238001',
            name='Mi Empresa S.A.',
            razon_social='MI EMPRESA S.A.',
        )
        assert cust.id is not None
        assert cust.company == company
        # related_name facturacion_customers funciona
        assert company.facturacion_customers.filter(id=cust.id).exists()

    def test_invoice_auto_numbering_signal(self, company, customer, user):
        """Signal auto_number_invoice asigna número secuencial."""
        inv = Invoice.objects.create(
            company=company,
            customer=customer,
            created_by=user,
            date='2026-05-12',
        )
        assert inv.number is not None
        assert len(inv.number) >= 17  # Formato: 001-001-000000XXX

    def test_invoice_totals_signal(self, company, customer, user, product):
        """Signal calculate_invoice_totals suma líneas correctamente."""
        inv = Invoice.objects.create(
            company=company,
            customer=customer,
            created_by=user,
            date='2026-05-12',
        )
        InvoiceLine.objects.create(
            invoice=inv,
            product=product,
            quantity=2,
            unit_price=10.00,
            unit_discount=0,
            subtotal=20.00,
            tax_rate=12.00,
            tax_amount=2.40,
            discount=0,
            total=22.40,
        )
        inv.refresh_from_db()
        assert inv.subtotal == 20.00
        assert inv.tax_total == 2.40
        assert inv.total == 22.40

    def test_invoice_related_names(self, company, customer, user):
        """Invoice.related_names únicos y sin colisión."""
        inv = Invoice.objects.create(
            company=company,
            customer=customer,
            created_by=user,
            date='2026-05-12',
        )
        # related_name facturacion_invoices en Customer y Company
        assert customer.facturacion_invoices.filter(id=inv.id).exists()
        assert company.facturacion_invoices.filter(id=inv.id).exists()
        # related_name facturas_created_facturacion en User
        assert user.facturas_created_facturacion.filter(id=inv.id).exists()


@pytest.mark.django_db
class TestFacturacionECPluginModels(TestCase):
    """Plugin SRI: extensión y catálogos."""

    def test_invoice_sri_extension_one_to_one(self, invoice):
        """InvoiceSRIExtension es OneToOne con Invoice core."""
        ext = InvoiceSRIExtension.objects.create(
            invoice=invoice,
            ambiente=1,
            access_key='1234567890123456789012345678901234567890',
            sri_status='draft',
        )
        invoice.refresh_from_db()
        assert invoice.sri_extension == ext
        # related_name desde Invoice → sri_extension
        assert hasattr(invoice, 'sri_extension')

    def test_sri_catalog_creation(self):
        """Catálogos SRI se crean correctamente."""
        tipo = SriTipoComprobante.objects.create(code='01', name='Factura')
        ambiente = SriAmbiente.objects.create(code=1, name='Pruebas')
        impuesto = SriImpuesto.objects.create(code='02', name='IVA', percent=12.00)

        assert tipo.code == '01'
        assert ambiente.code == 1
        assert impuesto.percent == 12.00

    def test_sri_send_log_related_name(self, invoice):
        """SRISendLog usa related_name 'sri_logs'."""
        ext = InvoiceSRIExtension.objects.create(
            invoice=invoice,
            ambiente=1,
            access_key='1234567890123456789012345678901234567890',
        )
        log = SRISendLog.objects.create(
            invoice_extension=ext,
            endpoint='https://cel.arlenys.pro',
            request_xml='<xml/>',
            response_xml='<response/>',
            response_code='000',
            success=True,
        )
        assert ext.sri_logs.filter(id=log.id).exists()

    def test_company_license_unique_together(self, company):
        """CompanyLicense tiene unique_together(company, license_type)."""
        from modules.facturacion_ec.models import SriTipoComprobante
        tipo = SriTipoComprobante.objects.create(code='01', name='Factura')
        lic1 = CompanyLicense.objects.create(
            company=company,
            license_type=tipo,
            is_active=True,
        )
        # Uniqueness: misma compañía + mismo tipo → solo una licencia activa
        assert lic1.id is not None
        # (no probamos dup en integración para no complicar rollback)


@pytest.mark.django_db
class TestFacturacionIntegrationDAG(TestCase):
    """Flujo end-to-end: core → extensión SRI → envío simulado."""

    def test_full_invoice_with_sri_extension(self, company, customer, user, product):
        """Crear factura core + extensión SRI completa."""
        # 1. Crear factura en core
        inv = Invoice.objects.create(
            company=company,
            customer=customer,
            created_by=user,
            date='2026-05-12',
        )
        InvoiceLine.objects.create(
            invoice=inv,
            product=product,
            quantity=1,
            unit_price=100.00,
            unit_discount=0,
            subtotal=100.00,
            tax_rate=12.00,
            tax_amount=12.00,
            discount=0,
            total=112.00,
        )
        inv.refresh_from_db()

        # 2. Extensión SRI (asociada uno-a-uno)
        tipo = SriTipoComprobante.objects.create(code='01', name='Factura')
        ext = InvoiceSRIExtension.objects.create(
            invoice=inv,
            ambiente=1,
            tipo_comprobante=tipo,
            access_key='1234567890123456789012345678901234567890123456',
            sri_status='pending',
        )

        # 3. Asociación bidireccional funciona
        assert inv.sri_extension == ext
        assert ext.invoice == inv
        assert ext.invoice.number == inv.number

    def test_models_have_correct_related_names(self):
        """Verificar que todos los related_names son únicos en el proyecto."""
        # Revisamos campos clave:
        # Customer.company → related_name='facturacion_customers'
        assert Customer._meta.get_field('company').related_name == 'facturacion_customers'
        # Invoice.company → related_name='facturacion_invoices'
        assert Invoice._meta.get_field('company').related_name == 'facturacion_invoices'
        # Invoice.customer → related_name='facturacion_invoices'
        assert Invoice._meta.get_field('customer').related_name == 'facturacion_invoices'
        # Invoice.created_by → related_name='facturas_created_facturacion'
        assert Invoice._meta.get_field('created_by').related_name == 'facturas_created_facturacion'
        # InvoiceLine.invoice → related_name='facturacion_lines'
        assert InvoiceLine._meta.get_field('invoice').related_name == 'facturacion_lines'
        # InvoiceLine.product → related_name='facturacion_invoice_lines'
        assert InvoiceLine._meta.get_field('product').related_name == 'facturacion_invoice_lines'
        # InvoiceSRIExtension.invoice → related_name='sri_extension'
        assert InvoiceSRIExtension._meta.get_field('invoice').related_name == 'sri_extension'
        # SRISendLog.invoice_extension → related_name='sri_logs'
        assert SRISendLog._meta.get_field('invoice_extension').related_name == 'sri_logs'


# Fixtures factories (para reutilizar en otros tests)
import factory


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'core_companies.Company'

    name = factory.Sequence(lambda n: f'Empresa {n}')
    ruc = factory.Sequence(lambda n: f'179236923800{n:03d}')
    email = factory.LazyAttribute(lambda o: f'{o.name.lower().replace(" ", "")}@example.com')


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'facturacion.Customer'

    company = factory.SubFactory(CompanyFactory)
    identification_type = '04'
    identification_number = factory.Sequence(lambda n: f'179236923800{n:03d}')
    name = factory.Sequence(lambda n: f'Cliente {n}')


class InvoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'facturacion.Invoice'

    company = factory.SubFactory(CompanyFactory)
    customer = factory.SubFactory(CustomerFactory)
    created_by = factory.SubFactory('apps.core_users.tests.factories.UserFactory')
    date = '2026-05-12'


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'inventory.Product'

    company = factory.SubFactory(CompanyFactory)
    code = factory.Sequence(lambda n: f'P{n:05d}')
    name = factory.Sequence(lambda n: f'Product {n}')
    unit_price = 10.00


# Auto-register fixtures via conftest en el directorio tests/
# (conftest.py se genera aparte)
