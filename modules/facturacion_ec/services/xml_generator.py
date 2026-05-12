"""
XMLGenerator — Genera XML SRI Ecuador desde core facturacion models

Usa:
- apps.facturacion.models: Invoice, InvoiceLine, Customer, Product
- modules.facturacion_ec.models: SriTipoComprobante

Accede a campos SRI a través de InvoiceSRIExtension.
"""
from jinja2 import Template
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
import hashlib
import urllib.parse


INVOICE_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<factura id="comprobante" version="1.0.0">
  <infoTributaria>
    <ambiente>{{ ambiente }}</ambiente>
    <tipoEmision>1</tipoEmision>
    <razonSocialSujeto>{{ company.legal_name | e }}</razonSocialSujeto>
    <nombreComercial>{{ company.commercial_name | default(company.name) | e }}</nombreComercial>
    <ruc>{{ company.ruc }}</ruc>
    <codDoc>{{ invoice_type_code }}</codDoc>
    <estab>{{ establishment_code }}</estab>
    <ptoEmi>{{ emission_point_code }}</ptoEmi>
    <secuencial>{{ sequential_str }}</secuencial>
    <claveAcceso>{{ access_key }}</claveAcceso>
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
  </infoTributaria>
  <detalles>
    {% for line in invoice_lines %}
    <detalle>
      <codigoPrincipal>{{ line.product.code | e }}</codigoPrincipal>
      <descripcion>{{ line.description | e }}</descripcion>
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
</factura>
"""


class XMLGenerator:
    def __init__(self):
        self.template = Template(INVOICE_XML_TEMPLATE)

    def generate_invoice_xml(
        self,
        invoice,
        ambiente: int,
        access_key: str,
        establishment_code: str = "001",
        emission_point_code: str = "001",
        sequential: str = "",
        **kwargs
    ) -> str:
        """
        Genera XML de factura desde core Invoice.

        Args:
            invoice: apps.facturacion.models.Invoice
            ambiente: 1=Pruebas, 2=Producción
            access_key: clave acceso SRI (49 dígitos)
            establishment_code: código establecimiento (3 dígitos)
            emission_point_code: código punto emisión (3 dígitos)
            sequential: secuencial (9 dígitos)

        Returns:
            str: XML generado (sin firmar)
        """
        company = invoice.company
        customer = invoice.customer
        invoice_lines = invoice.lines.all()

        # Agrupar impuestos (por ahora todos IVA 2)
        total_impuestos = [{
            'codigo': '2',
            'codigo_porcentaje': '12',
            'base_imponible': float(invoice.subtotal),
            'valor': float(invoice.tax_total)
        }]

        # Fecha en formato SRI: YYYY-MM-ddThh:mm:ssOffset
        emission_dt = datetime.combine(invoice.date, datetime.min.time())
        fecha_emision = emission_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
        # Añadir offset manual si no hay tz
        if not fecha_emision.endswith(('-05:00', '+00:00')):
            fecha_emision += "-05:00"

        context = {
            'ambiente': ambiente,
            'invoice_type_code': '01',  # Factura por defecto
            'company': {
                'legal_name': company.legal_name or company.name,
                'commercial_name': company.commercial_name or company.name,
                'name': company.name,
                'ruc': company.ruc,
                'address': company.address or 'Dirección no especificada',
            },
            'establishment_code': establishment_code,
            'emission_point_code': emission_point_code,
            'sequential_str': sequential,
            'access_key': access_key,
            'invoice_date': fecha_emision,
            'invoice': invoice,
            'customer': customer,
            'invoice_lines': invoice_lines,
            'total_impuestos': total_impuestos,
        }

        xml = self.template.render(**context)
        return xml
