# API REST - Facturación Electrónica
from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from datetime import datetime
from decimal import Decimal
from django.utils import timezone

from ..models import Invoice, InvoiceLine, Customer, Product, ElectronicDocument
from ..services import (
    generate_invoice_number,
    generate_access_key,
    send_invoice_to_sri,
    get_next_sequential,
)

router = Router(tags=["Facturación Electrónica"])


# ===================== SCHEMAS =====================

class CustomerIn(Schema):
    identification_type: str
    identification_number: str
    name: str
    email: str = ""
    phone: str = ""
    address: str = ""


class ProductIn(Schema):
    code: str
    name: str
    unit_price: float
    tax_rate: float = 12.0


class InvoiceLineIn(Schema):
    product_code: str
    quantity: float
    unit_price: float
    unit_discount: float = 0


class InvoiceCreate(Schema):
    customer: CustomerIn
    lines: list[InvoiceLineIn]
    date: str = None  # ISO date


class InvoiceOut(Schema):
    id: int
    number: str
    date: str
    customer_name: str
    total: float
    sri_status: str
    ambiente: int


# ===================== HELPERS =====================

def get_company_for_request(request):
    """Obtiene la company activa, con fallback en DEBUG."""
    from django.conf import settings
    company = getattr(request, "active_company", None)
    if not company and settings.DEBUG:
        from apps.core_companies.models import Company
        company = Company.objects.first()
    return company


# ===================== ENDPOINTS =====================
# ORDEN: estáticas primero, dinámicas después

@router.get("/", response=list[InvoiceOut])
def list_invoices(request, status: str = None):
    """Lista facturas de la empresa activa."""
    company = get_company_for_request(request)
    if not company:
        return []
    qs = Invoice.objects.filter(company=company)
    if status:
        qs = qs.filter(sri_status=status)
    return [
        {
            "id": inv.id,
            "number": inv.number,
            "date": inv.date.isoformat(),
            "customer_name": inv.customer.name,
            "total": float(inv.total),
            "sri_status": inv.sri_status,
            "ambiente": inv.ambiente,
        }
        for inv in qs.order_by("-date")[:100]
    ]


@router.post("/")
def create_invoice(request, data: InvoiceCreate):
    """
    Crea factura electrónica y la envía a SRI automaticamente.

    Flujo:
    1. Crear factura en BD (estado pending)
    2. Generar XML + firma digital
    3. Enviar a SRI (async opcional)
    4. Actualizar estado
    """
    company = get_company_for_request(request)
    if not company:
        return {"error": "No company configured"}

    # 1. Crear/obtener cliente
    customer, _ = Customer.objects.get_or_create(
        company=company,
        identification_number=data.customer.identification_number,
        defaults={
            "identification_type": data.customer.identification_type,
            "name": data.customer.name,
            "email": data.customer.email,
            "phone": data.customer.phone,
            "address": data.customer.address,
        },
    )

    # 2. Calcular número único
    seq = get_next_sequential(company, "001", "001")
    number = generate_invoice_number("001", "001", seq)

    # 3. Crear factura
    from django.contrib.auth import get_user_model
    User = get_user_model()
    # En desarrollo, usar primer usuario si no hay autenticación
    creator = request.user if request.user.is_authenticated else User.objects.first()

    invoice = Invoice.objects.create(
        company=company,
        number=number,
        date=datetime.strptime(data.date, "%Y-%m-%d").date() if data.date else timezone.now().date(),
        customer=customer,
        ambiente=1,  # default pruebas
        created_by=creator,
    )

    # 4. Crear líneas
    subtotal = Decimal('0.00')
    for line_data in data.lines:
        product = Product.objects.get(company=company, code=line_data.product_code)
        quantity = Decimal(str(line_data.quantity))
        unit_price = Decimal(str(line_data.unit_price))

        line_subtotal = (quantity * unit_price).quantize(Decimal('0.01'))
        tax_amount = (line_subtotal * Decimal('0.12')).quantize(Decimal('0.01'))

        InvoiceLine.objects.create(
            invoice=invoice,
            product=product,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=line_subtotal,
            tax_rate=Decimal('12.00'),
            tax_amount=tax_amount,
            total=line_subtotal + tax_amount,
        )
        subtotal += line_subtotal

    # 5. Calcular totales
    invoice.subtotal = subtotal
    invoice.tax_total = subtotal * Decimal('0.12')
    invoice.total = subtotal + invoice.tax_total
    invoice.save()

    # 6. Generar clave acceso
    invoice.access_key = generate_access_key(
        ruc=company.ruc,
        ambiente=invoice.ambiente,
        establishment_code="001",
        emission_point="001",
        sequential=str(seq),
        date=invoice.date,
    )
    invoice.save(update_fields=["access_key"])

    # 7. Enviar a SRI (async ideal, aquí sync para demo)
    try:
        result = send_invoice_to_sri(invoice.id)
        if result.get('success'):
            invoice.sri_status = 'accepted' if result.get('estado') == 'APROBADA' else 'sent'
            invoice.sri_message = result.get('mensaje', '')
            invoice.save(update_fields=["sri_status", "sri_message"])
    except Exception as e:
        # No fallar creación, se reintentará después
        pass

    return {
        "id": invoice.id,
        "number": invoice.number,
        "access_key": invoice.access_key,
        "total": float(invoice.total),
        "sri_status": invoice.sri_status,
    }


