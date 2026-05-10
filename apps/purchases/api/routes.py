"""
API endpoints para el módulo purchases (compras).
"""
from ninja import Router
from django.db import transaction
from django.utils import timezone

from ..models import Supplier, PurchaseOrder, PurchaseOrderLine

router = Router(tags=["Compras"])


# === Suppliers ===

@router.get("/suppliers/")
def list_suppliers(request):
    suppliers = Supplier.objects.all()
    return [
        {
            "id": s.id,
            "vendor_number": s.vendor_number,
            "customer_name": s.customer.name,
            "rating": s.rating,
            "is_active": s.is_active,
        }
        for s in suppliers
    ]


# === Purchase Orders ===

@router.get("/purchase-orders/")
def list_pos(request):
    """Lista órdenes de compra."""
    pos = PurchaseOrder.objects.all()
    return [
        {
            "id": po.id,
            "po_number": po.po_number,
            "supplier_id": po.supplier_id,
            "order_date": po.order_date,
            "expected_delivery": po.expected_delivery,
            "status": po.status,
            "total": float(po.total),
        }
        for po in pos
    ]


@router.post("/purchase-orders/")
def create_po(request):
    """Crea una orden de compra."""
    data = request.json
    with transaction.atomic():
        po = PurchaseOrder.objects.create(
            po_number=data["po_number"],
            supplier_id=data["supplier_id"],
            order_date=data.get("order_date", timezone.now().date()),
            expected_delivery=data["expected_delivery"],
            status="draft",
            notes=data.get("notes", ""),
        )
        for line in data.get("lines", []):
            product_id = line["product_id"]
            quantity = line["quantity_ordered"]
            unit_price = line["unit_price"]
            PurchaseOrderLine.objects.create(
                po=po,
                product_id=product_id,
                quantity_ordered=quantity,
                quantity_received=0,
                unit_price=unit_price,
            )
        po.recalculate_totals()
        po.save()
    return {"id": po.id, "po_number": po.po_number}


@router.post("/purchase-orders/{po_id}/send/")
def send_po(request, po_id: int):
    """Marca PO como enviada al proveedor."""
    po = PurchaseOrder.objects.get(id=po_id)
    po.status = "sent"
    po.save()
    return {"status": "sent", "po_id": po.id}


@router.post("/purchase-orders/{po_id}/receive/")
def receive_po(request, po_id: int):
    """Registra recepción de mercancía (stock update en inventory)."""
    data = request.json  # { "lines": [{ "line_id": X, "quantity_received": Y }] }
    po = PurchaseOrder.objects.get(id=po_id)

    from apps.inventory.models import Product, StockMovement

    with transaction.atomic():
        for line_data in data.get("lines", []):
            line = PurchaseOrderLine.objects.get(id=line_data["line_id"])
            received = line_data["quantity_received"]
            line.quantity_received += received
            line.save()

            # Actualizar stock en inventory
            product = line.product
            product.stock_quantity += received
            product.save(update_fields=["stock_quantity"])

            # Registrar movimiento
            StockMovement.objects.create(
                product=product,
                movement_type="in",
                quantity=received,
                reference=f"PO-{po.po_number}",
                notes=f"Recepción PO {po.po_number}",
                created_by="system",
            )

        # Check if all lines fully received
        if all(l.quantity_received >= l.quantity_ordered for l in po.lines.all()):
            po.status = "received"
        else:
            po.status = "partial"
        po.save()

    return {"status": po.status, "po_id": po.id}
