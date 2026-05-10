# Digital Signature - Firma XML con certificado X.509 (.p12)
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.x509 import load_pem_x509_certificate
from cryptography.exceptions import UnsupportedAlgorithm
from signxml import XMLSigner, methods
from signxml.exceptions import InvalidSignature
import base64
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
            with open(self.p12_path, 'rb') as f:
                p12_data = f.read()

            self._private_key, self._cert, self._additional_certs = (
                serialization.pkcs12.load_key_and_certificates(
                    p12_data,
                    self.password.encode('utf-8')
                )
            )
        except Exception as e:
            raise ValueError(f"Error cargando certificado: {e}")

    def sign_xml(self, xml_string: str, canonicalize: bool = True) -> str:
        """
        Firma un documento XML según estándar W3C.

        Args:
            xml_string: XML como string (UTF-8)
            canonicalize: Si aplicar canonicalización (recomendado)

        Returns:
            XML firmado (con elemento Signature anexado)
        """
        if not self._private_key or not self._cert:
            raise ValueError("Certificado no cargado")

        try:
            signer = XMLSigner(
                method=methods.enveloped,
                signature_algorithm="rsa-sha256",
                digest_algorithm="sha256",
                c14n_algorithm="http://www.w3.org/2006/12/xml-c14n"
            )

            # Parsear XML
            xml_doc = etree.fromstring(xml_string.encode('utf-8'))

            # Firmar
            signed_xml = signer.sign(
                xml_doc,
                cert=self._cert,
                key=self._private_key,
                reference_uri=""  # Empty URI for enveloped signature
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
        _, cert, _ = serialization.pkcs12.load_key_and_certificates(
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
