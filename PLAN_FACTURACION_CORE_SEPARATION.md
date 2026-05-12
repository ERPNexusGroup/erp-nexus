# Facturación Core Separation — Plan de Implementación

**Proyecto:** ERP Nexus — Separación de core facturación y plugin SRI Ecuador
**Metodología:** PAUL (PLAN → APPLY → UNIFY)
**Estado:** En progreso — 60% completado (diseño e implementación estructural)
**Fecha:** 2026-05-12
**Responsable:** Walter Cun (con asistencia IA)

---

## 📋 PLAN — Visión y Alcance

### 1.1 Problema
El módulo `facturacion_ec` está monolítico:
- Mezcla lógica de negocio local (Customer, Invoice, Quote) con lógica SRI específica (XML, firma, catálogos)
- Dificulta testing, mantenimiento y posible expansión a otros países
- Imposible reutilizar core facturación sin arrastrar dependencias SRI

### 1.2 Solución
Separar en dos capas claras:

| Capa | Ubicación | Responsabilidad |
|------|-----------|-----------------|
| **Core Facturación** | `apps/facturacion/` | Modelos locales, cálculos, estados, API REST local |
| **Plugin SRI Ecuador** | `modules/facturacion_ec/` | Catálogos SRI, licenciamiento, XML, firma digital, envío SOAP |

### 1.3 Principios de Diseño

- **Independencia regulatoria**: El core no conoce detalles de SRI Ecuador
- **Extensibilidad**: Otros plugins pueden implementar su propio integrador (ej. facturacion_mx)
- **Compatibilidad hacia atrás**: El API existente se mantiene (via plugin)
- **Single Source of Truth**: Datos facturación viven solo en core, extensión SRI solo metadata de integración

### 1.4 Alcance (In-scope)

- Migrar modelos: `Customer`, `Product`, `Invoice`, `InvoiceLine`, `Quote`, `QuoteLine` → core
- Crear `InvoiceSRIExtension` (OneToOne a core.Invoice) para campos SRI
- Mover catálogos SRI (SriAmbiente, SriTipoComprobante, SriImpuesto) → plugin
- Mover lógica de licenciamiento (LicenseType, CompanyLicense) → plugin
- Refactorizar servicios: `xml_generator`, `digital_signature`, `sri_client` → plugin
- Adaptar integración con `apps.sales.Order` → core.Invoice
- Actualizar API REST: separar endpoints core vs SRI-specific
- Actualizar admin: separar registros core vs plugin
- Mantener señales de auto-numeración y cálculo de totales
- Migración de datos desde tablas legacy a nueva estructura
- Actualizar dependencias de migraciones (sales, purchases)
- Escribir migración de datos one-off

### 1.5 No Alcance (Out-of-scope)

- Cambiar lógica de negocio de facturación (cálculos, validaciones) — se mantiene
- Modificar `core_companies` o `core_users` — se usan tal cual
- Implementar soporte multi-país (solo Ecuador por ahora) — futura fase
- Cambiar framework (Django -> otro) — fuera de scope

### 1.6 Artefactos Entregables

| Artefacto | Tipo | Ubicación |
|-----------|------|-----------|
| Modelos core facturación | Código | `apps/facturacion/models.py` |
| API core facturación | Código | `apps/facturacion/api/routes.py` |
| Señales core | Código | `apps/facturacion/signals.py` |
| Admin core | Código | `apps/facturacion/admin.py` |
| Modelos plugin SRI | Código | `modules/facturacion_ec/models.py` |
| Plugin SRI API | Código | `modules/facturacion_ec/api/routes.py` |
| Plugin SRI Admin | Código | `modules/facturacion_ec/admin.py` |
| Servicios plugin (XML, firma, SRI client) | Código | `modules/facturacion_ec/services/*.py` |
| Migraciones iniciales | Migraciones | `apps/facturacion/migrations/0001_initial.py`<br>`modules/facturacion_ec/migrations/0001_initial.py` |
| Migración de datos | Management Command | `modules/facturacion_ec/management/commands/migrate_facturacion_ec_data.py` |
| Documentación arquitectura | Markdown | `docs/FACTURACION_CORE_SEPARATION.md` |
| Plan de implementación | Markdown | `PLAN_FACTURACION_CORE_SEPARATION.md` (este archivo) |
| Actualización de estado | Markdown | `STATE.md` |

