# INSTALACIÓN — ERP Nexus + Módulo facturacion_ec

## 📋 Requisitos previos

- Python 3.11 o superior
- `uv` instalado (gestor de paquetes)
- Git
- (Opcional) Certificado digital .p12 para pruebas SRI

---

## 🚀 Paso 1 — Clonar y levantar ERP Base (sin módulos)

```bash
# 1. Clonar ERP Nexus core
git clone https://github.com/ERPNexusGroup/erp-nexus.git
cd erp-nexus

# 2. Instalar dependencias
uv sync

# 3. Aplicar migraciones core
uv run python manage.py migrate

# 4. Crear superusuario
uv run python manage.py createsuperuser --username admin --email admin@erpnexus.ec

# 5. Levantar servidor
uv run python manage.py runserver
```

**Acceso:**
- URL: http://localhost:8000/admin
- User: admin
- Pass: (el que configuraste)

**Verificar:**
- [ ] Admin carga correctamente
- [ ] Menú izquierdo muestra apps core (auth, companies, users, etc.)
- [ ] NO aparece "Facturación Electrónica Ecuador" aún (módulo no instalado)

---

## 📦 Paso 2 — Instalar módulo facturacion_ec

### Opción A: Usando comando `module_install` (recomendado)

```bash
# El módulo ya está en modules/facturacion_ec
uv run python manage.py module_install modules/facturacion_ec
```

Salida esperada:
```
📦 Instalando módulo: Facturación Electrónica Ecuador v0.1.0
   Technical name: facturacion_ec
   Django app: modules.facturacion_ec
✅ Catálogo: Actualizado
✅ modules_enabled.py actualizado
🎉 Módulo instalado!
```

### Opción B: Manual (para debug)

```bash
# 1. Registrar en catálogo (ModuleCatalogItem)
uv run python manage.py register_facturacion_ec

# 2. Crear EnabledModule
uv run python manage.py shell -c "
from apps.core_marketplace.models import EnabledModule
EnabledModule.objects.get_or_create(
    technical_name='facturacion_ec',
    defaults={'django_app': 'modules.facturacion_ec', 'status': 'active'}
)
"

# 3. Generar modules_enabled.py
uv run python manage.py apply_modules
```

---

## 🔄 Paso 3 — Aplicar migraciones del módulo

```bash
# Generar y aplicar migraciones facturacion_ec
uv run python manage.py makemigrations facturacion_ec
uv run python manage.py migrate
```

**Output esperado:**
```
Migrations for 'facturacion_ec':
  apps/facturacion/migrations/0001_initial.py
    - Create model LicenseType
    - Create model Customer
    - Create model Product
    - Create model Invoice
    ...
Operations to perform:
  Apply all migrations... OK
```

---

## ✅ Paso 4 — Verificar instalación

1. **Reiniciar servidor** (Ctrl+C y `uv run python manage.py runserver`)

2. **Login admin:** http://localhost:8000/admin

3. **Verificar:**
   - [ ] Menú izquierdo muestra sección "Facturación Electrónica Ecuador"
   - [ ] Submenús: Facturas, Clientes, Productos, Licencias, Catalogos SRI
   - [ ] En "Core → Module Catalog": `facturacion_ec` aparece Activo
   - [ ] En "Core → Enabled Modules": `facturacion_ec` listado

4. **Probar CRUD:**
   - Crear un Cliente ( Customer )
   - Crear un Producto ( Product )
   - Ver listado LicenseType (5 planes preconfigurados)

---

## ⚙️ Paso 5 — Configuración inicial (SRI)

### 5.1 Crear Company de prueba

```bash
uv run python manage.py shell
```

```python
from apps.core_companies.models import Company
c = Company.objects.create(
    name="Demo Ecuador SA",
    ruc="1791234567001",  # RUC válido (algoritmo mód 10)
    slug="demo-ecuador-sa"
)
print(f"Company creada: {c.name} RUC: {c.ruc}")
```

