# SRI Client - Comunicación con Web Services del SRI Ecuador
import httpx
from lxml import etree
from datetime import datetime
import base64
from typing import Optional, Dict, Any


class SRIClient:
    """
    Cliente para Web Services de Recepción de Comprobantes del SRI Ecuador.

    URLs oficiales:
    - Pruebas: https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl
    - Producción: https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl

    Protocolo: SOAP 1.1
    """

    # URLs oficiales SRI (mayo 2024)
    URLs = {
        1: "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl",
        2: "https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl",
    }

    # Namespace SOAP
    SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
    SRI_NS = "http://ec.gob.ec/sri/comprobantes"

    def __init__(self, environment: int = 1, timeout: int = 30):
        """
        Inicializa cliente SRI.

        Args:
            environment: 1=Pruebas, 2=Producción
            timeout: Timeout en segundos para requests
        """
        if environment not in self.URLs:
            raise ValueError(f"Ambiente inválido: {environment}. Use 1 o 2.")
        self.environment = environment
        self.url = self.URLs[environment]
        self.timeout = timeout

    def build_soap_envelope(self, xml_comprobante: str) -> str:
        """
        Construye envelope SOAP con XML firmado.

        Args:
            xml_comprobante: XML firmado (base64 o binario)

        Returns:
            String XML del envelope SOAP completo
        """
        # Si es string XML, convertir a base64
        if xml_comprobante.strip().startswith('<'):
            xml_bytes = xml_comprobante.encode('utf-8')
            xml_b64 = base64.b64encode(xml_bytes).decode('ascii')
        else:
            xml_b64 = xml_comprobante

        soap_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="{self.SOAP_NS}"
                  xmlns:ec="{self.SRI_NS}">
  <soapenv:Header/>
  <soapenv:Body>
    <ec:recepcionComprobante>
      <xmlComprobante>{xml_b64}</xmlComprobante>
    </ec:recepcionComprobante>
  </soapenv:Body>
</soapenv:Envelope>'''
        return soap_template

    async def send(self, signed_xml: str) -> Dict[str, Any]:
        """
        Envía comprobante firmado a SRI (async).

        Args:
            signed_xml: XML firmado (string)

        Returns:
            Dict: {success: bool, estado: str, mensaje: str, respuesta_xml: str}
        """
        soap_envelope = self.build_soap_envelope(signed_xml)

        headers = {
            'Content-Type': 'text/xml; charset=UTF-8',
            'SOAPAction': ''
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.post(
                    self.url,
                    content=soap_envelope,
                    headers=headers
                )

            # Parsear respuesta SOAP
            return self._parse_soap_response(response.text)

        except httpx.TimeoutException:
            return {
                "success": False,
                "estado": "TIMEOUT",
                "mensaje": "Timeout al conectar con SRI",
                "respuesta_xml": ""
            }
        except Exception as e:
            return {
                "success": False,
                "estado": "ERROR",
                "mensaje": f"Error HTTP: {str(e)}",
                "respuesta_xml": ""
            }

    def _parse_soap_response(self, soap_xml: str) -> Dict[str, Any]:
        """
        Parsea respuesta SOAP del SRI y extrae estado.

        Respuestas posibles:
        - ESTADO = "RECIBIDA" → SRI recibió, procesando…
        - ESTADO = "APROBADA" → Factura autorizada
        - ESTADO = "RECHAZADA" → Error en factura
        """
        try:
            root = etree.fromstring(soap_xml.encode('utf-8'))

            # Buscar respuesta en namespace SRI
            ns = {'soap': self.SOAP_NS, 'sri': self.SRI_NS}

            # Extraer estado y mensajes
            estado_elem = root.find('.//sri:estado', ns)
            comprobante_elem = root.find('.//sri:comprobante', ns)
            mensaje_elem = root.find('.//sri:mensaje', ns)
            info_adicional_elem = root.find('.//sri:infoAdicional', ns)

            estado = estado_elem.text if estado_elem is not None else "DESCONOCIDO"
            comprobante = comprobante_elem.text if comprobante_elem is not None else ""
            mensaje = mensaje_elem.text if mensaje_elem is not None else ""
            info_adicional = info_adicional_elem.text if info_adicional_elem is not None else ""

            success = estado in ("APROBADA", "RECIBIDA", "AUTORIZADO")
            if estado == "RECHAZADA":
                success = False

            return {
                "success": success,
                "estado": estado,
                "mensaje": mensaje,
                "info_adicional": info_adicional,
                "respuesta_xml": soap_xml,
                "comprobante_autorizado": comprobante,
            }

        except etree.XMLSyntaxError as e:
            return {
                "success": False,
                "estado": "ERROR_PARSE",
                "mensaje": f"Error parseando XML: {e}",
                "respuesta_xml": soap_xml,
            }

    def check_authorization(self, access_key: str) -> Dict[str, Any]:
        """
        Consulta estado de autorización de una factura por clave acceso.

        URL: https://cel.sri.gob.ec/servicios-sri-consulta/stream?tipo=autorizacion&clave=...

        Args:
            access_key: Clave de acceso de 49 dígitos

        Returns:
            Dict con estado autorización
        """
        auth_url = (
            f"https://cel.sri.gob.ec/servicios-sri-consulta/stream?"
            f"tipo=autorizacion&clave={access_key}"
        )

        try:
            import requests
            resp = requests.get(auth_url, timeout=self.timeout, verify=False)
            resp.raise_for_status()

            # Respuesta es XML
            return self._parse_authorization_response(resp.text)

        except Exception as e:
            return {
                "estado": "ERROR",
                "mensaje": str(e),
                "autorizado": False,
            }

    def _parse_authorization_response(self, xml: str) -> Dict[str, Any]:
        """Parsea respuesta de consulta autorización"""
        try:
            root = etree.fromstring(xml.encode('utf-8'))
            ns = {'ns': 'http://ec.gob.ec/servicios-sri-consulta'}

            estado = root.find('.//ns:estado', ns)
            fecha_autorizacion = root.find('.//ns:fechaAutorizacion', ns)
            numero_autorizacion = root.find('.//ns:numeroAutorizacion', ns)

            return {
                "estado": estado.text if estado is not None else "DESCONOCIDO",
                "fecha_autorizacion": fecha_autorizacion.text if fecha_autorizacion is not None else "",
                "numero_autorizacion": numero_autorizacion.text if numero_autorizacion is not None else "",
                "autorizado": (estado is not None and estado.text == "AUTORIZADO"),
            }
        except Exception:
            return {"estado": "ERROR", "autorizado": False}
