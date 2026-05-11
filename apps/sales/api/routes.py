"""
API endpoints para el módulo sales (ventas).
Router de Django Ninja expuesto en /api/v1/sales/
"""
from ninja import Router
from django.db import transaction
from django.utils import timezone

from ..models import Quote, QuoteLine, Order, OrderLine

router = Router(tags=["Ventas"])


# === Quotes ===

@router.get("/quotes/")
def list_quotes(request):
    """Lista todas las cotizaciones."""
    quotes = Quote.objects.all()
    return [
        {
            "id": q.id,
            "quote_number": q.quote_number,
            "customer_id": q.customer_id,
            "customer_name": q.customer.name,
            "issue_date": q.issue_date,
            "expiry_date": q.expiry_date,
            "status": q.status,
            "total": float(q.total),
        }
        for q in quotes
    ]


@router.get("/quotes/{quote_id}/")
def get_quote(request, quote_id: int):
    """Obtiene una cotización con sus líneas."""
    quote = Quote.objects.get(id=quote_id)
    lines = [
        {
            "product_id": l.product_id,
            "product_sku": l.product.sku,
            "product_name": l.product.name,
            "quantity": float(l.quantity),
            "unit_price": float(l.unit_price),
            "subtotal": float(l.subtotal),
        }
        for l in quote.lines.all()
    ]
    return {
        "id": quote.id,
        "quote_number": quote.quote_number,
        "customer_id": quote.customer_id,
        "issue_date": quote.issue_date,
        "expiry_date": quote.expiry_date,
        "status": quote.status,
        "subtotal": float(quote.subtotal),
        "tax": float(quote.tax),
        "total": float(quote.total),
        "notes": quote.notes,
        "lines": lines,
    }


@router.post("/quotes/")
def create_quote(request):
    """Crea una cotización con líneas."""
    data = request.json
    with transaction.atomic():
        quote = Quote.objects.create(
            quote_number=data["quote_number"],
            customer_id=data["customer_id"],
            issue_date=data.get("issue_date", timezone.now().date()),
            expiry_date=data["expiry_date"],
            status="draft",
            notes=data.get("notes", ""),
        )
        for line in data.get("lines", []):
            product_id = line["product_id"]
            quantity = line["quantity"]
            unit_price = line["unit_price"]
            subtotal = quantity * unit_price
            QuoteLine.objects.create(
                quote=quote,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
            )
        # recalcular totales
        quote.recalculate_totals()
        quote.save()
    return {"id": quote.id, "quote_number": quote.quote_number}


@router.post("/quotes/{quote_id}/accept/")
def accept_quote(request, quote_id: int):
    """Marcar cotización como aceptada."""
    quote = Quote.objects.get(id=quote_id)
    quote.status = "accepted"
    quote.save()
    return {"status": "accepted", "quote_id": quote.id}


@router.post("/quotes/{quote_id}/reject/")
def reject_quote(request, quote_id: int):
    """Marcar cotización como rechazada."""
    quote = Quote.objects.get(id=quote_id)
    quote.status = "rejected"
    quote.save()
    return {"status": "rejected", "quote_id": quote.id}


# === Orders ===

@router.get("/orders/")
def list_orders(request):
    """Lista todas las órdenes."""
    orders = Order.objects.all()
    return [
        {
            "id": o.id,
            "order_number": o.order_number,
            "customer_id": o.customer_id,
            "issue_date": o.issue_date,
            "delivery_date": o.delivery_date,
            "status": o.status,
            "total": float(o.total),
        }
        for o in orders
    ]


@router.post("/orders/")
def create_order(request):
    """Crea una orden y opcionalmente reserva stock."""
    data = request.json
    with transaction.atomic():
        order = Order.objects.create(
            order_number=data["order_number"],
            customer_id=data["customer_id"],
            issue_date=data.get("issue_date", timezone.now().date()),
            delivery_date=data["delivery_date"],
            status="pending",
            notes=data.get("notes", ""),
        )
        for line in data.get("lines", []):
            product_id = line["product_id"]
            quantity = line["quantity"]
            unit_price = line["unit_price"]
            subtotal = quantity * unit_price
            OrderLine.objects.create(
                order=order,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
            )
        order.recalculate_totals()
        order.save()
    return {"id": order.id, "order_number": order.order_number}


@router.post("/orders/{order_id}/confirm/")
def confirm_order(request, order_id: int):
    """Confirma una orden y reserva stock si hay disponibilidad."""
    order = Order.objects.get(id=order_id)
    if order.status != "pending":
        return {"error": "Solo se pueden confirmar órdenes pendientes"}, 400

    # Verificar stock en inventory
    from apps.inventory.models import Product
    errors = []
    for line in order.lines.all():
        product = line.product
        # En producción: verificar que stock >= quantity
        if product.stock_quantity < line.quantity:
            errors.append(f"Stock insuficiente para {product.sku}")

    if errors:
        return {"error": "Stock insuficiente", "details": errors}, 400

    order.status = "confirmed"
    order.save()
    return {"status": "confirmed", "order_id": order.id}


@router.post("/orders/{order_id}/invoice/")
def order_to_invoice(request, order_id: int):
    """Convierte una orden confirmada en factura."""
    order = Order.objects.select_related("customer").get(id=order_id)
    if order.status not in ["confirmed", "completed"]:
        return {"error": "La orden debe estar confirmada"}, 400

    # Generar factura via facturacion module (REST call interno)
    from apps.facturacion.services import create_invoice_from_order
    invoice = create_invoice_from_order(order)

    return {
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "order_id": order.id,
    }
