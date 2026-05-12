"""
SRIClient — Cliente SOAP para Web Services SRI Ecuador

Endpoint: RecepcionComprobantesOffline
 Operación: validarComprobante(xml_base64)
"""
import httpx
import base64
from lxml import etree
from typing import Optional, Dict, Any


class SRIClient:
    """Cliente SOAP para envío de comprobantes al SRI"""
    URLs = {
        1: "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline",
        2: "https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline",
    }
    TNS_NS = "http://ec.gob.sri.ws.recepcion"
    SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"

    def __init__(self, environment: int = 1, timeout: int = 30):
        if environment not in self.URLs:
            raise ValueError(f"Ambiente inválido: {environment}. Use 1 o 2.")
        self.environment = environment
        self.url = self.URLs[environment]
        self.timeout = timeout

    def build_soap_envelope(self, xml_comprobante: str) -> str:
        if xml_comprobante.strip().startswith('<'):
            xml_b64 = base64.b64encode(xml_comprobante.encode('utf-8')).decode('ascii')
        else:
            xml_b64 = xml_comprobante

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="{self.SOAP_NS}"
                  xmlns:tns="{self.TNS_NS}">
  <soapenv:Header/>
  <soapenv:Body>
    <tns:validarComprobante>
      <xml>{xml_b64}</xml>
    </tns:validarComprobante>
  </soapenv:Body>
</soapenv:Envelope>'''

    def send_xml(self, signed_xml: str) -> Dict[str, Any]:
        """
        Envía XML firmado al SRI.

        Args:
            signed_xml: XML firmado digitalmente (string)

        Returns:
            dict: {success: bool, estado: str, mensaje: str, xml_autorizado: str}
        """
        try:
            soap_envelope = self.build_soap_envelope(signed_xml)
            headers = {
                'Content-Type': 'text/xml; charset=UTF-8',
                'SOAPAction': 'validarComprobante',
            }

            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.url,
                    content=soap_envelope.encode('utf-8'),
                    headers=headers
                )
                response.raise_for_status()

            # Parsear respuesta SOAP
            try:
                root = etree.fromstring(response.content)
                ns = {'soap': self.SOAP_NS, 'tns': self.TNS_NS}
                body = root.find('.//soap:Body', ns)
                resp_elem = body.find('.//tns:validarComprobanteResponse', ns) if body is not None else None

                if resp_elem is not None:
                    comp_elem = resp_elem.find('.//tns:comprobante', ns)
                    if comp_elem is not None:
                        estado_el = comp_elem.find('estado')
                        if estado_el is not None and estado_el.text == 'RECIBIDO':
                            # Extraer XML autorizado
                            xml_autorizado_el = comp_elem.find('comprobante')
                            if xml_autorizado_el is not None and xml_autorizado_el.text:
                                return {
                                    'success': True,
                                    'estado': 'RECIBIDO',
                                    'mensaje': 'Comprobante recibido correctamente',
                                    'xml_autorizado': xml_autorizado_el.text,
                                }
            except etree.XMLSyntaxError:
                pass  # fall through a error

            return {
                'success': False,
                'estado': 'ERROR',
                'mensaje': f"Respuesta inesperada del SRI (HTTP {response.status_code})",
                'xml_autorizado': '',
            }

        except httpx.HTTPStatusError as e:
            return {
                'success': False,
                'estado': 'ERROR',
                'mensaje': f"Error HTTP: {e.response.status_code}",
                'xml_autorizado': '',
            }
        except Exception as e:
            return {
                'success': False,
                'estado': 'ERROR',
                'mensaje': str(e),
                'xml_autorizado': '',
            }
