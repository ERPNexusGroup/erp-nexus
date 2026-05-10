# INSTALACIÓN — ERP Nexus (Hybrid Architecture)

**Versión:** 0.6.x-alpha  
**Arquitectura:** Hybrid — Essential modules integrados en core

---

## 📋 Requisitos previos

- Python 3.11 o superior
- `uv` instalado (gestor de paquetes ultra-rápido)
- Git
- Base de datos PostgreSQL (recomendado) o SQLite (desarrollo rápido)

---

## 🚀 Instalación rápida (5 minutos)

```bash
# 1. Clonar ERP Nexus (único repositorio necesario)
git clone https://github.com/ERPNexusGroup/erp-nexus.git
cd erp-nexus

# 2. Instalar dependencias (uv es 10-100x más rápido que pip)
uv sync

# 3. Configurar variables de entorno (opcional, valores por defecto para dev)
cp .env.example .env
# Editar .env si es necesario (DB, SECRET_KEY, etc.)

# 4. Aplicar migraciones (crea todas las tablas de los 17 módulos)
uv run python manage.py migrate

# 5. Crear superusuario
uv run python manage.py createsuperuser --username admin --email admin@erpnexus.ec

# 6. Levantar servidor
uv run python manage.py runserver
```

**Acceso:**
- URL admin: http://localhost:8000/admin
- API: http://localhost:8000/api/v1/
- Docs API: http://localhost:8000/api/docs (Swagger UI)

---

## 📦 ¿Qué incluye la instalación por defecto?

ERP Nexus instala **17 aplicaciones Django** automáticamente:

| Tipo | Apps | Descripción |
|------|------|-------------|
| **Core Framework (11)** | `core_users`, `core_companies`, `core_events`, `core_api`, `core_marketplace`, `core_permissions`, `core_audit`, `core_stats`, `core_config`, `core_dashboard`, `core_pagebuilder` | Framework base — siempre cargado |
| **Essential Modules (6)** | `facturacion`, `inventory`, `sales`, `purchases`, `notifications`, `print_manager` | Módulos de negocio integrados |

**NO necesitas instalar plugins adicionales** para tener un ERP funcional:
- ✅ Facturación electrónica SRI Ecuador (listo)
- ✅ Gestión de inventario (listo)
- ✅ Ventas y cotizaciones (listo)
- ✅ Compras y órdenes de compra (listo)
- ✅ Notificaciones email/Telegram (listo, configurar credenciales)
- ✅ Generación de PDFs (listo, plantillas básicas)

---

## ⚙️ Configuración inicial post-instalación

### 5.1 Crear Company (empresa principal)

```bash
uv run python manage.py shell
```

```python
from apps.core_companies.models import Company

# Crear company de prueba
c = Company.objects.create(
    name="Mi Empresa Ecuador SA",
    ruc="1791234567001",  # RUC válido (algoritmo mód 10)
    slug="mi-empresa",
    address="Quito, Pichincha, Ecuador",
    phone="+5939988776655",
    email="info@miempresa.ec"
)
print(f"✅ Company: {c.name} (RUC: {c.ruc})")
```

### 5.2 Configurar certificado digital SRI (opcional)

El módulo `facturacion` funciona **sin certificado** para crear facturas en estado `draft`. Para enviar al SRI necesitas certificado `.p12`.

```bash
# Opción A — variables entorno (.env)
echo "FACTURACION_CERT_PATH=/ruta/completa/certificado.p12" >> .env
echo "FACTURACION_CERT_PASSWORD=tu_password" >> .env
echo "SRI_AMBIENTE=1" >> .env  # 1=Pruebas, 2=Producción

# Opción B — settings.py (no recomendado para producción)
# FACTURACION = {
#     "CERT_PATH": "/path/to/cert.p12",
#     "CERT_PASSWORD": "password",
#     "SRI_AMBIENTE": 1,
# }
```

**Obtener certificado de pruebas SRI:**
1. Registrarse en https://celcer.sri.gob.ec/
2. Descargar certificado `.p12` (password habitualmente `1234`)
3. Colocar en `~/certs/` o ruta segura

### 5.3 Configurar notificaciones (Email + Telegram)

```bash
# .env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password

TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=tu_chat_id
```

### 5.4 Crear datos de prueba (facturación + inventario)

