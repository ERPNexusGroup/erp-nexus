"""
API REST — Core de Facturación (agnóstico de SRI)
Endpoints locales para Customer, Invoice, Quote.
"""
from ninja import Router, Schema, File
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
from datetime import date

from ..models import Customer, Product, Invoice, InvoiceLine, Quote, QuoteLine
from core_companies.models import Company


# ─────────────────── Schemas ────────────────────

class CustomerIn(Schema):
    identification_type: str
    identification_number: str
    name: str
    email: str = ""
    phone: str = ""
    address: str = ""
    razon_social: str = ""


class CustomerOut(Schema):
    id: int
    identification_type: str
    identification_number: str
    name: str
    email: str
    phone: str
    address: str
    razon_social: str
    is_active: bool


class ProductIn(Schema):
    code: str
    name: str
    description: str = ""
    unit_price: float
    tax_percent: float = 12.0
    unit_of_measure: str = "N/A"


class ProductOut(Schema):
    id: int
    code: str
    name: str
    description: str
    unit_price: float
    tax_percent: float
    unit_of_measure: str
    is_active: bool


class InvoiceLineIn(Schema):
    product_code: str
    description: str = ""
    quantity: float = 1.0
    unit_price: float
    unit_discount: float = 0.0
    tax_rate: float = 12.0


class InvoiceIn(Schema):
    customer_identification_number: str
    lines: list[InvoiceLineIn]
    notes: str = ""
    due_date: str = None  # ISO date YYYY-MM-DD


class InvoiceOut(Schema):
    id: int
    number: str
    date: str
    customer: CustomerOut
    subtotal: float
    tax_total: float
    total: float
    status: str
    created_at: str


class QuoteIn(Schema):
    customer_identification_number: str
    lines: list[InvoiceLineIn]
    issue_date: str = None
    expiry_date: str = None
    notes: str = ""


class QuoteOut(Schema):
    id: int
    quote_number: str
    issue_date: str
    expiry_date: str = None
    customer: CustomerOut
    subtotal: float
    tax_total: float
    total: float
    status: str


class ConvertQuoteIn(Schema):
    pass  # Sin campos, solo POST vacío


router = Router(tags=["Facturación Core"])


# ─────────────────── Customer ────────────────────

@router.get("/customers/", response=list[CustomerOut])
def list_customers(request, search: str = None):
    company = request.active_company
    qs = Customer.objects.filter(company=company, is_active=True)
    if search:
        qs = qs.filter(name__icontains=search) | qs.filter(identification_number__icontains=search)
    return [
        {
            "id": c.id,
            "identification_type": c.identification_type,
            "identification_number": c.identification_number,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "address": c.address,
            "razon_social": c.razon_social,
            "is_active": c.is_active,
        }
        for c in qs.order_by("name")[:100]
    ]


@router.post("/customers/", response=CustomerOut)
def create_customer(request, data: CustomerIn):
    company = request.active_company
    cust = Customer.objects.create(company=company, **data.dict())
    return {
        "id": cust.id,
        "identification_type": cust.identification_type,
        "identification_number": cust.identification_number,
        "name": cust.name,
        "email": cust.email,
        "phone": cust.phone,
        "address": cust.address,
        "razon_social": cust.razon_social,
        "is_active": cust.is_active,
    }


# ─────────────────── Products ────────────────────

@router.get("/products/", response=list[ProductOut])
def list_products(request, search: str = None):
    company = request.active_company
    qs = Product.objects.filter(company=company, is_active=True)
    if search:
        qs = qs.filter(name__icontains=search) | qs.filter(code__icontains=search)
    return [
        {
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "description": p.description,
            "unit_price": float(p.unit_price),
            "tax_percent": float(p.tax_percent),
            "unit_of_measure": p.unit_of_measure,
            "is_active": p.is_active,
        }
        for p in qs.order_by("code")[:100]
    ]