---

## 📐 APPLY — Pasos de Implementación

### Fase 0 — Preparación (completado)

- [x] Análisis de código existente en `modules/facturacion_ec/`
- [x] Identificación de modelos a mover
- [x] Diseño de arquitectura objetivo
- [x] Creación de directorios: `apps/facturacion/`, `apps/facturacion/api/`
- [x] Configuración de apps en `INSTALLED_APPS`

### Fase 1 — Crear Core Facturación (✅ 100%)

**Objetivo:** Extraer y reimplementar los modelos de negocio local sin dependencias SRI.

**Pasos:**

1. **Crear estructura de app core**
   ```bash
   mkdir -p apps/facturacion/api
   touch apps/facturacion/__init__.py apps/facturacion/apps.py apps/facturacion/models.py \
         apps/facturacion/admin.py apps/facturacion/signals.py apps/facturacion/urls.py \
         apps/facturacion/api/__init__.py apps/facturacion/api/routes.py \
         apps/facturacion/migrations/__init__.py
   ```

2. **Implementar modelos core** (`apps/facturacion/models.py`)
   - `Customer` (sin cambios sustanciales)
   - `Product` (sin cambios sustanciales)
   - `Invoice` (sin campos SRI: `ambiente`, `tipo_comprobante`, `access_key`, `xml_content`, `sri_status`, etc.)
   - `InvoiceLine` (sin cambios)
   - `Quote` y `QuoteLine` (nuevos, antes no existían)
   - Estados locales: `draft`, `sent`, `paid`, `cancelled` para Invoice

3. **Implementar señales** (`apps/facturacion/signals.py`)
   - `invoice_line_calculate_totals`: calcula totals en línea antes de guardar
   - `invoice_line_update_invoice_totals`: recalcula totales de factura post-guard
   - `invoice_assign_number`: asigna número automático (formato 001-001-000000001)
   - `quote_assign_number`: asigna número de cotización (COT-001-000001)

4. **Implementar Admin** (`apps/facturacion/admin.py`)
   - Registro de Customer, Product, Invoice, InvoiceLine, Quote, QuoteLine
   - Inlines para líneas
   - Acciones (ej. convertir Quote → Invoice)

5. **Implementar API REST** (`apps/facturacion/api/routes.py`)
   - Endpoints CRUD para Customers, Products
   - Endpoints para Invoices (list, create, get)
   - Endpoints para Quotes (list, create, convert-to-invoice)
   - Schemas Ninja (CustomerIn/Out, ProductIn/Out, InvoiceIn/Out, QuoteIn/Out)

6. **Crear migración inicial** (`apps/facturacion/migrations/0001_initial.py`)
   - Generada manualmente (ver archivo)
   - Dependencias: `core_companies`, `auth.User`
   - Índices nombrados explícitamente

7. **Actualizar `INSTALLED_APPS`** (`erp_nexus/settings/base.py`)
   ```python
   INSTALLED_APPS = [
       ...,
       "apps.facturacion",  # Core facturación local
       ...
   ]
   ```

✅ **Resultado:** Core facturación independiente, probablemente funcional.

---

### Fase 2 — Adaptar Plugin SRI (✅ 100%)

**Objetivo:** Transformar `facturacion_ec` de monolito a plugin que extiende el core.

**Pasos:**