```bash
# Cargar fixtures (futuro)
uv run python manage.py loaddata fixtures/initial_data.json
```

---

## 🔄 Diferencias vs Plugin-Only Architecture

| Aspecto | Plugin-Only (WordPress style) | **Hybrid (ERP Nexus)** |
|---------|-------------------------------|------------------------|
| Instalación inicial |框架 + 5+ plugins | `git clone` único |
| Manejo de dependencias | Cada plugin resuelve sus propias deps | Core gestiona todas deps |
| Migraciones | Cada plugin tiene su propio | Todas en un solo `migrate` |
| Desinstalación | `module_uninstall plugin_name` | No aplica — essential modules always installed |
| Customización | Plugins reemplazables | Essential modules modificables en core |

**ERP Nexus Hybrid** está diseñado para PYMES que necesitan un ERP completo listo en 5 minutos, sin fricción de instalar 6 módulos por separado.

---

## 🧪 Validación de instalación

```bash
# 1. Verificar apps cargadas
uv run python manage.py shell -c "
from django.conf import settings
apps = [a for a in settings.INSTALLED_APPS if a.startswith('apps.')]
print('Essential modules loaded:', len([a for a in apps if a not in settings.INSTALLED_APPS[:11]]))
print('Apps:', sorted(apps))
"

# 2. Check system
uv run python manage.py check

# 3. Probar API facturación
curl http://localhost:8000/api/v1/facturacion/customers/ | jq .

# 4. Probar inventory
curl http://localhost:8000/api/v1/inventory/products/ | jq .

# 5. Login admin
# http://localhost:8000/admin → verificar menú incluye:
#   - Facturación (facturas, clientes, productos SRI)
#   - Inventario (productos, movimientos)
#   - Ventas (cotizaciones, órdenes)
#   - Compras (OC, proveedores)
```

---

## 🐛 Troubleshooting

### Error: "No module named 'apps.facturacion'"
**Causa:** `facturacion` no está en `INSTALLED_APPS`  
**Solución:** Verificar `erp_nexus/settings/base.py` incluye `"apps.facturacion"`

### Error de migración pendiente
```bash
uv run python manage.py makemigrations
uv run python manage.py migrate --fake-initial
```

### Error al crear superuser: "User model has no field 'email'"
**Causa:** Usando custom User model de `core_users`  
**Solución:** El comando `createsuperuser` funciona normalmente. Si falla:
```bash
uv run python manage.py shell -c "
from apps.core_users.models import User
User.objects.create_superuser('admin', 'admin@erpnexus.ec', 'password123')
"
```

### Puerto 8000 ocupado
```bash
uv run python manage.py runserver 0.0.0.0:8080
```

---

## 📚 Documentación

- `MODULE_SPEC.md` — Especificaciones técnicas de cada módulo
- `ARCHITECTURE_HYBRID.md` — Guía arquitectónica (Hybrid Model)
- `ADR/` — Architectural Decision Records
- `apps/<module>/README.md` — Docs específicas por módulo
- `API_REFERENCE.md` — Referencia completa de endpoints
- `docs/DEVELOPMENT.md` — Guía para desarrolladores

---

## 🔧 Comandos útiles

| Comando | Descripción |
|---------|-------------|
| `uv run python manage.py check` | Verificar sistema sin errores |
| `uv run python manage.py migrate` | Aplicar migraciones pendientes |
| `uv run python manage.py makemigrations` | Generar migraciones desde cambios en modelos |
| `uv run python manage.py shell` | Consola Django interactiva |
| `uv run python manage.py collectstatic` | Colectar archivos estáticos (producción) |
| `uv run pytest apps/` | Tests de todas las apps |
| `uv run pytest apps/facturacion/` | Tests solo facturación |

---

## 🎯 Próximos pasos

1. Configurar certificado SRI (si necesitas facturar en producción)
2. Personalizar plantillas PDF (via `print_manager`)
3. Configurar correo SMTP para notificaciones automáticas
4. Revisar `apps/facturacion/README.md` para flujo SRI completo
5. Explorar API: http://localhost:8000/api/docs

---

**ERP Nexus — Listo en 5 minutos.**
**¿Problemas?** Revisar logs: `tail -f logs/erp-nexus.log`
