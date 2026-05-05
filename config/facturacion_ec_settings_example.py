# Configuración SRI para facturacion_ec
# Colocar en settings.py o como variables entorno

# Ruta al certificado digital .p12 (o .pfx)
FACTURACION_EC_CERT_PATH = "/ruta/a/tu/certificado.p12"

# Password del certificado
FACTURACION_EC_CERT_PASSWORD = "tu_password"

# Ambiente: 1 = Pruebas (SRI testing), 2 = Producción
SRI_AMBIENTE = 1

# URLs SRI (no modificar a menos que SRI cambie endpoints)
SRI_RECEPTION_URL = {
    1: "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl",
    2: "https://prepro Rees/RecepcionComprobantesOffline?wsdl",
}

# Timeout en segundos para llamadas SRI
SRI_TIMEOUT = 30

# Retry policy (intentos antes de fallar)
SRI_MAX_RETRIES = 3
