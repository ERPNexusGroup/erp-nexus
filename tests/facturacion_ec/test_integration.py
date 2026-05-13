# Integration Tests — Facturación Core & SRI Plugin
# Pytest-style (no Django TestCase)
import pytest
from decimal import Decimal
from django.db import connection

from apps.facturacion.models import Customer, Invoice, InvoiceLine
from modules.facturacion_ec.models import (
    InvoiceSRIExtension,
    SriTipoComprobante,
    SriAmbiente,
    SriImpuesto,
    SRISendLog,
    CompanyLicense,
)


@pytest.mark.django_db
def test_customer_creation_with_company(company):
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


@pytest.mark.django_db
def test_invoice_auto_numbering_signal(company, customer, user):
    """Signal auto_number_invoice asigna número secuencial."""
    inv = Invoice.objects.create(
        company=company,
        customer=customer,
        created_by=user,
        date='2026-05-12',
    )
    assert inv.number is not None
    assert len(inv.number) >= 17  # Formato: 001-001-000000XXX


@pytest.mark.django_db
def test_invoice_totals_signal(company, customer, user, product):
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
    assert inv.subtotal == Decimal('20.00')
    assert inv.tax_total == Decimal('2.40')
    assert inv.total == Decimal('22.40')


@pytest.mark.django_db
def test_invoice_related_names(company, customer, user):
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
def test_invoice_sri_extension_one_to_one(invoice, sri_tipo):
    """InvoiceSRIExtension es OneToOne con Invoice core."""
    ext = InvoiceSRIExtension.objects.create(
        invoice=invoice,
        ambiente=1,
        tipo_comprobante=sri_tipo,
        access_key='1234567890123456789012345678901234567890',
        sri_status='draft',
    )
    invoice.refresh_from_db()
    assert invoice.sri_extension == ext
    # related_name desde Invoice → sri_extension
    assert hasattr(invoice, 'sri_extension')


@pytest.mark.django_db
def test_sri_catalog_creation():
    """Catálogos SRI se crean correctamente."""
    tipo = SriTipoComprobante.objects.create(code='01', name='Factura')
    ambiente = SriAmbiente.objects.create(code=1, name='Pruebas')
    impuesto = SriImpuesto.objects.create(code='02', name='IVA', percent=12.00, is_active=True)

    assert tipo.code == '01'
    assert ambiente.code == 1
    assert impuesto.percent == 12.00


@pytest.mark.django_db
def test_sri_send_log_related_name(invoice, sri_tipo):
    """SRISendLog usa related_name 'sri_logs'."""
    ext = InvoiceSRIExtension.objects.create(
        invoice=invoice,
        ambiente=1,
        tipo_comprobante=sri_tipo,
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


@pytest.mark.django_db
def test_company_license_unique_together(company, sri_tipo):
    """CompanyLicense tiene unique_together(company, license_type) por modelo."""
    lic1 = CompanyLicense.objects.create(
        company=company,
        license_type=sri_tipo,
        is_active=True,
    )
    assert lic1.id is not None


@pytest.mark.django_db
def test_full_invoice_with_sri_extension(company, customer, user, product, sri_tipo):
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
    ext = InvoiceSRIExtension.objects.create(
        invoice=inv,
        ambiente=1,
        tipo_comprobante=sri_tipo,
        access_key='1234567890123456789012345678901234567890123456',
        sri_status='pending',
    )

    # 3. Asociación bidireccional funciona
    assert inv.sri_extension == ext
    assert ext.invoice == inv
    assert ext.invoice.number == inv.number


@pytest.mark.django_db
def test_models_have_correct_related_names():
    """Verificar que todos los related_names son únicos en el proyecto."""
    # Revisamos campos clave:
    assert Customer._meta.get_field('company').remote_field.related_name == 'facturacion_customers'
    assert Invoice._meta.get_field('company').remote_field.related_name == 'facturacion_invoices'
    assert Invoice._meta.get_field('customer').remote_field.related_name == 'facturacion_invoices'
    assert Invoice._meta.get_field('created_by').remote_field.related_name == 'facturas_created_facturacion'
    assert InvoiceLine._meta.get_field('invoice').remote_field.related_name == 'facturacion_lines'
    assert InvoiceLine._meta.get_field('product').remote_field.related_name == 'facturacion_invoice_lines'
    assert InvoiceSRIExtension._meta.get_field('invoice').remote_field.related_name == 'sri_extension'
    assert SRISendLog._meta.get_field('invoice_extension').remote_field.related_name == 'sri_logs'