@router.get("/customers/")
def list_customers(request, q: str = None):
    """Busca clientes (para autocomplete)."""
    company = get_company_for_request(request)
    if not company:
        return []
    qs = Customer.objects.filter(company=company, is_active=True)
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(identification_number__icontains=q)
    return [{"id": c.id, "name": c.name, "ruc": c.identification_number} for c in qs[:20]]


@router.get("/products/")
def list_products(request, q: str = None):
    """Busca productos."""
    company = get_company_for_request(request)
    if not company:
        return []
    qs = Product.objects.filter(company=company, is_active=True)
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(code__icontains=q)
    return [
        {"id": p.id, "code": p.code, "name": p.name, "price": float(p.unit_price)}
        for p in qs[:20]
    ]


# Rutas dinámicas (después de estáticas)
@router.get("/{invoice_id}/")
def get_invoice(request, invoice_id: int):
    """Obtiene detalle de factura."""
    from django.shortcuts import get_object_or_404
    company = get_company_for_request(request)
    invoice = get_object_or_404(Invoice, id=invoice_id, company=company)
    return {
        "id": invoice.id,
        "number": invoice.number,
        "date": invoice.date.isoformat(),
        "customer": {
            "name": invoice.customer.name,
            "ruc": invoice.customer.identification_number,
        },
        "subtotal": float(invoice.subtotal),
        "tax_total": float(invoice.tax_total),
        "total": float(invoice.total),
        "sri_status": invoice.sri_status,
        "sri_message": invoice.sri_message,
    }


@router.get("/{invoice_id}/xml")
def download_xml(request, invoice_id: int):
    """Descarga XML firmado."""
    from django.shortcuts import get_object_or_404
    company = get_company_for_request(request)
    invoice = get_object_or_404(Invoice, id=invoice_id, company=company)
    if not invoice.xml_content:
        return {"error": "XML no generado aún"}
    return HttpResponse(
        invoice.xml_content,
        content_type='application/xml',
        headers={'Content-Disposition': f'attachment; filename="{invoice.number}.xml"'}
    )


@router.post("/{invoice_id}/resend")
def resend_invoice(request, invoice_id: int):
    """Reenvía factura rechazada/corrige."""
    from django.shortcuts import get_object_or_404
    company = get_company_for_request(request)
    invoice = get_object_or_404(Invoice, id=invoice_id, company=company)
    if invoice.sri_status not in ('rejected', 'draft'):
        return {"error": "Solo se pueden reenviar facturas rechazadas o en borrador"}

    result = send_invoice_to_sri(invoice.id)
    if result.get('success'):
        invoice.sri_status = 'accepted' if result.get('estado') == 'APROBADA' else 'sent'
        invoice.save()
        return {"success": True, "estado": invoice.sri_status}
    return {"success": False, "error": result.get('mensaje')}