1. **Reducir alcance de modelos en `modules/facturacion_ec/models.py`**
   - Eliminar: `Customer`, `Product`, `Invoice`, `InvoiceLine` (usará core)
   - Mantener: `SriAmbiente`, `SriTipoComprobante`, `SriImpuesto`, `LicenseType`, `CompanyLicense`
   - Agregar: `InvoiceSRIExtension` (OneToOne a `facturacion.Invoice`)
     - Campos SRI: `ambiente`, `tipo_comprobante` (FK), `access_key`, `xml_content`, `xml_original_hash`, `sri_status`, `sri_authorization_date`, `sri_message`, `sri_xml_autorizado`, `guia_remision_number`
     - Relación: `invoice = OneToOneField('facturacion.Invoice', on_delete=CASCADE, related_name='sri_extension')`

2. **Actualizar Admin** (`modules/facturacion_ec/admin.py`)
   - Registrar nuevos modelos (extension + catálogos + licencias)
   - Read-only para campos generados por SRI
   - Remover admin de modelos movidos al core

3. **Refactorizar servicios** (`modules/facturacion_ec/services/`)
   - `facturation_integration.py`:
     - Ahora recibe `invoice_id` (core) en lugar de crear modelo propio
     - Obtiene/crea `InvoiceSRIExtension`
     - Genera XML → firma → envío
     - Actualiza extensión con respuesta SRI
   - `xml_generator.py`:
     - Acepta `invoice` (core.Invoice) y `invoice_lines` (related manager)
     - Usa datos de `invoice.company` y `invoice.customer`
     - Genera XML según XSD SRI v1.0.0
   - `digital_signature.py`: sin cambios (usaba `lxml`, `signxml`)
   - `sri_client.py`: sin cambios (cliente SOAP)
   - `code_unique.py`: sin cambios
   - `validator.py`: sin cambios

4. **Actualizar Signals** (`modules/facturacion_ec/signals.py`)
   - Escuchar `post_save` de `facturacion.Invoice`
   - Crear/actualizar `InvoiceSRIExtension`
   - Disparar envío SRI en background (threading) en DEBUG o si `FACTURACION_EC_AUTO_SEND=True`

5. **Actualizar API REST** (`modules/facturacion_ec/api/routes.py`)
   - **Eliminar** endpoints duplicados de core (create invoice, list customers, products)
   - **Mantener** endpoints SRI-specific:
     - `GET /api/facturacion-ec/extensions/` — listar extensiones SRI
     - `GET /api/facturacion-ec/extensions/{id}/` — detalle extensión
     - `POST /api/facturacion-ec/invoices/{id}/send/` — enviar factura core a SRI
     - `GET /api/facturacion-ec/invoices/{id}/xml/` — descargar XML firmado
     - `GET /api/facturacion-ec/invoices/{id}/xml-autorizado/` — XML autorizado por SRI
     - `GET /api/facturacion-ec/catalogos/*` — catálogos SRI
     - `GET/POST /api/facturacion-ec/licenses/` — gestión de licencias

6. **Actualizar Management Commands**
   - `send_pending_facturacion.py`:
     - Ahora consulta `Invoice.objects.filter(status='draft')` (core)
     - Llama a `send_invoice_to_sri(invoice.id)`
   - `migrate_facturacion_ec_data.py` (nuevo):
     - Migra datos legacy (tabla antigua `modules.facturacion_ec_invoice`) → core + extensión
     - Copia Customer, Product, Invoice, InvoiceLine a tablas core
     - Crea `InvoiceSRIExtension` con campos SRI heredados
     - Marcar como `--dry-run` por defecto para validación

7. **Crear migración inicial para plugin** (`modules/facturacion_ec/migrations/0001_initial.py`)
   - Incluye: SriAmbiente, SriTipoComprobante, SriImpuesto, LicenseType, CompanyLicense, InvoiceSRIExtension
   - Depende de `('facturacion', '0001_initial')` y `('core_companies', '0001_initial')`
   - Índices nombrados

