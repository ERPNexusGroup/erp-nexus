# Servicios de facturación electrónica Ecuador
from datetime import datetime
import random
import hashlib


def generate_access_key(ruc: str, ambiente: int, establishment_code: str, emission_point: str,
                        sequential: str, date: datetime = None,
                        cod_doc: str = "01", tipo_emision: str = "1") -> str:
    """
    Genera la clave de acceso única del SRI Ecuador (49 dígitos).

    Formato oficial SRI:
      [08] Fecha emisión           YYYYMMDD
      [02] Código documento        ej. 01/Factura, 04/NC, 05/ND
      [13] RUC (13 dígitos)
      [03] Código ambiente         001=pruebas, 002=producción
      [03] Código establecimiento  3 dígitos
      [03] Código punto emisión    3 dígitos
      [09] Número secuencial       9 dígitos
      [01] Tipo de emisión         1=Normal, 2=Contingencia
      [08] Código numérico aleatorio (8 dígitos)
      [01] Dígito verificador      checksum mód 10
      --- Total: 49 dígitos ---

    Args:
        ruc: RUC emisor (13 dígitos)
        ambiente: 1=Pruebas, 2=Producción
        establishment_code: Código establecimiento (2-3 dígitos)
        emission_point: Código punto emisión (3 dígitos)
        sequential: Secuencial de factura (9 dígitos o convertible)
        date: Fecha emisión
        cod_doc: Código documento SRI (01,04,05,06,07)
        tipo_emision: 1=Normal, 2=Contingencia

    Returns:
        Clave de acceso de 49 dígitos
    """
    if date is None:
        date = datetime.now()

    # 1. Fecha emisión (8)
    date_str = date.strftime('%Y%m%d')

    # 2. Código documento (2)
    cod_doc = str(cod_doc).zfill(2)[:2]

    # 3. RUC (13)
    ruc_clean = str(ruc).replace('-', '').replace(' ', '').zfill(13)[:13]

    # 4. Ambiente (3) — SRI usa 001 para pruebas, 002 para producción
    amb_code = '001' if ambiente == 1 else '002'

    # 5. Establecimiento (3)
    estab = str(establishment_code).zfill(3)[:3]

    # 6. Punto emisión (3)
    pto = str(emission_point).zfill(3)[:3]

    # 7. Secuencial (9)
    seq = str(sequential).zfill(9)[:9]

    # 8. Tipo emisión (1) — 1=Normal
    tipo_em = str(tipo_emision)[:1]

    # 9. Código aleatorio (8 dígitos)
    random_part = str(random.randint(0, 99999999)).zfill(8)

    # 10. Dígito verificador (mód 10 sobre la concatenación sin el random)
    base = date_str + cod_doc + ruc_clean + amb_code + estab + pto + seq + tipo_em
    digito_verificador = str(sum(int(d) for d in base) % 10)

    clave = base + random_part + digito_verificador
    assert len(clave) == 49, f"Clave debe tener 49 dígitos, tiene {len(clave)}"
    return clave


def validate_access_key(access_key: str) -> bool:
    """Valida formato de clave de acceso SRI (49 dígitos numéricos)."""
    return bool(access_key and access_key.isdigit() and len(access_key) == 49)


def generate_invoice_number(establishment: str, emission_point: str, sequential: int) -> str:
    """
    Genera número de factura formato: 001-001-000000001

    Args:
        establishment: Código establecimiento (3 dígitos)
        emission_point: Código punto emisión (3 dígitos)
        sequential: Número secuencial

    Returns:
        String formato "XXX-XXX-XXXXXXXXX"
    """
    est = str(establishment).zfill(3)[:3]
    pto = str(emission_point).zfill(3)[:3]
    seq = str(sequential).zfill(9)
    return f"{est}-{pto}-{seq}"


def parse_invoice_number(number: str):
    """
    Parsea número de factura 001-001-000000001

    Returns:
        Tuple: (establishment, emission_point, sequential)
    """
    parts = number.split("-")
    if len(parts) != 3:
        raise ValueError("Formato inválido. Esperado: XXX-XXX-XXXXXXXXX")
    return parts[0], parts[1], parts[2]


def get_next_sequential(company, establishment_code, emission_point, tipo_comprobante="01"):
    """
    Obtiene el siguiente número secuencial para una factura.

    Busca la última factura del mismo tipo, establecimiento, punto emisión
    y devuelve secuencial + 1.

    Args:
        company: Instancia Company
        establishment_code: Código establecimiento (2-3 dígitos)
        emission_point: Código punto emisión (3 dígitos)
        tipo_comprobante: Código SRI (01, 04, 05, 06)

    Returns:
        int: Siguiente secuencial (1 si no hay anteriores)
    """
    from .models import Invoice, SriTipoComprobante
    try:
        tipo = SriTipoComprobante.objects.get(code=tipo_comprobante)
    except SriTipoComprobante.DoesNotExist:
        tipo = None

    last = Invoice.objects.filter(
        company=company,
        tipo_comprobante=tipo
    ).order_by("-number").first()

    if last:
        _, _, last_seq_str = parse_invoice_number(last.number)
        last_seq = int(last_seq_str)
        return last_seq + 1
    return 1


def get_next_sequential_for_invoice(company) -> str:
    """
    Wrapper que devuelve secuencial formateado a 9 dígitos.
    Usa empresa desde settings o company. Por ahora usa 001-001.
    """
    from django.conf import settings
    seq_int = get_next_sequential(
        company=company,
        establishment_code=getattr(settings, 'ESTABLISHMENT_CODE', '001'),
        emission_point=getattr(settings, 'EMISSION_POINT_CODE', '001'),
        tipo_comprobante='01'
    )
    return str(seq_int).zfill(9)
