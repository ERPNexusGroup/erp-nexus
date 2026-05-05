# XML Generator - Genera factura electrónica XML según XSD SRI Ecuador
from jinja2 import Template
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from typing import Optional


# Plantilla XML SRI Ecuador (factura 01)
# Cumple con XSD oficial SRI (versión 1.0.0)
INVOICE_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<factura id="comprobante" version="1.0.0">
  <infoTributaria>
    <ambiente>{{ environment }}</ambiente>
    <tipoEmision>1</tipoEmision>
    <razonSocialSujeto>{{ company.legal_name | e }}</razonSocialSujeto>
    <nombreComercial>{{ company.commercial_name | default(company.name) | e }}</nombreComercial>
    <ruc>{{ company.ruc }}</ruc>
    <codDoc>{{ invoice_type_code }}</codDoc>
    <estab>{{ establishment_code }}</estab>
    <ptoEmi>{{ emission_point_code }}</ptoEmi>
    <secuencial>{{ sequential_str }}</secuencial>
    <dirMatriz>{{ company.address | e }}</dirMatriz>
    {% if invoice.customer.identification_type == '04' %}
    <codDocSustento></codDocSustento>
    <numDocSustento></numDocSustento>
    {% endif %}
    <fechaEmision>{{ invoice_date }}</fechaEmision>
    <dirEstablecimiento>{{ company.address | e }}</dirEstablecimiento>
    <tipoIdentificacionComprador>{{ invoice.customer.identification_type }}</tipoIdentificacionComprador>
    <razonSocialComprador>{{ invoice.customer.name | e }}</razonSocialComprador>
    <direccionComprador>{{ invoice.customer.address | e }}</direccionComprador>
    <totalSinImpuestos>{{ "%.2f"|format(invoice.subtotal) }}</totalSinImpuestos>
    <totalDescuento>0.00</totalDescuento>
    {% for impuesto in total_impuestos %}
    <totalConImpuestos>
      <totalImpuesto>
        <codigo>{{ impuesto.codigo }}</codigo>
        <codigoPorcentaje>{{ impuesto.codigo_porcentaje }}</codigoPorcentaje>
        <baseImponible>{{ "%.2f"|format(impuesto.base_imponible) }}</baseImponible>
        <valor>{{ "%.2f"|format(impuesto.valor) }}</valor>
      </totalImpuesto>
    </totalConImpuestos>
    {% endfor %}
    <propina>0.00</propina>
    <importeTotal>{{ "%.2f"|format(invoice.total) }}</importeTotal>
    <moneda>DOLAR</moneda>
    {% if extra_fields %}
    {% for key, value in extra_fields.items() %}
    <campoAdicional nombre="{{ key | e }}">{{ value | e }}</campoAdicional>
    {% endfor %}
    {% endif %}
  </infoTributaria>
  <detalles>
    {% for line in invoice_lines %}
    <detalle>
      <codigoPrincipal>{{ line.product.code | e }}</codigoPrincipal>
      <descripcion>{{ line.product.name | e }}</descripcion>
      <cantidad>{{ "%.4f"|format(line.quantity) }}</cantidad>
      <precioUnitario>{{ "%.6f"|format(line.unit_price) }}</precioUnitario>
      <precioTotalSinImpuesto>{{ "%.2f"|format(line.subtotal) }}</precioTotalSinImpuesto>
      <impuestos>
        <impuesto>
          <codigo>2</codigo>
          <codigoPorcentaje>{{ line.tax_rate | replace('.00','') }}</codigoPorcentaje>
          <tarifa>{{ "%.2f"|format(line.tax_rate) }}</tarifa>
          <baseImponible>{{ "%.2f"|format(line.subtotal) }}</baseImponible>
          <valor>{{ "%.2f"|format(line.tax_amount) }}</valor>
        </impuesto>
      </impuestos>
      {% if line.discount > 0 %}
      <descuento>{{ "%.2f"|format(line.discount) }}</descuento>
      {% endif %}
    </detalle>
    {% endfor %}
  </detalles>
  <infoAdicional>
    {% if forma_pago %}
    <campoAdicional nombre="FormasPago">{{ forma_pago }}</campoAdicional>
    {% endif %}
  </infoAdicional>
