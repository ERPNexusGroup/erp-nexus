# Digital Signature - Firma XML con certificado X.509 (.p12)
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.x509 import load_pem_x509_certificate
from cryptography.exceptions import UnsupportedAlgorithm
from signxml import XMLSigner, methods
from signxml.exceptions import InvalidSignature
import base64
from datetime import datetime
from lxml import etree


class DigitalSigner:
    """
    Firma documentos XML con certificado X.509 (.p12 o .pfx).

    Para Ecuador SRI:
    - Certificado emitido por SRI (o entidad certificadora acreditada)
    - Formato PKCS#12 (extensión .p12 o .pfx)
    - Contiene clave privada + certificado público
    """

    def __init__(self, p12_path: str, password: str):
        """
        Inicializa el firmador con certificado.

        Args:
            p12_path: Ruta al archivo .p12/.pfx
            password: Contraseña del certificado
        """
        self.p12_path = p12_path
        self.password = password
        self._private_key = None
        self._cert = None
        self._load_certificate()

    def _load_certificate(self):
        """Carga certificado desde archivo PKCS#12"""
        try:
            from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

            with open(self.p12_path, 'rb') as f:
                p12_data = f.read()

            self._private_key, self._cert, self._additional_certs = (
                load_key_and_certificates(
                    p12_data,
                    self.password.encode('utf-8')
                )
            )

            # Convertir certificado a PEM para signxml
            self._cert_pem = self._cert.public_bytes(Encoding.PEM).decode('utf-8')
            self._private_key_pem = self._private_key.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.PKCS8,
                encryption_algorithm=NoEncryption()
            ).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Error cargando certificado: {e}")

    def sign_xml(self, xml_string: str, reference_id: str = "comprobante") -> str:
        """
        Firma un documento XML según estándar del SRI Ecuador.

        Para factura electrónica (XSD SRI), el elemento <factura> debe tener
        atributo Id (mayúscula) y la firma enveloped referencia ese ID.

        Args:
            xml_string: XML como string (UTF-8)
            reference_id: Atributo Id del elemento a firmar (default: 'comprobante')

        Returns:
            XML firmado (con elemento Signature anexado)
        """
        if not hasattr(self, '_private_key_pem') or not hasattr(self, '_cert_pem'):
            raise ValueError("Certificado no cargado en formato PEM")

        try:
            signer = XMLSigner(
                method=methods.enveloped,
                signature_algorithm="rsa-sha256",
                digest_algorithm="sha256"
            )

            # Parsear XML
            xml_doc = etree.fromstring(xml_string.encode('utf-8'))

            # Asegurar atributo Id mayúscula en el elemento raíz (requerido por SRI)
            if xml_doc.get('Id') is None:
                xml_doc.set('Id', reference_id)

            # Firmar con PEM strings (formato que acepta signxml)
            signed_xml = signer.sign(
                xml_doc,
                cert=self._cert_pem,
                key=self._private_key_pem,
                reference_uri=f"#{reference_id}"
            )

            return etree.tostring(signed_xml, encoding='utf-8', xml_declaration=True).decode('utf-8')

        except Exception as e:
            raise ValueError(f"Error firmando XML: {str(e)}")

    def verify_signature(self, signed_xml: str) -> bool:
        """
        Verifica que una firma XML es válida (útil para debug).

        Args:
            signed_xml: XML firmado

        Returns:
            True si la firma es válida
        """
        try:
            from signxml import XMLVerifier
            verifier = XMLVerifier()
            verified_data = verifier.verify(signed_xml.encode('utf-8'))
            return True
        except InvalidSignature:
            return False
        except Exception:
            return False


def load_certificate_info(p12_path: str, password: str) -> dict:
    """
    Extrae información del certificado sin firmar nada.

    Útil para mostrar datos al usuario (RUC, válido hasta, etc.)

    Returns:
        Dict con: subject, issuer, serial_number, not_valid_before, not_valid_after
    """
    try:
        with open(p12_path, 'rb') as f:
            p12_data = f.read()
        _, cert, _ = load_key_and_certificates(
            p12_data, password.encode('utf-8')
        )

        from cryptography.x509 import NameOID

        # Subject (emisor del certificado = SRI)
        subject = cert.subject
        ruc = subject.get_attributes_for_oid(NameOID.SERIAL_NUMBER)
        ruc_value = ruc[0].value if ruc else ""

        # Issuer (autoridad certificadora)
        issuer = cert.issuer

        return {
            "subject": str(subject),
            "issuer": str(issuer),
            "ruc": ruc_value,
            "serial_number": cert.serial_number,
            "not_valid_before": cert.not_valid_before,
            "not_valid_after": cert.not_valid_after,
            "is_valid_now": (
                cert.not_valid_before <= datetime.now() <= cert.not_valid_after
            ),
        }
    except Exception as e:
        return {"error": str(e)}


# Helper: Convertir cert a base64 para envío (opcional, según API SRI)
def cert_to_base64(cert) -> str:
    """Convierte certificado X.509 a base64 (sin headers)"""
    from cryptography.x509 import Encoding
    pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
    # Eliminar headers ----BEGIN/END CERTIFICATE----
    b64 = base64.b64encode(pem).decode('utf-8')
    return b64
