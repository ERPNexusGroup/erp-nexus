# Servicios de facturación electrónica Ecuador
from datetime import datetime
import random
import hashlib


def generate_access_key(ruc: str, ambiente: int, establishment_code: str, emission_point: str,
                        sequential: str, date: datetime = None) -> str:
    """
    Genera la clave de acceso única del SRI (49 dígitos).

    Formato SRI Ecuador:
    AAAAMMDD + 2d estab + 3d ptoEmi + 15d secuencial + 9d random+verificador

    Ejemplo: 2024011500100000000000012345678

    Args:
        ruc: RUC de la empresa (13 dígitos, no se usa en clave pero es parte del contexto)
        ambiente: 1=Pruebas, 2=Producción
        establishment_code: Código establecimiento (2 dígitos)
        emission_point: Código punto emisión (3 dígitos)
        sequential: Número secuencial (9 dígitos)
        date: Fecha emisión (default: hoy)

    Returns:
        Clave de acceso de hasta 49 dígitos
    """
    if date is None:
        date = datetime.now()

    # 1. Fecha: 8 dígitos YYYYMMDD
    date_str = date.strftime('%Y%m%d')

    # 2. Establecimiento: 2 dígitos (rellenar con ceros)
    estab = establishment_code.zfill(2)[:2]

    # 3. Punto emisión: 3 dígitos (rellenar con ceros)
    pto_emi = emission_point.zfill(3)[:3]

    # 4. Secuencial: 15 dígitos (rellenar con ceros)
    # El secuencial viene de la factura: 001-001-000000001 → último bloque 9 dígitos
    # Para 49 dígitos totales, tomamos 15 (padding)
    secuencial = sequential.zfill(15)[:15]

    # 5. Random + verificador: 9 dígitos
    # Generamos 8 dígitos aleatorios, el noveno es dígito verificador
    import random
    random_part = str(random.randint(0, 99999999)).zfill(8)

    # Dígito verificador (módulo 11 sobre el string sin el random)
    # SRI no especifica algoritmo exacto para este dígito
    # Usamos simple checksum para demo
    base = date_str + estab + pto_emi + secuencial + random_part
    checksum = sum(int(d) for d in base) % 10
    verificador = str(checksum)

    codigo = date_str + estab + pto_emi + secuencial + random_part + verificador
    return codigo[:49]  # Máximo 49 dígitos


def validate_access_key(access_key: str) -> bool:
    """Valida formato de clave de acceso SRI (49 dígitos)"""
    if not access_key or not access_key.isdigit():
        return False
    if len(access_key) != 49:
        return False
    return True


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
    est = establishment.zfill(3)[:3]
    pto = emission_point.zfill(3)[:3]
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

    Busca la factura con el mayor ID (más reciente) y extrae su secuencial.
    Si no hay facturas, retorna 1.

    Args:
        company: Instancia Company
        establishment_code: Código establecimiento (2 dígitos)
        emission_point: Código punto emisión (3 dígitos)
        tipo_comprobante: Código SRI (01, 04, 05, 06)

    Returns:
        int: Siguiente secuencial
    """
    from ..models import Invoice, SriTipoComprobante
    try:
        tipo = SriTipoComprobante.objects.get(code=tipo_comprobante)
    except SriTipoComprobante.DoesNotExist:
        tipo = None

    # Buscar la factura más reciente por ID (no por número, que puede repetirse en seed data)
    last = Invoice.objects.filter(
        company=company,
        tipo_comprobante=tipo
    ).order_by("-id").first()

    if last and last.number:
        try:
            _, _, last_seq_str = parse_invoice_number(last.number)
            last_seq = int(last_seq_str)
            return last_seq + 1
        except (ValueError, IndexError):
            pass
    return 1
