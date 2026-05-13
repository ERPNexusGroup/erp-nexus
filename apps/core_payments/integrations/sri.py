# apps/core_payments/integrations/sri.py
"""
Integración con SRI / Bancos ecuatorianos para transferencias bancarias.

 NOTA: SRI NO expone API pública de transferencias. La integración real
es con los bancos (Banco Pichincha, Produbanco, etc.) que ofrecen APIs
REST/SOAP con certificado digital .p12.

Esta clase es una abstracción que puede implementarse para:
- Banco Pichincha (Transferencias API)
- Produbanco (Pagos Móviles API)
- Nubi (aggregator de pagos)

Para producción: implementar `create_transfer` y `query_status` según
la documentación oficial del banco seleccionado.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from lxml import etree

logger = logging.getLogger(__name__)


class SRIClientError(Exception):
    """Excepción base para errores de integración SRI/Banco."""
    pass


class SRIClient:
    """
    Cliente para envío de transferencias bancarias vía SRI/Banco.

    Ambiente: 'test' (certificados prueba) | 'production'
    Requiere: certificado .p12 + password + endpoint URL.
    """

    # endpoints de prueba SRI (no real — usar URLs de banco)
    WSDL_TEST = "https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl"
    WSDL_PROD = "https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl"

    def __init__(self, cert_path: str, cert_password: str, environment: str = 'test'):
        if environment not in ('test', 'production'):
            raise ValueError("environment debe ser 'test' o 'production'")
        self.cert_path = cert_path
        self.cert_password = cert_password
        self.environment = environment
        self.wsdl_url = self.WSDL_TEST if environment == 'test' else self.WSDL_PROD
        self._private_key = None
        self._certificate = None
        self._load_certificate()

    def _load_certificate(self):
        """Carga certificado .p12 y extrae key+cert."""
        try:
            with open(self.cert_path, 'rb') as f:
                p12_data = f.read()
            key, cert, _ = pkcs12.load_key_and_certificates(
                p12_data,
                self.cert_password.encode(),
                backend=default_backend()
            )
            self._private_key = key
            self._certificate = cert
            logger.info(f"Certificado cargado: {cert.subject.rfc4514_string()}")
        except Exception as exc:
            logger.error(f"Error cargando certificado: {exc}")
            raise SRIClientError(f"Failed to load certificate: {exc}")

    def _sign_xml(self, xml_string: str) -> str:
        """
        Firma documento XML con certificado digital (XAdES-BES).
        Implementación simplificada — en producción usar `xmlsec` library.
        """
        # TODO: implementar firma XAdES según especificación SRI
        # Por ahora retornamos XML sin firmar (NO PRODUCCIÓN)
        logger.warning("XAdES signing not implemented — using unsigned XML (TEST ONLY)")
        return xml_string

    def create_transfer(self, bank_account, amount: Decimal, reference: str) -> Dict[str, Any]:
        """
        Crea transferencia bancaria.

        Args:
            bank_account: BankAccount instance
            amount: monto a transferir
            reference: referencia única (UUID)

        Returns:
            {'success': bool, 'transaction_id': str, 'error': str, 'raw': dict}
        """
        # Construir mensaje XML de transferencia según XSD del banco
        # Por ahora placeholder — implementar según API específica
        xml_payload = self._build_transfer_xml(bank_account, amount, reference)
        signed_xml = self._sign_xml(xml_payload)

        # Enviar vía SOAP/REST al endpoint del banco
        # Ejemplo SOAP:
        # headers = {'Content-Type': 'application/soap+xml; charset=utf-8'}
        # response = requests.post(self.wsdl_url, data=signed_xml, headers=headers, cert=(cert, key))

        # PLACEHOLDER — simular éxito en test
        if self.environment == 'test':
            return {
                'success': True,
                'transaction_id': f"TEST-{reference}",
                'status': 'PROCESSING',
                'raw': {'mock': True},
            }

        # PRODUCCIÓN: implementar según banco elegido
        raise NotImplementedError("Implementar create_transfer para banco específico (Pichincha/Produbanco/Nubi)")

    def _build_transfer_xml(self, bank_account, amount: Decimal, reference: str) -> str:
        """Construye XML de solicitud de transferencia."""
        # XML schema según especificación del banco
        # Ejemplo genérico:
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<transferencia>
    <bancoCodigo>{bank_account.bank_code}</bancoCodigo>
    <cuenta>{bank_account.account_number}</cuenta>
    <beneficiario>
        <nombre>{bank_account.holder_name}</nombre>
        <identificacion>{bank_account.holder_identification}</identificacion>
    </beneficiario>
    <monto>{str(amount)}</monto>
    <moneda>{bank_account.currency or 'USD'}</moneda>
    <referencia>{reference}</referencia>
    <concepto>Pago de comisiones ERP Nexus</concepto>
</transferencia>"""
        return xml

    def query_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Consulta estado de transferencia en banco/SRI.

        Returns:
            {'confirmed': bool, 'rejected': bool, 'reason': str, 'paid_at': datetime}
        """
        if self.environment == 'test':
            return {'confirmed': True, 'rejected': False, 'paid_at': datetime.now()}

        # PRODUCCIÓN: implementar API de consulta
        raise NotImplementedError("Implementar query_status para banco específico")


# ─── Factory ──────────────────────────────────────────────────────────────────
def get_payout_provider(provider: str, **kwargs) -> SRIClient:
    """
    Factory para obtener cliente de payout según proveedor.
    """
    if provider == 'SRI':
        return SRIClient(
            cert_path=kwargs.get('cert_path', settings.SRI_CERT_PATH),
            cert_password=kwargs.get('cert_password', settings.SRI_CERT_PASSWORD),
            environment=kwargs.get('environment', settings.SRI_ENVIRONMENT),
        )
    # TODO: NUBI, Banco Pichincha, etc.
    raise ValueError(f"Proveedor no implementado: {provider}")
