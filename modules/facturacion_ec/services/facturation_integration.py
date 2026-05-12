"""
Integración completa: Core Invoice → SRI Extension → XML → Firma → Envío

Flujo:
1. Obtener Invoice desde core facturacion (ya existe)
2. Crear/obtener InvoiceSRIExtension asociada
3. Generar XML SRI
4. Firmar XML
5. Enviar a SRI
6. Actualizar extensión con respuesta
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from apps.facturacion.models import Invoice as CoreInvoice
from modules.facturacion_ec.models import InvoiceSRIExtension, SriTipoComprobante
from .code_unique import generate_access_key, generate_invoice_number, get_next_sequential_for_invoice
from .xml_generator import XMLGenerator
from .digital_signature import DigitalSigner
from .sri_client import SRIClient
from django.conf import settings


def generate_sri_extension(invoice_id: int, ambiente: int = 1) -> InvoiceSRIExtension:
    """
    Genera la extensión SRI para una factura core.

    Args:
        invoice_id: ID de factura del core
        ambiente: 1=Pruebas, 2=Producción

    Returns:
        InvoiceSRIExtension guardada
    """
    invoice = CoreInvoice.objects.get(id=invoice_id)

    # Obtener o crear extensión
    extension, created = InvoiceSRIExtension.objects.get_or_create(
        invoice=invoice,
        defaults={'ambiente': ambiente}
    )

    # Asignar tipo comprobante (default Factura 01)
    tipo_comp, _ = SriTipoComprobante.objects.get_or_create(
        code='01',
        defaults={'name': 'Factura', 'description': 'Factura de venta'}
    )
    extension.tipo_comprobante = tipo_comp

    # Generar clave acceso
    establishment_code = getattr(invoice.company, 'establishment_code', '001')
    emission_point_code = getattr(invoice.company, 'point_emission_code', '001')
    sequential = get_next_sequential_for_invoice(invoice.company)

    access_key = generate_access_key(
        ruc=invoice.company.ruc,
        ambiente=extension.ambiente,
        establishment_code=establishment_code,
        emission_point_code=emission_point_code,
        sequential=sequential,
        date=invoice.date
    )
    extension.access_key = access_key

    # Generar número de factura
    invoice.number = generate_invoice_number(
        establishment_code=establishment_code,
        emission_point_code=emission_point_code,
        sequential=int(sequential)
    )
    invoice.save(update_fields=['number'])

    # Generar XML
    xml_gen = XMLGenerator()
    xml_content = xml_gen.generate_invoice_xml(
        invoice=invoice,
        ambiente=extension.ambiente,
        access_key=access_key,
        establishment_code=establishment_code,
        emission_point_code=emission_point_code,
        sequential=sequential,
    )

    # Firmar XML
    cert_path = getattr(settings, 'FACTURACION_EC_CERT_PATH', '')
    cert_pass = getattr(settings, 'FACTURACION_EC_CERT_PASSWORD', '')
    signer = DigitalSigner(p12_path=cert_path, password=cert_pass)
    signed_xml = signer.sign_xml(xml_content)

    extension.xml_content = signed_xml

    # Hash para registro
    import hashlib
    extension.xml_original_hash = hashlib.sha256(signed_xml.encode('utf-8')).hexdigest()
    extension.save()

    return extension


def send_invoice_to_sri(invoice_id: int) -> Dict[str, Any]:
    """
    Envía factura (core) al SRI, creando extensión si no existe.

    Args:
        invoice_id: ID de Invoice del core

    Returns:
        dict con éxito/error
    """
    try:
        invoice = CoreInvoice.objects.get(id=invoice_id)

        # Obtener o crear extensión SRI
        extension, created = InvoiceSRIExtension.objects.get_or_create(
            invoice=invoice
        )

        # Si no tiene XML/firma, generarla (usa extension.ambiente)
        if not extension.xml_content:
            generate_sri_extension(invoice_id, ambiente=extension.ambiente or 1)
            extension.refresh_from_db()

        # Enviar a SRI
        client = SRIClient(environment=extension.ambiente or 1)
        result = client.send_xml(extension.xml_content)

        # Actualizar extensión con respuesta
        extension.sri_status = 'accepted' if result.get('success') else 'rejected'
        extension.sri_message = result.get('mensaje', '')
        extension.sri_xml_autorizado = result.get('xml_autorizado', '')
        if result.get('success'):
            extension.sri_authorization_date = datetime.now()
        extension.save()

        # Actualizar factura core status
        invoice.status = 'sent' if result.get('success') else 'draft'
        invoice.save(update_fields=['status'])

        return result

    except Exception as e:
        return {'success': False, 'mensaje': str(e)}


def process_pending_invoices(limit: int = 50, company_id: int = None) -> dict:
    """
    Procesa facturas pendientes de envío SRI.
    Usado por management command.
    """
    qs = CoreInvoice.objects.filter(status='draft').order_by('date', 'id')
    if company_id:
        qs = qs.filter(company_id=company_id)

    pending = qs[:limit]
    total = pending.count()

    results = {
        'total': total,
        'success': 0,
        'errors': 0,
        'details': []
    }

    for invoice in pending:
        try:
            res = send_invoice_to_sri(invoice.id)
            if res.get('success'):
                results['success'] += 1
                results['details'].append(f"{invoice.number}: OK")
            else:
                results['errors'] += 1
                results['details'].append(f"{invoice.number}: {res.get('mensaje','ERROR')}")
        except Exception as e:
            results['errors'] += 1
            results['details'].append(f"{invoice.number}: {str(e)}")

    return results