@router.post("/products/", response=ProductOut)
def create_product(request, data: ProductIn):
    company = request.active_company
    product = Product.objects.create(company=company, **data.dict())
    return {
        "id": product.id,
        "code": product.code,
        "name": product.name,
        "description": product.description,
        "unit_price": float(product.unit_price),
        "tax_percent": float(product.tax_percent),
        "unit_of_measure": product.unit_of_measure,
        "is_active": product.is_active,
    }


# ─────────────────── Invoices ────────────────────

@router.get("/invoices/", response=list[InvoiceOut])
def list_invoices(request, status: str = None):
    company = request.active_company
    qs = Invoice.objects.filter(company=company)
    if status:
        qs = qs.filter(status=status)
    return [
        {
            "id": inv.id,
            "number": inv.number,
            "date": inv.date.isoformat(),
            "customer": {
                "id": inv.customer.id,
                "name": inv.customer.name,
                "identification_number": inv.customer.identification_number,
            },
            "subtotal": float(inv.subtotal),
            "tax_total": float(inv.tax_total),
            "total": float(inv.total),
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        }
        for inv in qs.order_by("-date")[:100]
    ]


@router.post("/invoices/", response=InvoiceOut)
def create_invoice(request, data: InvoiceIn):
    """
    Crea factura en estado draft.

    El envío a SRI (si aplica) lo maneja el plugin modules.facturacion_ec
    vía signal o endpoint dedicado.
    """
    company = request.active_company
    user = request.user

    with transaction.atomic():
        # Obtener o crear customer
        customer, _ = Customer.objects.get_or_create(
            company=company,
            identification_number=data.customer_identification_number,
            defaults={
                "identification_type": "07",  # Consumidor final por defecto
                "name": data.customer_identification_number,
                "is_active": True,
            },
        )

        # Crear factura
        invoice = Invoice.objects.create(
            company=company,
            customer=customer,
            date=date.today(),
            status="draft",
            created_by=user,
            notes=data.notes,
        )
        # Number assignment via signal (pre_save)

        # Crear líneas
        for line_data in data.lines:
            product = get_object_or_404(Product, company=company, code=line_data.product_code)
            quantity = Decimal(str(line_data.quantity))
            unit_price = Decimal(str(line_data.unit_price))
            unit_discount = Decimal(str(line_data.unit_discount))
            tax_rate = Decimal(str(line_data.tax_rate))

            subtotal = quantity * (unit_price - unit_discount)
            tax_amount = subtotal * (tax_rate / Decimal('100'))
            total = subtotal + tax_amount

            InvoiceLine.objects.create(
                invoice=invoice,
                product=product,
                description=line_data.description or product.name,
                quantity=quantity,
                unit_price=unit_price,
                unit_discount=unit_discount,
                subtotal=subtotal.quantize(Decimal('0.01')),
                tax_rate=tax_rate,
                tax_amount=tax_amount.quantize(Decimal('0.01')),
                discount=(unit_discount * quantity).quantize(Decimal('0.01')),
                total=total.quantize(Decimal('0.01')),
            )

        # Recalcular totales
        lines = invoice.lines.all()
        invoice.subtotal = sum(l.subtotal for l in lines)
        invoice.tax_total = sum(l.tax_amount for l in lines)
        invoice.total = invoice.subtotal + invoice.tax_total
        invoice.save(update_fields=["subtotal", "tax_total", "total"])

    return {
        "id": invoice.id,
        "number": invoice.number,
        "date": invoice.date.isoformat(),
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "identification_number": customer.identification_number,
        },
        "subtotal": float(invoice.subtotal),
        "tax_total": float(invoice.tax_total),
        "total": float(invoice.total),
        "status": invoice.status,
        "created_at": invoice.created_at.isoformat(),
    }


@router.get("/invoices/{invoice_id}/", response=InvoiceOut)
def get_invoice(request, invoice_id: int):
    company = request.active_company
    invoice = get_object_or_404(Invoice, company=company, id=invoice_id)
    return {
        "id": invoice.id,
        "number": invoice.number,
        "date": invoice.date.isoformat(),
        "customer": {
            "id": invoice.customer.id,
            "name": invoice.customer.name,
            "identification_number": invoice.customer.identification_number,
        },
        "subtotal": float(invoice.subtotal),
        "tax_total": float(invoice.tax_total),
        "total": float(invoice.total),
        "status": invoice.status,
        "created_at": invoice.created_at.isoformat(),
    }


