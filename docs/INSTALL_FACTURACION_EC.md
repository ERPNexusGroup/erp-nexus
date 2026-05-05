# INSTALACIÓN Y CONFIGURACIÓN — Módulo facturacion_ec
## ERP Nexus + Facturación Electrónica Ecuador

---

## 📋 ÍNDICE

1. [Requisitos](#requisitos)
2. [Instalación ERP Base](#instalación-erp-base)
3. [Instalación Módulo](#instalación-módulo)
4. [Configuración Inicial](#configuración-inicial)
5. [Pruebas](#pruebas)
6. [Configuración SRI (Certificado)](#configuración-sri-certificado)
7. [Envío a SRI](#envió-a-sri)
8. [Troubleshooting](#troubleshooting)

---

## 📋 REQUISITOS

### Software
- **Python** ≥ 3.11
- **uv** — gestor de paquetes (https://astral.sh/uv)
- **Git**
- **SQLite** (incluido en Python)

### Librerías externas (instaladas automáticamente por setup)
- `jinja2` — generación XML
- `lxml` — parseo/validación XML
- `signxml` — firma digital XML (cryptography backend)
- `httpx` — llamadas HTTP a SRI webservice
- `cryptography` — manejo certificados .p12/.pfx

### Certificado digital SRI (para envío real)
- Certificado `.p12` o `.pfx` (obtenido de https://celcer.sri.gob.ec/)
- Password del certificado
- **Ambiente pruebas** → no necesitas facturar, solo validar XML

---

## 🚀 INSTALACIÓN ERP BASE

```bash
# 1. Clonar ERP Nexus
git clone https://github.com/ERPNexusGroup/erp-nexus.git
cd erp-nexus

# 2. Instalar dependencias (uv crea .venv automáticamente)
uv sync

# 3. Aplicar migraciones core
uv run python manage.py migrate

# 4. Crear superusuario
uv run python manage.py createsuperuser
#   Username: admin
#   Email: admin@erpnexus.ec
#   Password: (elige uno seguro)

# 5. Verificar ERP funciona SIN módulos
uv run python manage.py check
# → System check identified no issues

# 6. Levantar servidor
uv run python manage.py runserver
# → http://localhost:8000/admin
```

**✅ Verificación:**
```bash
# Sin módulos (modules_enabled.py vacío)
cat erp_nexus/modules_enabled.py
# Debe mostrar: MODULE_APPS = []

# Installed apps en runtime
uv run python manage.py shell -c "
from django.conf import settings
mods = [a for a in settings.INSTALLED_APPS if 'facturacion' in a]
print('facturacion_ec cargado?', bool(mods))
"
# Debe mostrar: False
```

---

## 📦 INSTALACIÓN MÓDULO facturacion_ec

### Opción A — Automática (recomendada)

El módulo ya está en `modules/facturacion_ec/`. Solo falta **activarlo**:

```bash
# 1. Registrar en catálogo (ModuleCatalogItem)
uv run python manage.py register_facturacion_ec

# 2. Activar módulo (EnabledModule)
uv run python manage.py shell -c "
from apps.core_marketplace.models import EnabledModule
EnabledModule.objects.get_or_create(
    technical_name='facturacion_ec',
    defaults={'django_app': 'modules.facturacion_ec', 'status': 'active'}
)
print('✅ Módulo activado')
"

# 3. Generar modules_enabled.py
uv run python manage.py apply_modules

# O usa el comando unificado:
uv run python manage.py module_install modules/facturacion_ec
```

**Salida esperada:**
```bash
📦 Instalando módulo: Facturación Electrónica Ecuador v0.1.0
   Technical name: facturacion_ec
   Django app: modules.facturacion_ec
✅ Catálogo: Actualizado
✅ modules_enabled.py actualizado
🎉 Módulo instalado!
```

### Opción B — Script todo-en-uno

```bash
./setup_complete.sh
# Este script hace:
# - Instala dependencias
# - Migraciones core
# - Crea superusuario si no existe
# - Instala facturacion_ec
# - Aplica migraciones
# - Configura 5 LicenseTypes
# - Verifica carga del módulo
```

---

## 🔄 VERIFICACIÓN INSTALACIÓN

```bash
# 1. modules_enabled.py debe incluir el módulo
cat erp_nexus/modules_enabled.py
# OUTPUT:
# MODULE_APPS = [
#     "modules.facturacion_ec",
# ]

# 2. Django check debe estar OK
uv run python manage.py check
# OUTPUT: System check identified no issues (0 silenced)

# 3. Módulo en INSTALLED_APPS
uv run python manage.py shell -c "
from django.conf import settings
print('facturacion_ec en INSTALLED_APPS:', 'modules.facturacion_ec' in settings.INSTALLED_APPS)
"
# OUTPUT: True

# 4. Migraciones aplicadas
uv run python manage.py showmigrations facturacion_ec
# Todas las migraciones deben tener [X]
```

---

## ⚙️ CONFIGURACIÓN INICIAL

### Paso 1 — Crear Company de prueba

```bash
uv run python manage.py shell
```

```python
from apps.core_companies.models import Company
from django.contrib.auth import get_user_model

User = get_user_model()
admin = User.objects.filter(is_superuser=True).first()

company = Company.objects.create(
    slug="demo-ecuador-sa",
    name="Demo Ecuador SA",
    ruc="1791234567001",           # RUC válido (algoritmo mód 10)
    tax_id="1791234567001",
    address="Av. Amazonas N34-56, Quito, Ecuador",
    phone="+593 2 555 1234",
    email="demo@demo-ec.com",
    establishment_code="001",      # 3 dígitos
    point_emission_code="001",     # 3 dígitos
)
print(f"✅ Company: {company.name} [{company.ruc}]")
```

### Paso 2 — Vincular Company a Usuario (Membership)

```python
from apps.core_companies.models import Membership

membership = Membership.objects.create(
    user=admin,
    company=company,
    role="owner",
    is_owner=True,
    status="active",
)
print(f"✅ Membership: {admin.username} → {company.name}")
```

### Paso 3 — Verificar LicenseTypes (5 planes)

Los LicenseTypes se crean automáticamente vía signal o seed:

```python
from modules.facturacion_ec.models import LicenseType

for lt in LicenseType.objects.all():
    print(f"  • {lt.plan_id}: {lt.display_name}")
```

**Planes esperados:**
```
• free:        Free (10 facturas/mes)
• monthly_10:  Plan Mensual $10/mes
• yearly_100:  Plan Anual $100/año
• lifetime_3500: Lifetime + Updates $3,500
• lifetime_750:  Lifetime (sin updates) $750
```

### Paso 4 — Asignar licencia Free a Company

```python
from modules.facturacion_ec.models import CompanyLicense, LicenseType

lt_free = LicenseType.objects.get(plan_id="free")
license_obj = CompanyLicense.objects.create(
    company=company,
    license_type=lt_free,
    is_active=True,
)
print(f"✅ Licencia asignada: {license_obj}")
```

---

## 🧪 PRUEBAS (sin certificado SRI)

Ejecuta el test completo incluido:

```bash
uv run python test_facturacion_ec.py
```

**Lo que prueba:**
1. ✅ Company creada/obtenida
2. ✅ Membership usuario → Company
3. ✅ LicenseType Free existente
4. ✅ CompanyLicense asignada
5. ✅ Customer de prueba creado
6. ✅ Product de prueba creado
7. ✅ SriTipoComprobante "01" existe
8. ✅ Invoice creada con número y access_key
9. ✅ InvoiceLine enlazada
10. ✅ Totales coinciden ($224.00)
11. ✅ XML Generator produce XML válido (1926 bytes)

**Salida esperada:**
```
============================================================
  ✅ TEST COMPLETO — Módulo facturacion_ec operativo
============================================================
📊 Datos creados:
   • Company: Demo Ecuador SA [1791234567001]
   • Customer: Cliente Demo [1750234556]
   • Product: DEMO-001 - Producto Demo
   • Invoice: #001-001-000000001 | Total: $224.0
   • LicenseType: Free (10 facturas/mes)
```

---

## 🔐 CONFIGURACIÓN SRI (CERTIFICADO DIGITAL)

### Paso 1 — Obtener certificado de pruebas

1. Registrarse en https://celcer.sri.gob.ec/
2. Ir a **Servicios en línea → Certificados → Solicitar certificado de prueba**
3. Descargar archivo `.p12` o `.pfx`
4. Anotar el **password** del certificado

### Paso 2 — Configurar settings.py o variables entorno

**Opción A — settings.py (development):**

```python
# erp_nexus/settings.py — al final del archivo
FACTURACION_EC = {
    "CERT_PATH": "/home/wcun/certs/facturacion_pruebas.p12",
    "CERT_PASSWORD": "tu_password",
    "SRI_AMBIENTE": 1,  # 1=Pruebas, 2=Producción
    "ESTABLECIMIENTO_DEFAULT": "001",
    "PUNTO_EMISION_DEFAULT": "001",
}
```

**Opción B — Variables entorno (.env):**

```bash
# ~/.bashrc, ~/.zshrc o archivo .env del proyecto
export FACTURACION_CERT_PATH="/ruta/completa/certificado.p12"
export FACTURACION_CERT_PASSWORD="tu_password"
export SRI_AMBIENTE=1
```

settings.py ya lee estas variables:
```python
FACTURACION_EC = {
    "CERT_PATH": os.getenv("FACTURACION_CERT_PATH", ""),
    "CERT_PASSWORD": os.getenv("FACTURACION_CERT_PASSWORD", ""),
    "SRI_AMBIENTE": int(os.getenv("SRI_AMBIENTE", "1")),
    ...
}
```

### Paso 3 — Reiniciar servidor Django

```bash
# Si tienes runserver corriendo:
Ctrl+C
uv run python manage.py runserver
```

---

## 📤 ENVÍO A SRI

### Envío manual desde Django shell

```bash
uv run python manage.py shell
```

```python
from modules.facturacion_ec.models import Invoice
from modules.facturacion_ec.services import send_invoice_to_sri

# Obtener factura pendiente
inv = Invoice.objects.filter(sri_status="pending").first()
if not inv:
    print("No hay facturas pendientes")
else:
    result = send_invoice_to_sri(inv.id)
    print(f"Resultado: {result}")

    # Recargar factura
    inv.refresh_from_db()
    print(f"Estado SRI: {inv.sri_status}")
    print(f"Mensaje: {inv.sri_message[:200]}")
```

### Envío automático (cron o comando management)

```bash
# Enviar todas las facturas pendientes
uv run python manage.py send_pending_facturacion
```

**El comando:**
1. Busca invoices con `sri_status="pending"`
2. Para cada una:
   - Genera XML (si no existe)
   - Firma con certificado .p12
   - Envía POST a SRI (ambiente 1 o 2)
   - Guarda respuesta en `SRISendLog`
   - Actualiza `sri_status` y `sri_message`

### Ver logs de envío

```bash
uv run python manage.py shell -c "
from modules.facturacion_ec.models import SRISendLog
for log in SRISendLog.objects.all().order_by('-timestamp')[:5]:
    print(f'{log.timestamp} | {log.response_code} | {log.invoice.number}')
"
```

---

## 🗃️ BASE DE DATOS — TABLAS FACTURACION_EC

```sql
-- Catálogos SRI (deben precargarse)
facturacion_ec_sriambiente           -- 1=Pruebas, 2=Prod
facturacion_ec_sritipocomprobante    -- 01=Factura, 04=NC, 05=ND
facturacion_ec_sriimpuesto           -- 2=IVA, 3=ICE, 5=IRBP
facturacion_ec_sricodigoexento       -- Códigos exentos IVA

-- Maestros
facturacion_ec_licensetype           -- 5 planes
facturacion_ec_companylicense        -- Licencia por empresa
facturacion_ec_customer              -- Clientes (máx 1 por company)
facturacion_ec_product               -- Productos (código único por company)

-- Transaccional
facturacion_ec_invoice               -- Factura principal (clave acceso única)
facturacion_ec_invoiceline           -- Líneas (cantidad × precio)
facturacion_ec_electronicdocument    -- Documentos XML guardados
facturacion_ec_srisendlog            -- Log de envíos a SRI
```

---

## 🎯 FLUJO COMPLETO RESUMIDO

```
1. ERP base → migrate → check → OK
2. Instalar módulo → module_install → modules_enabled.py
3. Company + Membership → empresa vinculada a usuario
4. LicenseType seed → plan gratis Free asignado
5. Customer + Product → datos para factura
6. SriTipoComprobante(01) → tipo factura
7. Invoice + InvoiceLine → generanumero + access_key
8. XMLGenerator → XML firmable (sin certificado aún)
9. Configurar CERT_PATH + CERT_PASSWORD
10. send_invoice_to_sri() o send_pending_facturacion
11. SRISendLog → respuesta SRI almacenada
12. Invoice.sri_status → "accepted" / "rejected"
```

---

## 🐛 TROUBLESHOOTING

### Error: "modules.facturacion_ec has no migrations"
```bash
uv run python manage.py makemigrations facturacion_ec
uv run python manage.py migrate
```

### Error: "Foreign key constraint failed" al crear Invoice
```bash
# Asegurar dependencias primero:
uv run python manage.py shell -c "
from modules.facturacion_ec.models import SriTipoComprobante
SriTipoComprobante.objects.get_or_create(code='01', defaults={'name':'Factura'})
"
```

### Error: "guia_remision_number no existe" en XMLGenerator
```bash
# Ya corregido: agregamos campo guia_remision_number a Invoice
# Si persiste: makemigrations + migrate facturacion_ec
```

### Error: XMLGenerator "line.discount no existe"
```bash
# Ya corregido: agregamos campo discount a InvoiceLine
# makemigrations + migrate facturacion_ec
```

### Módulo no carga después de instalar
```bash
# 1. Verificar EnabledModule
uv run python manage.py shell -c "
from apps.core_marketplace.models import EnabledModule
print(list(EnabledModule.objects.values()))
"

# 2. Verificar modules_enabled.py
cat erp_nexus/modules_enabled.py

# 3. Forzar regeneración
uv run python manage.py apply_modules

# 4. Reiniciar servidor Django (Ctrl+C y runserver de nuevo)
```

### XML no incluye claveAcceso
```bash
# Verificar plantilla en xml_generator.py:
# infoTributaria.claveAcceso → debe ser {{ invoice.access_key }}
# Si no aparece, asegurar que Invoice.access_key está seteado
```

### "Certificate not found" al enviar a SRI
```bash
# 1. Verificar ruta del certificado
ls -la /ruta/a/tu/certificado.p12

# 2. Verificar settings.FACTURACION_EC
uv run python manage.py shell -c "
from django.conf import settings
print(settings.FACTURACION_EC)
"

# 3. Configurar variable entorno
export FACTURACION_CERT_PATH="/ruta/certificado.p12"
export FACTURACION_CERT_PASSWORD="password"
```

### "Tipo comprobante no existe"
```bash
# Pre-cargar catálogo SRI
uv run python manage.py shell -c "
from modules.facturacion_ec.models import SriTipoComprobante
SriTipoComprobante.objects.get_or_create(code='01', defaults={'name':'Factura'})
SriTipoComprobante.objects.get_or_create(code='04', defaults={'name':'Nota de Crédito'})
SriTipoComprobante.objects.get_or_create(code='05', defaults={'name':'Nota de Débito'})
"
```

---

## 📁 ARCHIVOS DE CONFIGURACIÓN

| Archivo | Propósito |
|---------|-----------|
| `erp_nexus/settings.py` | `FACTURACION_EC` dict con config SRI |
| `erp_nexus/modules_enabled.py` | **Auto-generado** — lista MODULE_APPS |
| `modules/facturacion_ec/__meta__.py` | Metadata del módulo (parser AST) |
| `setup_complete.sh` | Instalador todo-en-uno |
| `test_facturacion_ec.py` | Test end-to-end (sin SRI) |
| `docs/INSTALL.md` | Guía instalación (este archivo es resumen) |

---

## 🎯 PRÓXIMOS PASOS INMEDIATOS

1. **Ahora** — Probar en admin: http://localhost:8000/admin
   - App "Facturación Electrónica Ecuador"
   - Crear Company, Customer, Product manualmente
   - Ver LicenseTypes

2. **Hoy** — Obtener certificado SRI pruebas
   - Registrar en https://celcer.sri.gob.ec/
   - Descargar `.p12`

3. **Hoy** — Configurar certificado en `settings.py`

4. **Mañana** — Probar envío 1 factura a SRI ambiente pruebas
   ```bash
   uv run python manage.py send_pending_facturacion
   ```

5. **Próxima semana** — Validación XSD completa
   - Comparar XML generado contra XSD oficial SRI
   - Ajustar campos faltantes (`infoAdicional`, `campoAdicional`)

6. **Siguiente** — API REST
   - Endpoints GET/POST facturas
   - Autenticación token

---

## 📚 DOCUMENTACIÓN ADICIONAL

- `modules/facturacion_ec/README.md` — Docs técnicas módulo
- `ERP_NEXUS_BUSINESS_PLAN.md` — Modelo negocio + pricing
- `ERP_NEXUS_ESTADO_ACTUAL.md` — Checklist estado actual
- `docs/ARCHITECTURE_PLAN.md` — Arquitectura general ERP

---

## ✅ CHECKLIST PRE-SRI

Antes de intentar envío a SRI, verifica:

- [x] ERP base levanta sin errores
- [x] Módulo facturacion_ec instalado y activo
- [x] Company creada con RUC válido
- [x] Membership vincula usuario → Company
- [x] LicenseType Free asignada
- [x] Customer + Product creados
- [x] SriTipoComprobante "01" existe
- [x] Invoice generada con access_key correcta
- [x] InvoiceLine con totals correctos
- [x] XML Generator produce XML (1926+ bytes)
- [ ] Certificado .p12 obtenido
- [ ] FACTURACION_EC_CERT_PATH configurado
- [ ] FACTURACION_EC_CERT_PASSWORD configurado
- [ ] SRI_AMBIENTE = 1 (pruebas)
- [ ] Puerto 8000 accesible (no bloqueado por firewall)

**Una vez todo checklist ✅ → ejecutar:**
```bash
uv run python manage.py send_pending_facturacion
```

---

## 🆘 CONTACTO Y SOPORTE

- **GitHub Issues:** https://github.com/ERPNexusGroup/erp-nexus/issues
- **Documentación:** `docs/` + `modules/facturacion_ec/README.md`
- **Comunidad:** https://discord.gg/erp-nexus (enlace pendiente)

---

**Estado actual:** 🟢 Módulo instalado y probado (XML generation OK). Pendiente certificado SRI para envío real.

**Última actualización:** 2026-05-05