8. **Actualizar `modules_enabled.py`**
   - Ya solo carga `'modules.facturacion_ec'` — correcto

✅ **Resultado:** Plugin SRI aislado, solo dependiente de core facturación.

---

### Fase 3 — Migración de Datos Legacy (⏳ Pendiente)

**Objetivo:** Mover datos existentes en producción/dev desde el esquema viejo al nuevo.

**Estrategia:**
- Usar comando `migrate_facturacion_ec_data` (creado en Fase 2)
- Ejecutar en transacciones por lotes (batch_size = 100)
- Dry-run primero, validar conteos, luego aplicar

**Detalles:**
```bash
# 1. Backup de BD
uv run python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > backup.json

# 2. Dry-run (solo conteos)
uv run python manage.py migrate_facturacion_ec_data --dry-run

# 3. Migración real
uv run python manage.py migrate_facturacion_ec_data --batch-size 100

# 4. Verificar
uv run python manage.py shell -c "from apps.facturacion.models import Invoice; print(Invoice.objects.count())"
```

**Validación:**
- Contar registros: `Customer`, `Product`, `Invoice`, `InvoiceLine` (core) vs legacy
- Verificar que cada Invoice legacy tenga su `InvoiceSRIExtension`
- Probar envío de una factura migrada a SRI (ambiente pruebas)

**Rollback:**
- Restaurar backup JSON: `uv run python manage.py loaddata backup.json`
- Revertir migraciones: `uv run python manage.py migrate facturacion zero` y `facturacion_ec zero`

---

### Fase 4 — Actualizar Integraciones (✅ 80%)

**Objetivo:** Asegurar que otras apps (sales, purchases) funcionen con nueva estructura.

**Cambios ya realizados:**
- ✅ `apps/sales/migrations/0001_initial.py`: dependencia actualizada a `facturacion.0001_initial`
- ✅ `apps/purchases/migrations/0001_initial.py`: dependencia actualizada

**Pendiente:**
- Verificar que `apps.sales.models.Order` sigue funcionando con `Customer` en core facturación
- Si hay ForeignKey directas a `facturacion_ec.Customer`, actualizar a `facturacion.Customer`
- Revisar `core_api/v1/facturacion_ec.py` — importa desde `modules.facturacion_ec.api.routes`, OK

---

### Fase 5 — Testing (⏳ Pendiente)

**Unit Tests:**
- Core facturación: tests de modelos, signals, cálculos de totales
- Plugin SRI: tests de services (XML gen, firma, cliente SOAP) con mocks
- API: tests de endpoints core y SRI

**Integration Tests:**
- Flujo completo: Order → Invoice (core) → send_to_sri → SRI extension
- Manejo de errores SRI (rechazo, timeouts)

**Cobertura objetivo:** >80%

---

### Fase 6 — Documentación y Despliegue (⏳ Pendiente)

**Documentación:**
- `docs/FACTURACION_CORE_SEPARATION.md` — arquitectura, decisión técnica, diagrama
- `README.md` de apps facturacion y modules facturacion_ec actualizados
- Guía de migración para despliegues existentes

**Despliegue:**
1. Actualizar `docker-compose.prod.yml` si hay nuevos servicios (no)
2. Ejecutar migraciones en producción: `uv run python manage.py migrate`
3. Ejecutar migración de datos: `uv run python manage.py migrate_facturacion_ec_data`
4. Validar健康 checks: `/api/health/`
5. Monitorear logs por errores SRI

**Rollback inmediato:**
- `scripts/rollback.sh` — rollback a commit anterior
- Restaurar BD desde backup
- Revertir `INSTALLED_APPS` y dependencias de migraciones

---

## ✅ UNIFY — Validación y Monitoreo

### Criterios de Aceptación