### 5.2 Configurar certificado SRI (opcional para pruebas)

El módulo funciona SIN certificado, pero para enviar a SRI necesitas:

1. **Obtener certificado de pruebas:**
   - Registrarse en https://celcer.sri.gob.ec/
   - Descargar certificado `.p12`
   - Anotar password

2. **Configurar en `settings.py` o variables entorno:**

```python
# settings.py
FACTURACION_EC = {
    "CERT_PATH": "/ruta/completa/certificado.p12",
    "CERT_PASSWORD": "tu_password",
    "SRI_AMBIENTE": 1,  # 1=Pruebas, 2=Producción
}
```

O variables entorno:
```bash
export FACTURACION_CERT_PATH=/path/to/cert.p12
export FACTURACION_CERT_PASSWORD=password
export SRI_AMBIENTE=1
```

---

## 🧪 Paso 6 — Probar flujo completo (con certificado)

```bash
# 1. Crear factura desde Django shell
uv run python manage.py shell
```

```python
from datetime import date
from django.contrib.auth import get_user_model
from modules.facturacion_ec.models import Customer, Product, Invoice, InvoiceLine
from apps.core_companies.models import Company

# Datos
User = get_user_model()
user = User.objects.first()
company = Company.objects.first()

# Cliente
cust = Customer.objects.create(
    company=company,
    identification_type="05",  # Cédula
    identification_number="1750234556",
    name="Cliente de Prueba",
    address="Quito, Ecuador"
)

# Producto
prod = Product.objects.create(
    company=company,
    code="PROD-001",
    name="Producto Demo",
    unit_price=100.00,
    tax_percent=12.00
)

# Factura
inv = Invoice.objects.create(
    company=company,
    number="001-001-000000001",
    date=date.today(),
    customer=cust,
    ambiente=1,  # Pruebas
    created_by=user
)

# Línea
line = InvoiceLine.objects.create(
    invoice=inv,
    product=prod,
    quantity=2,
    unit_price=100.00,
    subtotal=200.00,
    tax_rate=12.00,
    tax_amount=24.00,
    total=224.00
)

# Calcular totales
inv.subtotal = sum(l.subtotal for l in inv.lines.all())
inv.tax_total = sum(l.tax_amount for l in inv.lines.all())
inv.total = inv.subtotal + inv.tax_total
inv.save()

print(f"✅ Factura creada: {inv.number} - Total: ${inv.total}")
print(f"   Access key (generada automáticamente?): {inv.access_key or 'Pendiente'}")
```

### 6.1 Generar XML y firmar (sin enviar)

```python
from modules.facturacion_ec.services import XMLGenerator, DigitalSigner
from lxml import etree

# Generar XML
gen = XMLGenerator(company)
xml = gen.generate(inv, list(inv.lines.all()))
print("✅ XML generado:")
print(xml[:500] + "...")

# Si tienes certificado:
# signer = DigitalSigner("/ruta/cert.p12", "password")
# xml_signed = signer.sign_xml(xml)
# print("✅ XML firmado")
```

### 6.2 Enviar a SRI (si tienes certificado configurado)

```python
from modules.facturacion_ec.services import send_invoice_to_sri

result = send_invoice_to_sri(inv.id)
print(f"Resultado: {result}")

if result.get('success'):
    print(f"✅ Factura {result.get('estado')} por SRI")
    # Recargar factura desde DB
    inv.refresh_from_db()
    print(f"   Estado DB: {inv.sri_status}")
    print(f"   Mensaje: {inv.sri_message[:200]}")
else:
    print(f"❌ Error: {result.get('mensaje')}")
```

---

## 🗑️ Desinstalar módulo

```bash
# Desactivar módulo
uv run python manage.py module_uninstall facturacion_ec

# Esto:
# 1. Marca EnabledModule como inactivo
# 2. Regenera modules_enabled.py (vacío)
# 3. Reinicia servidor → módulo ya no carga
```

**Nota:** Las tablas en BD NO se eliminan automáticamente. Para eliminar datos:

```bash
# Eliminar migraciones (pérdida de datos)
uv run python manage.py migrate modules.facturacion_ec zero
# OBS: Esto BORRA todas las facturas, clientes, etc.
```

---

## 🔄 Comandos útiles

| Comando | Descripción |
|---------|-------------|
| `uv run python manage.py module_install <path>` | Instalar módulo |
| `uv run python manage.py module_uninstall <name>` | Desinstalar módulo |
| `uv run python manage.py apply_modules` | Regenerar modules_enabled.py |
| `uv run python manage.py sync_modules` | Sincronizar catálogo (scan modules/) |
| `uv run python manage.py register_facturacion_ec` | Registrar en catálogo (manual) |
| `uv run python manage.py send_pending_facturacion` | Enviar facturas pendientes a SRI |
| `uv run python manage.py check` | Verificar sistema (sin errores) |

---

## 🐛 Troubleshooting

### Error: "No module named 'modules.facturacion_ec'"
**Causa:** módulo no activado en `modules_enabled.py`
**Solución:**
```bash
uv run python manage.py module_install modules/facturacion_ec
# Verificar erp_nexus/modules_enabled.py contenga "modules.facturacion_ec"
```

### Error: "field ... doesn't provide model 'User'"
**Causa:** `core_users.User` no existe, debe usarse `settings.AUTH_USER_MODEL`
**Solución:** Revisar que todos los ForeignKey a User usen `settings.AUTH_USER_MODEL`

### Error: "modules.facturacion_ec has no migrations"
**Solución:**
```bash
uv run python manage.py makemigrations facturacion_ec
uv run python manage.py migrate
```

### Error al importar `jinja2` / `lxml` / `signxml`
**Solución:**
```bash
uv pip install jinja2 lxml signxml httpx cryptography
```

### XML no válido contra XSD
**Solución:** Revisar `services/xml_generator.py` - plantilla Jinja2 debe generar EXACTAMENTE estructura SRI. Comparar con XSD oficial.

---

## 📁 Estructura final

```
erp-nexus/
├── erp_nexus/
│   ├── settings.py         # INSTALLED_APPS incluye core + MODULE_APPS
│   ├── modules_enabled.py  # GENERADO: ["modules.facturacion_ec"]
│   └── ...
├── modules/
│   └── facturacion_ec/     # Módulo instalado
│       ├── __meta__.py     # Metadata (parser AST)
│       ├── models.py
│       ├── admin.py
│       ├── services/
│       ├── api/
│       └── migrations/
├── apps/
│   └── core_marketplace/
│       ├── models.py       # ModuleCatalogItem, EnabledModule
│       ├── activation.py   # write_modules_enabled()
│       └── management/
│           └── commands/
│               ├── module_install.py
│               ├── module_uninstall.py
│               ├── apply_modules.py
│               └── sync_modules.py
└── pyproject.toml
```

---

## 🎯 Próximos pasos después de instalación

1. **Semana 3:** XML generator → validar contra XSD
2. **Semana 4:** Firma digital + envío a SRI pruebas
3. **Semana 5:** Auto-envío (señales o cron)
4. **Semana 6:** API REST + admin mejorado
5. **Semana 7-8:** Módulos inventory + sales

---

## 📚 Documentación adicional

- `apps/facturacion/README.md` — Docs del módulo
- `ERP_NEXUS_BUSINESS_PLAN.md` — Modelo negocio + proyecciones
- `ERP_NEXUS_ESTADO_ACTUAL.md` — Estado actual + checklist

---

**¿Errores?** Revisar logs:
```bash
# Verificar módulo cargado
uv run python manage.py shell -c "from django.conf import settings; print(settings.INSTALLED_APPS)"

# Verificar EnabledModule
uv run python manage.py shell -c "from apps.core_marketplace.models import EnabledModule; print(list(EnabledModule.objects.values()))"

# Verificar modules_enabled.py contenido
cat erp_nexus/modules_enabled.py
```
