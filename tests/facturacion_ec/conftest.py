# Fixtures para tests de facturación_ec
import pytest
from django.contrib.auth import get_user_model

from apps.core_companies.models import Company
from apps.facturacion.models import Customer, Invoice
from apps.inventory.models import Category, Product
from modules.facturacion_ec.models import (
    SriTipoComprobante,
    SriAmbiente,
    SriImpuesto,
)


@pytest.fixture
def user(db):
    """Usuario Django para created_by en Invoice."""
    User = get_user_model()
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass'
    )


@pytest.fixture
def company(db):
    """Compañía de prueba."""
    return Company.objects.create(
        name='Test Company',
        ruc='1792369238001',
        email='test@example.com',
    )


@pytest.fixture
def customer(company, db):
    """Cliente asociado a compañía."""
    return Customer.objects.create(
        company=company,
        identification_type='04',
        identification_number='1792369238001',
        name='Cliente Test',
        razon_social='CLIENTE TEST CIA. LTDA.',
    )


@pytest.fixture
def product(company, db):
    """Producto en inventory."""
    # Crear categoría primero (Product requiere Category)
    cat = Category.objects.create(
        name='Categoría Test',
        code='TEST',
        is_active=True,
    )
    return Product.objects.create(
        sku='P001',
        name='Producto Test',
        description='Producto de prueba',
        category=cat,
        unit_price=100.00,
        stock_quantity=10,
        min_stock=2,
        is_active=True,
    )


@pytest.fixture
def invoice(company, customer, user, db):
    """Factura en estado draft."""
    inv = Invoice.objects.create(
        company=company,
        customer=customer,
        created_by=user,
        date='2026-05-12',
        status='draft',
    )
    # Signal auto_number_invoice asigna número
    inv.refresh_from_db()
    return inv


@pytest.fixture
def invoice_with_lines(invoice, product, db):
    """Factura con una línea calculada."""
    from apps.facturacion.models import InvoiceLine
    InvoiceLine.objects.create(
        invoice=invoice,
        product=product,
        quantity=2,
        unit_price=50.00,
        unit_discount=0,
        subtotal=100.00,
        tax_rate=12.00,
        tax_amount=12.00,
        discount=0,
        total=112.00,
    )
    invoice.refresh_from_db()
    return invoice


@pytest.fixture
def sri_tipo(db):
    """Tipo comprobante SRI por defecto."""
    return SriTipoComprobante.objects.create(
        code='01',
        name='Factura',
        description='Factura de venta'
    )


@pytest.fixture
def sri_ambiente(db):
    """Ambiente SRI (1=Pruebas)."""
    return SriAmbiente.objects.create(code=1, name='Pruebas')


@pytest.fixture
def sri_impuesto(db):
    """Impuesto SRI (IVA 12%)."""
    return SriImpuesto.objects.create(
        code='02',
        name='IVA',
        percent=12.00,
        is_active=True,
    )


@pytest.fixture
def sri_extension(invoice, sri_tipo, db):
    """Extensión SRI vinculada a factura."""
    return InvoiceSRIExtension.objects.create(
        invoice=invoice,
        ambiente=1,
        tipo_comprobante=sri_tipo,
        access_key='1234567890123456789012345678901234567890',
        sri_status='draft',
    )