# ─────────────────── Quotes ────────────────────

@router.get("/quotes/", response=list[QuoteOut])
def list_quotes(request, status: str = None):
    company = request.active_company
    qs = Quote.objects.filter(company=company)
    if status:
        qs = qs.filter(status=status)
    return [
        {
            "id": q.id,
            "quote_number": q.quote_number,
            "issue_date": q.issue_date.isoformat(),
            "expiry_date": q.expiry_date.isoformat() if q.expiry_date else None,
            "customer": {
                "id": q.customer.id,
                "name": q.customer.name,
                "identification_number": q.customer.identification_number,
            },
            "subtotal": float(q.subtotal),
            "tax_total": float(q.tax_total),
            "total": float(q.total),
            "status": q.status,
        }
        for q in qs.order_by("-issue_date")[:100]
    ]


@router.post("/quotes/", response=QuoteOut)
def create_quote(request, data: QuoteIn):
    company = request.active_company
    user = request.user
    issue_date = date.today()
    if data.issue_date:
        issue_date = date.fromisoformat(data.issue_date)

    with transaction.atomic():
        customer, _ = Customer.objects.get_or_create(
            company=company,
            identification_number=data.customer_identification_number,
            defaults={
                "identification_type": "07",
                "name": data.customer_identification_number,
                "is_active": True,
            },
        )

        quote = Quote.objects.create(
            company=company,
            customer=customer,
            issue_date=issue_date,
            expiry_date=date.fromisoformat(data.expiry_date) if data.expiry_date else None,
            status="draft",
            created_by=user,
        )

        for line_data in data.lines:
            product = get_object_or_404(Product, company=company, code=line_data.product_code)
            quantity = Decimal(str(line_data.quantity))
            unit_price = Decimal(str(line_data.unit_price))
            unit_discount = Decimal(str(line_data.unit_discount))
            tax_rate = Decimal(str(line_data.tax_rate))

            subtotal = quantity * (unit_price - unit_discount)
            tax_amount = subtotal * (tax_rate / Decimal('100'))
            total = subtotal + tax_amount

            QuoteLine.objects.create(
                quote=quote,
                product=product,
                description=line_data.description or product.name,
                quantity=quantity,
                unit_price=unit_price,
                unit_discount=unit_discount,
                subtotal=subtotal.quantize(Decimal('0.01')),
                tax_rate=tax_rate,
                tax_amount=tax_amount.quantize(Decimal('0.01')),
                discount=(unit_discount * quantity).quantize(Decimal('0.01')),
                total=total.quantize(Decimal('0.01')),
            )

        lines = quote.lines.all()
        quote.subtotal = sum(l.subtotal for l in lines)
        quote.tax_total = sum(l.tax_amount for l in lines)
        quote.total = quote.subtotal + quote.tax_total
        quote.save(update_fields=["subtotal", "tax_total", "total"])

    return {
        "id": quote.id,
        "quote_number": quote.quote_number,
        "issue_date": quote.issue_date.isoformat(),
        "expiry_date": quote.expiry_date.isoformat() if quote.expiry_date else None,
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "identification_number": customer.identification_number,
        },
        "subtotal": float(quote.subtotal),
        "tax_total": float(quote.tax_total),
        "total": float(quote.total),
        "status": quote.status,
    }


@router.post("/quotes/{quote_id}/convert/")
def convert_quote_to_invoice(request, quote_id: int):
    """
    Convierte una cotización aprobada en factura.
    """
    company = request.active_company
    user = request.user
    quote = get_object_or_404(Quote, company=company, id=quote_id)

    if quote.status != "approved":
        return {"error": "Solo cotizaciones aprobadas pueden convertirse"}

    invoice = quote.convert_to_invoice(user=user)
    return {
        "invoice_id": invoice.id,
        "invoice_number": invoice.number,
        "message": "Factura creada exitosamente",
    }
