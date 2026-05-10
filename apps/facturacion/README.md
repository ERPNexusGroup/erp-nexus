# Módulo Facturación Electrónica Ecuador

Módulo oficial para ERP Nexus que permite emitir, firmar y enviar facturas electrónicas al Servicio de Rentas Internas (SRI) de Ecuador.

## Características

- ✅ Generación XML según especificaciones SRI v1.0.0
- ✅ Firma digital X.509 con certificado .p12
- ✅ Envío a ambiente pruebas (1) y producción (2)
- ✅ Código único SRI (49 dígitos) automático
- ✅ Compatible con facturas (01), notas crédito (04), débito (05), guías remisión (06)
- ✅ Admin Django integrado
- ✅ API REST para integración frontend
- ✅ Logs de auditoría completos

## Instalación

```bash
cd erp-nexus
# El módulo ya está en apps/facturacion
uv run python manage.py makemigrations facturacion
uv run python manage.py migrate
```

## Configuración

### 1. Certificado Digital

Subir certificado .p12 al servidor y configurar:

```python
# settings.py o variables entorno
FACTURACION_EC_CERT_PATH = "/ruta/certificado.p12"
FACTURACION_EC_CERT_PASSWORD = "password"
SRI_AMBIENTE = 1  # 1=Pruebas, 2=Producción
```

### 2. Datos de Empresa

En admin → Companies, configurar:

- RUC (13 dígitos válido SRI)
- Razón social
- Dirección matriz
- Establecimiento (001 por defecto)
- Punto emisión (001 por defecto)

### 3. Licenciamiento

El módulo incluye sistema de licencias configurable remotamente:

| Plan | Precio | Límite | Actualizaciones |
|------|--------|---------|----------------|
| Free | $0 | 10 facturas/mes | ❌ |
| Mensual | $10/mes | Ilimitado | ✅ |
| Anual | $100/año | Ilimitado | ✅ |
| Lifetime | $3,500 (único) | Ilimitado | ✅ |
| Lifetime (sin updates) | $750 (único) | Ilimitado | ❌ |

```python
# Asignar licencia a empresa (admin)
from modules.facturacion.models import LicenseType, CompanyLicense, Company

license_type = LicenseType.objects.get(plan_id="monthly_10")
CompanyLicense.objects.create(
    company=my_company,
    license_type=license_type,
    transaction_id="txn_001",
    payment_provider="manual"
)
```

## Uso Básico

### Desde Admin Django

1. Admin → Facturación → Facturas → "Añadir factura"
2. Completar cliente, líneas
3. Guardar → estado inicia como "Pendiente"
4. Click "Enviar a SRI"

### Desde API

```bash
# Crear factura
curl -X POST http://localhost:8000/api/facturacion/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": {
      "identification_type": "05",
      "identification_number": "1791234567001",
      "name": "Cliente Ejemplo"
    },
    "lines": [
      {
        "product_code": "PROD-001",
        "quantity": 2,
        "unit_price": 100.00
      }
    ]
  }'
```

### Management Command

```bash
# Enviar todas las pendientes
uv run python manage.py send_pending_facturacion

# Envío dry-run (ver qué se enviaría)
uv run python manage.py send_pending_facturacion --dry-run

# Límite de 10 facturas por ejecución
uv run python manage.py send_pending_facturacion --limit=10
```

## Cron (Automatización)

```bash
# Cada 5 minutos
*/5 * * * * cd /ruta/erp-nexus && uv run python manage.py send_pending_facturacion --limit=20
```

## Validaciones

- RUC (13 dígitos) con algoritmo módulo 10
- Cédula (10 dígitos) módulo 10
- Totales línea vs subtotal factura
- Formato XML contra XSD
- Firma digital válida

## Estructura de Archivos

```
apps/facturacion/
├── __meta__.py           # Metadata (nexus CLI)
├── models.py             # Modelos Django
├── admin.py              # Admin integrado
├── api/routes.py         # Endpoints REST
├── services/             # Lógica de negocio
│   ├── xml_generator.py
│   ├── digital_signature.py
│   ├── sri_client.py
│   ├── code_unique.py
│   ├── validator.py
│   └── facturation_integration.py
├── management/commands/send_pending_facturacion.py
└── tests/                # Suite de tests
```

## Development

```bash
cd erp-nexus
uv sync
uv run pytest apps/facturacion/tests/ -v

# Generar migraciones
uv run python manage.py makemigrations facturacion
uv run python manage.py migrate
```

## Especificaciones Técnicas SRI

| Campo | Valor |
|-------|-------|
| Ambiente pruebas | https://celcer.sri.gob.ec/... |
| Ambiente producción | https://cel.sri.gob.ec/... |
| Formato XML | UTF-8, versión 1.0.0 |
| Algoritmo firma | RSA-SHA256 |
| Codificación | Base64 para envío SOAP |
| Tamaño máximo factura | ~50KB XML |

## Próximas Features

- [ ] Modelo de impuestos (IVA, ICE, IR) por producto
- [ ] Reporte ATS (Anexo Transaccional Simplificado)
- [ ] Anulación de facturas (SRI)
- []#endif Watermark PDF autorizado
- [ ] Múltiples establecimientos/ puntos emisión
- [ ] Retenciones automáticas (compras)
- [ ] Exportación contabilidad (formato SRI 103/104)

## Soporte

- 📧 contact@erpnexus.ec
- 🐛 Issues: https://github.com/ERPNexusGroup/facturacion/issues
- 📖 Documentación: `/docs/` en repo

## Licencia

MIT License - ver LICENSE en repositorio principal.

---

**ERP Nexus Group** · 2024-2026