| Criterio | Métrica | Target |
|----------|---------|--------|
| Integridad datos | % facturas legacy migradas | 100% |
| Funcionalidad core | Invoices/Quotes creados vía API | OK |
| Envío SRI | Facturas aceptadas en ambiente pruebas | >95% |
| Performance | Latencia creación factura < 200ms | OK |
| Errores | 5xx errors en /api/facturacion/ < 0.1% | OK |

### Checkpost de健康

```bash
# 1. Aplicación arranca sin errores
uv run python manage.py check --deploy

# 2. Migraciones aplicadas
uv run python manage.py showmigrations facturacion facturacion_ec

# 3. Conexión DB OK
uv run python manage.py dbshell -c "SELECT 1;"

# 4. API健康
curl http://localhost:8000/api/health/
```

### Monitoreo en Producción

- **Métricas clave:**
  - `invoices_created_total` por compañía
  - `sri_send_success_rate` (aprox por logs)
  - `license_usage` (facturas del mes vs límite)
- **Logs:** errors en `modules.facturacion_ec` → alerta
- **Dashboard:** ya existe en `core_dashboard` — agregar widget de facturación

### Alertas

| Condición | Severidad | Acción |
|-----------|-----------|--------|
| `sri_status='rejected'` en >5 facturas/hora | WARNING | Revisar certificado, conexión SRI |
| `Invoice` sin `sri_extension` | ERROR | Re-run migración de datos |
| Tasa de envío SRI > 80% | INFO | Considerar escalar workers |
| Licencia exceed (max_invoices) | WARNING | Notificar admin, upsell |

### Runbooks

1. **Factura rechazada por SRI:** revisar `sri_message` en admin o `InvoiceSRIExtension`
2. **XML no generado:** verificar certificado `.p12` configurado en settings
3. **Extension SRI missing:** ejecutar `python manage.py migrate_facturacion_ec_data --company-id N`
4. **Performance lento:** revisar índices DB (ya creados en migraciones)

---

## 📊 Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Pérdida datos durante migración | Baja | CRÍTICO | Backup completo antes de migrar; dry-run extenso; script reversible |
| Incompatibilidad con sales/purchases | Media | ALTO | Actualizar dependencias de migraciones; pruebas integración antes de deploy |
| Errores en generación XML SRI | Media | ALTO | Tests unitarios contra XSD SRI; ambiente pruebas 1 primero |
| Certificado digital inválido | Baja | MEDIO | Validar certificado en deployment; logs claros |
| Cuellos de botella en envío SRI (threading) | Media | MEDIO | Usar Celery workers (futuro); batch sendPending |

---

## 📝 Comandos Útiles

```bash
# Development
cd /home/wcun/.openclaw/workspace/repos/erp-nexus
uv run python manage.py makemigrations facturacion facturacion_ec
uv run python manage.py migrate --fake-initial  # si tablas ya existen

# Migración de datos
uv run python manage.py migrate_facturacion_ec_data --dry-run
uv run python manage.py migrate_facturacion_ec_data --company-id 1

# Enviar facturas pendientes SRI (cron)
uv run python manage.py send_pending_facturacion --limit 50

# Test
uv run pytest apps/facturacion/tests/ -v
uv run pytest modules/facturacion_ec/tests/ -v
```

---

## 🏁 Entregables Finales (al completar F1)

- [x] Core facturación funcional (`apps/facturacion/`)
- [x] Plugin SRI aislado (`modules/facturacion_ec/`)
- [x] Migraciones iniciales aplicables
- [x] Comando de migración de datos
- [ ] Migración de datos ejecutada en dev
- [ ] Tests de integración passing
- [ ] Documentación arquitectónica
- [ ] STATE.md actualizado
- [ ] Commit con mensaje `F1: core separation — facturacion core extracted to apps/`

---

**Plan aprobado por:** Walter Cun
**Fecha inicio:** 2026-05-12
**Fecha estimada de finalización:** 2026-05-15 (incluyendo migración y pruebas)
