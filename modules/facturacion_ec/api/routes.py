"""
API REST — Plugin Facturación Electrónica Ecuador (SRI)

Endpoints exclusivos para envío/consulta SRI.
La gestión de facturas (crear, listar) está en `apps.facturacion` core.
"""
from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

# Usar string references para evitar import circular
from django.apps import apps

Invoice = apps.get_model('facturacion', 'Invoice')
InvoiceSRIExtension = apps.get_model('facturacion_ec', 'InvoiceSRIExtension')

from ..services.facturation_integration import send_invoice_to_sri
from datetime import datetime


router = Router(tags=["Facturación Electrónica SRI"])


# ===================== SCHEMAS =====================

class SRISendResponse(Schema):
    success: bool
    mensaje: str
    sri_status: str = None


class InvoiceSRIOut(Schema):
    id: int
    invoice_number: str
    ambiente: int
    tipo_comprobante: str = None
    access_key: str
    sri_status: str
    sri_authorization_date: datetime = None


# ===================== ENDPOINTS =====================

@router.get("/invoices/", response=list[InvoiceSRIOut])
def list_sri_invoices(request, sri_status: str = None):
    """
    Lista facturas con extensión SRI.
    """
    company = request.active_company
    qs = InvoiceSRIExtension.objects.filter(invoice__company=company)
    if sri_status:
        qs = qs.filter(sri_status=sri_status)
    return [
        {
            "id": ext.id,
            "invoice_number": ext.invoice.number,
            "ambiente": ext.ambiente,
            "tipo_comprobante": str(ext.tipo_comprobante) if ext.tipo_comprobante else None,
            "access_key": ext.access_key,
            "sri_status": ext.sri_status,
            "sri_authorization_date": ext.sri_authorization_date,
        }
        for ext in qs.select_related('invoice', 'tipo_comprobante')[:100]
    ]


@router.post("/invoices/{invoice_id}/send_to_sri/", response=SRISendResponse)
def send_to_sri(request, invoice_id: int):
    """
    Envía factura (existente en core) al SRI.

    La factura debe existir en `apps.facturacion.Invoice`.
    Crea/actualiza la extensión SRI automáticamente.
    """
    company = request.active_company
    invoice = get_object_or_404(Invoice, id=invoice_id, company=company)

    result = send_invoice_to_sri(invoice.id)

    # Devolver estado actualizado
    ext = getattr(invoice, 'sri_extension', None)
    return {
        "success": result.get('success', False),
        "mensaje": result.get('mensaje', ''),
        "sri_status": ext.sri_status if ext else 'unknown',
    }


@router.get("/invoices/{invoice_id}/status/", response=InvoiceSRIOut)
def get_sri_status(request, invoice_id: int):
    """
    Consulta estado SRI de una factura.
    """
    company = request.active_company
    invoice = get_object_or_404(Invoice, id=invoice_id, company=company)
    ext = getattr(invoice, 'sri_extension', None)
    if not ext:
        return {"error": "Factura sin extensión SRI"}

    return {
        "id": ext.id,
        "invoice_number": ext.invoice.number,
        "ambiente": ext.ambiente,
        "tipo_comprobante": str(ext.tipo_comprobante) if ext.tipo_comprobante else None,
        "access_key": ext.access_key,
        "sri_status": ext.sri_status,
        "sri_authorization_date": ext.sri_authorization_date,
    }


@router.get("/invoices/{invoice_id}/xml")
def download_xml(request, invoice_id: int):
    """
    Descarga XML firmado de la factura.
    """
    company = request.active_company
    invoice = get_object_or_404(Invoice, id=invoice_id, company=company)
    ext = getattr(invoice, 'sri_extension', None)
    if not ext or not ext.xml_content:
        return {"error": "XML no generado aún"}

    return HttpResponse(
        ext.xml_content,
        content_type='application/xml',
        headers={'Content-Disposition': f'attachment; filename="{invoice.number}.xml"'}
    )


@router.post("/invoices/{invoice_id}/resend")
def resend_invoice(request, invoice_id: int):
    """
    Reenvía factura rechazada/corrige.
    """
    company = request.active_company
    invoice = get_object_or_404(Invoice, id=invoice_id, company=company)
    ext = getattr(invoice, 'sri_extension', None)
    if not ext:
        return {"success": False, "error": "Factura sin extensión SRI"}

    if ext.sri_status not in ('rejected', 'draft', 'pending'):
        return {"success": False, "error": "Solo se pueden reenviar facturas rechazadas o pendientes"}

    result = send_invoice_to_sri(invoice.id)

    return {
        "success": result.get('success', False),
        "mensaje": result.get('mensaje', ''),
        "sri_status": ext.sri_status,
    }
