# PAUL Phase 1.2 — Marketplace UI Polish + License Management

**Objetivo:** Mejorar la experiencia de Marketplace con UI refinada, sistema de licencias, y catálogo público.

## Context

Phase 1.1 creó el.backend funcional (models, commands, API). Phase 1.2 agrega:

1. **UI/UX mejorada** en admin (filtros, búsqueda, advertencias de compatibilidad)
2. **Sistema de licencias** (free/paid, expiry, seat count)
3. **Catálogo público** (página HTML simple)
4. **Validación de licencia** durante install
5. **Tests E2E** del flujo completo

---

## Architecture — License System

### **ModuleLicense Model**

```python
class ModuleLicense(models.Model):
    LICENSE_TYPES = [
        ('free', 'Free / Open Source'),
        ('trial', 'Trial (30 days)'),
        ('paid', 'Paid Subscription'),
        ('perpetual', 'Perpetual License'),
    ]

    module = models.ForeignKey(ModuleCatalogItem, on_delete=models.CASCADE)
    license_key = models.CharField(max_length=100, unique=True)
    license_type = models.CharField(choices=LICENSE_TYPES, max_length=20)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    max_seats = models.IntegerField(default=1)
    used_seats = models.IntegerField(default=0)
    company = models.ForeignKey('core_companies.Company', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=dict)  # {"support": "premium", "updates": True}
```

**Flujo:**
1. Admin crea/licenciase un módulo (via admin o API)
2. Usuario intenta instalar → valida licencia activa
3. Si trial → cuenta atrás
4. Si paid → verifica seat count

---

## Tasks Phase 1.2

### **1.2.1 — Extend ModuleCatalogItem with License Info**

- [ ] Añadir en `ModuleCatalogItem`:
  - `is_licensed` (BooleanField, default=False)
  - `license_required` (BooleanField, default=False)
  - `trial_days` (IntegerField, default=0)
  - `price_monthly` (DecimalField, null=True)
  - `price_yearly` (DecimalField, null=True)
- [ ] Actualizar admin: mostrar campos de licencia
- [ ] Migration: `0003_add_license_fields_to_modulecatalogitem`
- [ ] Commit: `feat(license): extend catalog with license metadata`

### **1.2.2 — Create ModuleLicense Model + Admin**

- [ ] Nuevo modelo en `core_marketplace/models.py`: `ModuleLicense`
- [ ] Admin: `ModuleLicenseAdmin` con search, filters, seat usage bar
- [ ] Admin action: `generate_license_key` (crea clave única aleatoria)
- [ ] Migration: `0004_modulelicense`
- [ ] Commit: `feat(license): ModuleLicense model and admin`

### **1.2.3 — License Validation in module_install**

- [ ] Modificar `module_install` command:
  - Si `catalog_item.license_required` → requiere `--license-key`
  - Validar `ModuleLicense.objects.get(license_key=key)`
  - Check: `is_active`, `valid_until` (si existe), `used_seats < max_seats`
  - Incrementar `used_seats` en +1
  - Si falla → `CommandError: Invalid or expired license`
- [ ] Commit: `feat(license): validate license during module install`

### **1.2.4 — Marketplace Catalog UI (Admin) Polish**

- [ ] Mejorar `ModuleCatalogItemAdmin`:
  - Filtro: `module_type`, `is_licensed`, `license_required`
  - Búsqueda: `display_name`, `technical_name`, `repo_url`
  - `list_filter`: `min_erp_version` (por rango)
  - `actions_buttons`: mostrar advertencia si versión incompatible
  - `display_license_badge`: icono 🔒 para módulos con licencia
- [ ] Commit: `style(marketplace): polish admin catalog UI`

### **1.2.5 — Public Catalog Page**

- [ ] Crear vista pública: `apps/core_marketplace/views.py` → `catalog_public(request)`
- [ ] Template: `core_marketplace/catalog_public.html`
  - Tabla de módulos (name, version, description, license, price)
  - Botón "Instalar" (solo staff)
  - Filtros por tipo (essential/optional/plugin)
- [ ] URL: `/marketplace/` → `core_marketplace:public_catalog`
- [ ] Commit: `feat(marketplace): public catalog page`

### **1.2.6 — API: License Endpoints**

- [ ] `POST /api/v1/marketplace/licenses/` — crear licencia (admin)
- [ ] `GET /api/v1/marketplace/licenses/` — listar licencias (admin)
- [ ] `GET /api/v1/marketplace/licenses/{key}/validate` — validar clave
- [ ] `DELETE /api/v1/marketplace/licenses/{key}/` — revocar
- [ ] Commit: `feat(license): REST API for license management`

### **1.2.7 — Tests E2E**

- [ ] Test: `test_module_install_requires_ license_for_licensed_module`
- [ ] Test: `test_license_invalid_expired_fails`
- [ ] Test: `test_license_seat_limit_exceeded_fails`
- [ ] Test: `test_public_catalog_page_loads`
- [ ] Commit: `test(1.2): e2e tests for marketplace + license`

---

## Acceptance Criteria Phase 1.2

- [ ] ModuleCatalogItem con campos de licencia (`is_licensed`, `license_required`, `trial_days`, precios)
- [ ] Modelo `ModuleLicense` con admin completo
- [ ] `module_install` rechaza módulos sin licencia válida
- [ ] Admin UI: filtros, búsqueda, badges de licencia
- [ ] Página pública `/marketplace/` con catálogo
- [ ] API endpoints para licencias
- [ ] Tests: 5+ pruebas E2E pasando

---

## Dependencies

✅ Phase 1.1 — Marketplace Foundation COMPLETED
🆕 `core_marketplace` app exists with models/admin/commands/api

---

## Timeline Estimation

**Total:** ~14h
- 1.2.1 — 1h
- 1.2.2 — 2h (model + admin + migration)
- 1.2.3 — 1.5h (validation logic)
- 1.2.4 — 1h (admin polish)
- 1.2.5 — 2h (public page + template)
- 1.2.6 — 1.5h (API endpoints)
- 1.2.7 — 2h (E2E tests)
- Testing/debug: 3h buffer

---

## Risks

| Riesgo | Mitigación |
|--------|------------|
| License validation compleja en install | Separar lógica en `core_marketplace/license.py` |
| Race condition en seat count | `select_for_update()` en transacción |
| Admin UI muy compleja | Iteración simple primero |
| API exposed sin auth | JWTAuth ya aplicado |

---

**Estado:** 📋 PLANEADO — Esperando APPLY