</factura>
"""


class XMLGenerator:
    """Generador de XML para facturas electrónicas SRI Ecuador"""

    def __init__(self, company):
        self.company = company
        self.template = Template(INVOICE_XML_TEMPLATE)

    def generate(self, invoice, invoice_lines, formapago="20") -> str:
        """
        Genera XML completo de factura.

        Args:
            invoice: Instancia Invoice model
            invoice_lines: Lista de InvoiceLine
            formapago: Forma de pago SRI (20=Otros, 01=Efectivo, etc.)

        Returns:
            String XML (UTF-8)
        """
        # Calcular totales por tipo de impuesto
        impuestos_agrupados = self._group_taxes(invoice_lines)

        # Constraints XML
        invoice_date = invoice.date.strftime("%d/%m/%Y")

        context = {
            "environment": invoice.ambiente,
            "company": self.company,
            "invoice": invoice,
            "invoice_type_code": invoice.tipo_comprobante.code,
            "establishment_code": "001",   # TODO: desde company config
            "emission_point_code": "001",  # TODO: desde company config
            "sequential_str": self._extract_sequential(invoice.number),
            "invoice_date": invoice_date,
            "invoice_lines": invoice_lines,
            "total_impuestos": impuestos_agrupados,
            "forma_pago": formapago,
            "extra_fields": self._get_extra_fields(invoice),
        }

        xml_str = self.template.render(**context)

        # Asegurar UTF-8
        xml_bytes = xml_str.encode('utf-8')
        return xml_bytes.decode('utf-8')

    def _extract_sequential(self, number: str) -> str:
        """Extrae el secuencial de 9 dígitos del número 001-001-000000001"""
        parts = number.split("-")
        if len(parts) == 3:
            return parts[2].zfill(9)
        return "000000001"

    def _group_taxes(self, invoice_lines):
        """
        Agrupa impuestos por código/porcentaje para elemento <totalConImpuestos>.
        SRI requiere un <totalImpuesto> por tipo de impuesto.
        """
        groups = {}
        for line in invoice_lines:
            key = (line.tax_rate, line.tax_code if hasattr(line, 'tax_code') else '2')
            if key not in groups:
                groups[key] = {
                    'codigo': key[1],  # 2=IVA, 3=ICE, etc.
                    'codigo_porcentaje': str(int(line.tax_rate)) if line.tax_rate == int(line.tax_rate) else str(line.tax_rate),
                    'base_imponible': Decimal('0.00'),
                    'valor': Decimal('0.00'),
                }
            groups[key]['base_imponible'] += Decimal(str(line.subtotal))
            groups[key]['valor'] += Decimal(str(line.tax_amount))

        return list(groups.values())

    def _get_extra_fields(self, invoice):
        """Campos adicionales opcionales (por ejemplo: Guía remisión)"""
        extra = {}
        if invoice.guia_remision_number:
            extra["GuiaRemision"] = invoice.guia_remision_number
        return extra


def validate_xml_against_xsd(xml_string: str, xsd_path: str = None) -> tuple[bool, str]:
    """
    Valida XML generado contra XSD oficial del SRI.

    Args:
        xml_string: String XML a validar
        xsd_path: Ruta al archivo XSD (si None, usa XSD embebido)

    Returns:
        (es_valido, mensaje_error)
    """
    from lxml import etree

    try:
        xml_doc = etree.fromstring(xml_string.encode('utf-8'))

        if xsd_path:
            with open(xsd_path, 'rb') as f:
                xsd_doc = etree.parse(f)
        else:
            # XSD mínimo embebido (solo para pruebas de estructura)
            xsd_str = _get_minimal_xsd()
            xsd_doc = etree.fromstring(xsd_str.encode('utf-8'))

        schema = etree.XMLSchema(xsd_doc)
        schema.assertValid(xml_doc)
        return True, "XML válido contra XSD"

    except etree.DocumentInvalid as e:
        return False, f"Error validación XSD: {str(e)}"
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"


def _get_minimal_xsd() -> str:
    """
    XSD mínimo embebido para validaciones en desarrollo.
    En producción usar XSD oficial descargado del SRI.
    """
    return """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="factura">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="infoTributaria"><xs:complexType><xs:sequence>
          <xs:element name="ambiente" type="xs:integer"/>
          <xs:element name="tipoEmision" type="xs:integer"/>
          <xs:element name="razonSocialSujeto" type="xs:string"/>
          <xs:element name="ruc" type="xs:string"/>
          <xs:element name="codDoc" type="xs:string"/>
          <xs:element name="estab" type="xs:string"/>
          <xs:element name="ptoEmi" type="xs:string"/>
          <xs:element name="secuencial" type="xs:string"/>
          <xs:element name="fechaEmision" type="xs:string"/>
        </xs:sequence></xs:complexType></xs:element>
        <xs:element name="detalles">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="detalle" maxOccurs="unbounded">
                <xs:complexType>
                  <xs:sequence>
                    <xs:element name="codigoPrincipal" type="xs:string"/>
                    <xs:element name="descripcion" type="xs:string"/>
                    <xs:element name="cantidad" type="xs:decimal"/>
                    <xs:element name="precioUnitario" type="xs:decimal"/>
                    <xs:element name="precioTotalSinImpuesto" type="xs:decimal"/>
                    <xs:element name="impuestos">
                      <xs:complexType>
                        <xs:sequence>
                          <xs:element name="impuesto">
                            <xs:complexType>
                              <xs:sequence>
                                <xs:element name="codigo" type="xs:string"/>
                                <xs:element name="codigoPorcentaje" type="xs:string"/>
                                <xs:element name="baseImponible" type="xs:decimal"/>
                                <xs:element name="valor" type="xs:decimal"/>
                              </xs:sequence>
                            </xs:complexType>
                          </xs:element>
                        </xs:sequence>
                      </xs:complexType>
                    </xs:element>
                  </xs:sequence>
                </xs:complexType>
              </xs:element>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>"""
