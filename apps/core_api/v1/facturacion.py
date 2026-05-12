# API Core Facturación — Django Ninja
from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from django.db import transaction
from datetime import datetime

from ..models import Customer, Invoice, InvoiceLine

router = Router(tags=["Facturación Core"])


# ========== SCHEMAS ==========

class CustomerIn(Schema):
    identification_type: str = "05"
    identification_number: str
    name: str
    email: str = ""
    phone: str = ""
    address: str = ""
    razon_social: str = ""


class CustomerOut(Schema):
    id: int
    company_id: int
    identification_type: str
    identification_number: str
    name: str
    email: str
    phone: str
    address: str
    razon_social: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class InvoiceLineIn(Schema):
    product_id: int
    description: str = ""
    quantity: float = 1
    unit_price: float
    unit_discount: float = 0


class InvoiceIn(Schema):
    customer_id: int
    lines: list[InvoiceLineIn]
    date: str = None  # ISO date
    notes: str = ""


class InvoiceLineOut(Schema):
    id: int
    product_id: int
    product_code: str
    product_name: str
    description: str
    quantity: float
    unit_price: float
    unit_discount: float
    subtotal: float
    tax_rate: float
    tax_amount: float
    discount: float
    total: float


class InvoiceOut(Schema):
    id: int
    company_id: int
    customer_id: int
    customer_name: str
    number: str
    date: str
    subtotal: float
    tax_total: float
    total: float
    status: str
    notes: str
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineOut] = []


# ========== CUSTOMERS ==========

@router.get("/customers/", response=list[CustomerOut])
def list_customers(request):
    company = request.active_company
    qs = Customer.objects.filter(company=company, is_active=True)
    return [
        {
            "id": c.id,
            "company_id": c.company_id,
            "identification_type": c.identification_type,
            "identification_number": c.identification_number,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "address": c.address,
            "razon_social": c.razon_social,
            "is_active": c.is_active,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in qs
    ]


@router.post("/customers/", response=CustomerOut)
def create_customer(request, data: CustomerIn):
    company = request.active_company
    cust = Customer.objects.create(
        company=company,
        identification_type=data.identification_type,
        identification_number=data.identification_number,
        name=data.name,
        email=data.email,
        phone=data.phone,
        address=data.address,
        razon_social=data.razon_social,
    )
    return cust


@router.get("/customers/{customer_id}/", response=CustomerOut)
def get_customer(request, customer_id: int):
    company = request.active_company
    cust = get_object_or_404(Customer, id=customer_id, company=company)
    return cust


# ========== INVOICES ==========

@router.get("/invoices/", response=list[InvoiceOut])
def list_invoices(request, status: str = None):
    company = request.active_company
    qs = Invoice.objects.filter(company=company).prefetch_related('facturacion_lines__product')
    if status:
        qs = qs.filter(status=status)
    result = []
    for inv in qs:
        result.append({
            "id": inv.id,
            "company_id": inv.company_id,
            "customer_id": inv.customer_id,
            "customer_name": inv.customer.name,
            "number": inv.number,
            "date": inv.date.isoformat(),
            "subtotal": float(inv.subtotal),
            "tax_total": float(inv.tax_total),
            "total": float(inv.total),
            "status": inv.status,
            "notes": inv.notes,
            "created_by_id": inv.created_by_id,
            "created_at": inv.created_at,
            "updated_at": inv.updated_at,
            "lines": [
                {
                    "id": l.id,
                    "product_id": l.product_id,
                    "product_code": l.product.code,
                    "product_name": l.product.name,
                    "description": l.description,
                    "quantity": float(l.quantity),
                    "unit_price": float(l.unit_price),
                    "unit_discount": float(l.unit_discount),
                    "subtotal": float(l.subtotal),
                    "tax_rate": float(l.tax_rate),
                    "tax_amount": float(l.tax_amount),
                    "discount": float(l.discount),
                    "total": float(l.total),
                }
                for l in inv.facturacion_lines.all()
            ],
        })
    return result


@router.post("/invoices/", response=InvoiceOut)
def create_invoice(request, data: InvoiceIn):
    company = request.active_company
    customer = get_object_or_404(Customer, id=data.customer_id, company=company)

    with transaction.atomic():
        invoice = Invoice.objects.create(
            company=company,
            customer=customer,
            date=datetime.strptime(data.date, "%Y-%m-%d").date() if data.date else datetime.now().date(),
            status='draft',
            created_by=request.user,
            notes=data.notes,
        )
        # El signal `invoice_pre_save` asigna número automáticamente

        subtotal = 0
        tax_total = 0

        for line_data in data.lines:
            product = get_object_or_404('inventory.Product', id=line_data.product_id, company=company)
            quantity = line_data.quantity
            unit_price = line_data.unit_price
            unit_discount = line_data.unit_discount

            line_subtotal = quantity * (unit_price - unit_discount)
            line_subtotal = round(line_subtotal, 2)
            tax_rate = 12.00
            tax_amount = round(line_subtotal * (tax_rate / 100), 2)
            line_total = line_subtotal + tax_amount

            InvoiceLine.objects.create(
                invoice=invoice,
                product=product,
                description=line_data.description,
                quantity=quantity,
                unit_price=unit_price,
                unit_discount=unit_discount,
                subtotal=line_subtotal,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                discount=0,
                total=line_total,
            )
            subtotal += line_subtotal
            tax_total += tax_amount

        # Actualizar totals (triggered por signal también)
        invoice.subtotal = subtotal
        invoice.tax_total = tax_total
        invoice.total = subtotal + tax_total
        invoice.save(update_fields=['subtotal', 'tax_total', 'total'])

    # Return serializado
    return {
        "id": invoice.id,
        "company_id": invoice.company_id,
        "customer_id": invoice.customer_id,
        "customer_name": invoice.customer.name,
        "number": invoice.number,
        "date": invoice.date.isoformat(),
        "subtotal": float(invoice.subtotal),
        "tax_total": float(invoice.tax_total),
        "total": float(invoice.total),
        "status": invoice.status,
        "notes": invoice.notes,
        "created_by_id": invoice.created_by_id,
        "created_at": invoice.created_at,
        "updated_at": invoice.updated_at,
        "lines": [],  # simplificado
    }


@router.get("/invoices/{invoice_id}/", response=InvoiceOut)
def get_invoice(request, invoice_id: int):
    company = request.active_company
    inv = get_object_or_404(Invoice, id=invoice_id, company=company)
    inv.lines = inv.facturacion_lines.all()
    return {
        "id": inv.id,
        "company_id": inv.company_id,
        "customer_id": inv.customer_id,
        "customer_name": inv.customer.name,
        "number": inv.number,
        "date": inv.date.isoformat(),
        "subtotal": float(inv.subtotal),
        "tax_total": float(inv.tax_total),
        "total": float(inv.total),
        "status": inv.status,
        "notes": inv.notes,
        "created_by_id": inv.created_by_id,
        "created_at": inv.created_at,
        "updated_at": inv.updated_at,
        "lines": [
            {
                "id": l.id,
                "product_id": l.product_id,
                "product_code": l.product.code,
                "product_name": l.product.name,
                "description": l.description,
                "quantity": float(l.quantity),
                "unit_price": float(l.unit_price),
                "unit_discount": float(l.unit_discount),
                "subtotal": float(l.subtotal),
                "tax_rate": float(l.tax_rate),
                "tax_amount": float(l.tax_amount),
                "discount": float(l.discount),
                "total": float(l.total),
            }
            for l in inv.facturacion_lines.all()
        ],
    }
