# Integración completa: Crear factura → XML → Firmar → Enviar a SRI
from datetime import datetime
from decimal import Decimal
from ..models import Invoice
from .code_unique import generate_access_key, generate_invoice_number
from .xml_generator import XMLGenerator
from .digital_signature import DigitalSigner
from .sri_client import SRIClient
from django.conf import settings


# TODO: Mover a settings
SRI_ENVIRONMENT = 1  # 1=Pruebas, 2=Producción
CERTIFICATE_PATH = "/path/to/certificate.p12"
CERTIFICATE_PASSWORD = ""


def send_invoice_to_sri(invoice_id: int) -> dict:
    """
    Orquesta el flujo completo de factura electrónica:

    1. Carga factura desde DB
    2. Genera XML
    3. Firma digital
    4. Envía a SRI
    5. Guarda respuesta

    Args:
        invoice_id: ID de Invoice

    Returns:
        dict: {success: bool, estado: str, mensaje: str, xml_sent: str, xml_response: str}
    """
    try:
        invoice = Invoice.objects.get(id=invoice_id)
    except Invoice.DoesNotExist:
        return {"success": False, "estado": "ERROR", "mensaje": "Factura no encontrada"}

    # 1. Cargar líneas
    lines = list(invoice.lines.all())
    if not lines:
        return {"success": False, "estado": "ERROR", "mensaje": "Factura sin líneas"}

    # 2. Generar clave acceso (si no existe)
    if not invoice.access_key:
        seq = generate_invoice_number(
            "001", "001", get_next_sequential(invoice.company, "001", "001")
        ).split("-")[2]
        invoice.access_key = generate_access_key(
            ruc=invoice.company.ruc,
            ambiente=invoice.ambiente,
            establishment_code="001",
            emission_point="001",
            sequential=seq,
            date=invoice.date,
        )
        invoice.save(update_fields=["access_key"])

    # 3. Generar XML
    generator = XMLGenerator(invoice.company)
    xml_raw = generator.generate(invoice, lines)

    # 4. Firmar
    signer = DigitalSigner(CERTIFICATE_PATH, CERTIFICATE_PASSWORD)
    xml_signed = signer.sign_xml(xml_raw)

    # Guardar XML firmado
    invoice.xml_content = xml_signed
    invoice.save(update_fields=["xml_content"])

    # 5. Enviar a SRI
    client = SRIClient(environment=invoice.ambiente)
    result = client.send(xml_signed)

    # 6. Guardar log
    from .models import SRISendLog
    SRISendLog.objects.create(
        invoice=invoice,
        endpoint=client.url,
        request_xml=xml_signed[:1000],  # truncado
        response_xml=result.get("respuesta_xml", "")[:2000],
        response_code=result.get("estado", ""),
        success=result.get("success", False),
        error_message=result.get("mensaje", ""),
    )

    # 7. Actualizar estado factura
    estado_sri = result.get("estado", "").upper()
    if estado_sri in ("APROBADA", "AUTORIZADA", "AUTORIZADO"):
        invoice.sri_status = "accepted"
        invoice.sri_authorization_date = datetime.now()
        invoice.sri_xml_autorizado = result.get("comprobante_autorizado", "")
    elif estado_sri == "RECHAZADA":
        invoice.sri_status = "rejected"
    else:
        invoice.sri_status = "sent"

    invoice.sri_message = result.get("mensaje", "")
    invoice.save(update_fields=["sri_status", "sri_message", "sri_authorization_date", "sri_xml_autorizado"])

    # 8. Incrementar contador licencia
    try:
        from .models import CompanyLicense
        license_obj = CompanyLicense.objects.filter(
            company=invoice.company,
            is_active=True
        ).first()
        if license_obj:
            license_obj.increment_invoice_count()
    except Exception:
        pass

    return result
