# PAUL Phase Plan — M5-A: Payout Automation

**Feature:** Comisiones → Transferencias bancarias (SRI integración)
**Prioridad:** P2 (Alto valor negocio, Media-Alta complejidad)
**Skill designada:** coding-agent
**Metodología:** PAUL (PLAN → APPLY → UNIFY)
**Duración estimada:** 10-12 días (2 personas)
**Fecha inicio:** 2026-05-13

---

## 🎯 Visión General

Automatizar el flujo de comisiones desde cálculo hasta transferencia bancaria:
1. **Cálculo** de comisiones por módulo (sales, purchases, marketplace)
2. **Acumulación** en wallet/balances por usuario/company
3. **Aprobación** (opcional — flujo automático directo)
4. **Payout** — transferencia bancaria (múltiples bancos Ecuador)
5. **SRI** — retenciones fuente, reportes electrónicos
6. **Notificación** — email + dashboard status

---

## 📊 Estado Actual (Baseline)

**Módulos existentes:**
- `core_payments` — wallet, transactions, top-up (solo inbound)
- `sales` — orders, commissions (sin payout)
- `purchases` — proveedores, pagos
- `facturacion` — SRI facturación, retenciones
- `core_notifications` — email tasks
- `core_companies` — Company model (datos bancarios?)

**Gaps identificados:**
- No hay modelo `Payout` / `BankAccount` / `CommissionRule`
- No hay lógica de cálculo automático por orden
- No hay integración bancaria (APIs: Produbanco, Pichincha, Guayaquil, etc.)
- No hay retención SRI aplicada a comisiones
- No hay cola Celery específica para payouts (reusar `sri` o crear `payouts`)

---

## 🏗️ Architecture Decision

**Estrategia:**
- **Backend-centric:** Django + Django Ninja API + Celery
- **Bank abstraction layer:** Interface `BankProvider` con implementaciones por banco
- **Commission engine:** Servicio separado `CommissionCalculator`
- **Payout worker:** Celery task programada (diaria/semanal) + manual on-demand
- **SRI integration:** Reutilizar `facturacion_ec` para retenciones, generar XML/PDF

**Tech stack:**
```
Backend:
  - Django 5.0 models: Payout, PayoutItem, BankAccount, CommissionRule
  - Django Ninja API: /api/v1/payouts/ (list, create, approve, cancel)
  - Celery: task process_payout_batch, task calculate_commissions_daily
  - Facturacion integration: generar retenciones SRI automáticas

Frontend:
  - Admin UI: Payout list + filters + actions (approve, cancel, retry)
  - Dashboard widget: pending/processed payouts summary
  - Company settings: Bank account form (banco, cuenta, rut)

Infra:
  - Docker env vars: BANK_API_* ( credentials por banco )
  - PostgreSQL: tablas payout + audit
  - Redis: cola `payouts` (concurrency 2, rate-limited)
```

---

## 📋 PAUL Phases — Payout Automation (M5-A)

### **Phase M5-A.1 — Models & Migrations** (2d)
**Objetivo:** Schema de datos para payouts
**Tasks:**
- [ ] `Payout` model (status: draft/approved/processing/paid/failed, total_amount, currency, reference)
- [ ] `PayoutItem` model (FK a Commission/Order, amount, commission_type, retained_amount)
- [ ] `BankAccount` model (company FK, bank_code, account_number, account_type, rut, is_active)
- [ ] `CommissionRule` model (module, percentage, min_amount, max_amount, is_active)
- [ ] `PayoutConfig` model (auto_approve, retention_rate, retention_threshold, retain_until_threshold)
- [ ] Migraciones + data migration (commission rules default)
- [ ] Admin registration + filters

**Commits:** `feat(payout): models + migrations`
**Tests:** Model tests + admin tests (15 tests)

---

### **Phase M5-A.2 — Commission Calculation Service** (2d)
**Objetivo:** Calcular comisiones pendientes por orden/compra
**Tasks:**
- [ ] `CommissionCalculator` service class (singleton-like)
- [ ] `calculate_for_order(order)` — calcula comisión bruta
- [ ] `calculate_for_invoice(invoice)` — extensión facturación
- [ ] Retención SRI aplicada (según `PayoutConfig.retention_rate`)
- [ ] `get_pending_commissions(company, date_range)` — query agregada
- [ ] Signal: `post_save` en Order/Invoice → crear CommissionRecord
- [ ] Management command `calculate_commissions` (dry-run + apply)

**Commits:** `feat(payout): commission calculator service`
**Tests:** 20 unit tests (calculator, retention, edge cases)

---

### **Phase M5-A.3 — Bank Integration Layer** (3d)
**Objetivo:** Abstraction para múltiples bancos Ecuador
**Tasks:**
- [ ] Abstract `BankProvider` (transfer(amount, account, reference) → {success, tx_id})
- [ ] Implementaciones:
  - `ProdubancoProvider` (API REST — consultar docs Produbanco Empresas)
  - `PichinchaProvider` (API SOAP/JSON — Banco Pichincha Negocios)
  - `GuayaquilProvider` (API REST — Banco Guayaquil Empresas)
  - `DummyProvider` (testing — mock exitoso)
- [ ] Factory `BankProviderFactory(bank_code)` → provider instance
- [ ] Settings: `BANK_API_TIMEOUT=30`, `BANK_RETRY_ATTEMPTS=3`
- [ ] Error handling: `BankError`, `InsufficientFundsError`, `AccountNotFoundError`
- [ ] Retry logic (celery automatic retry on bank errors)

**Commits:** `feat(payout): bank abstraction layer + providers`
**Tests:** Mock-based tests por provider (15 tests)

---

### **Phase M5-A.4 — Celery Tasks + Beat Schedule** (1.5d)
**Objetivo:** Procesamiento asíncrono de payouts
**Tasks:**
- [ ] `process_payout_batch(payout_id)` — task individual (lock payout, call bank, update status)
- [ ] `calculate_commissions_daily()` — Beat task (diaria 02:00 AM)
- [ ] Queue `payouts` creada en `celery.py` (concurrency=2, priority=high)
- [ ] Task retry config (max_retries=3, backoff 60s)
- [ ] Celery signals: on_success → send notification, on_failure → alert admin
- [ ] Idempotency: payout processing uses `select_for_update` lock

**Commits:** `feat(payout): celery tasks + beat schedule`
**Tests:** Celery task tests (10 tests)

---

### **Phase M5-A.5 — Django Ninja API Endpoints** (2d)
**Objetivo:** CRUD + actions para payouts
**Tasks:**
- [ ] `PayoutOut` schema (id, reference, total, status, items_count, created_at, paid_at)
- [ ] `PayoutItemOut` schema (order_id, amount, commission_type, retained)
- [ ] `BankAccountIn/Out` schemas
- [ ] GET `/api/v1/payouts/` — list (filters: status, date_range, company)
- [ ] GET `/api/v1/payouts/{id}/` — detail + items
- [ ] POST `/api/v1/payouts/` — crear desde pending commissions (bulk)
- [ ] POST `/api/v1/payouts/{id}/approve/` — approve (JWT admin)
- [ ] POST `/api/v1/payouts/{id}/cancel/` — cancel (only draft)
- [ ] GET `/api/v1/payouts/banks/` — list configured banks
- [ ] POST `/api/v1/payouts/bank-accounts/` — create bank account
- [ ] Auth: JWT required (admin + staff)
- [ ] Pagination: 50/page

**Commits:** `feat(payout): ninja API endpoints`
**Tests:** API integration tests (25 tests)

---

### **Phase M5-A.6 — Admin UI + Dashboard** (1.5d)
**Objetivo:** UI para gestión de payouts
**Tasks:**
- [ ] `PayoutAdmin` (list_display: ref, total, status, paid_at, actions)
- [ ] `PayoutItemInline` (readonly, show order breakdown)
- [ ] `BankAccountAdmin` (encrypted account numbers?)
- [ ] `CommissionRuleAdmin` (percentage, active flag)
- [ ] Dashboard card: `pending_payouts_count`, `total_pending_amount`
- [ ] Dashboard chart: payouts by month (last 6 months)
- [ ] Django admin actions: "Approve selected", "Cancel selected"
- [ ] Export CSV: payouts report (filtered)

**Commits:** `feat(payout): admin UI + dashboard`
**Tests:** Selenium admin tests? (skip — manual QA)

---

### **Phase M5-A.7 — SRI Integration** (2d)
**Objetivo:** Retenciones y reportes SRI automáticos
**Tasks:**
- [ ] `SRIRetention` model (payout FK, invoice_number, xml_doc, pdf_doc, submitted_at)
- [ ] Service `SRIRetentionGenerator` → genera XML retención (usar `facturacion_ec`)
- [ ] Signal: `post_save` Payout(paid) → crear SRIRetention (auto)
- [ ] Task: `submit_retentions_to_sri()` — envío masivo a SRI (Async)
- [ ] API: GET `/api/v1/payouts/{id}/retencion/` — descargar XML/PDF
- [ ] Admin: SRIRetention inline en Payout
- [ ] Reportes mensuales: `generate_sri_report(month, year)` → ZIP

**Commits:** `feat(payout): SRI retention integration`
**Tests:** 15 integration tests (retención generation, SRI mock)

---

### **Phase M5-A.8 — Notifications + QA** (1d)
**Objetivo:** Comunicación + validación completa
**Tasks:**
- [ ] Email template: `payout_approved.html`, `payout_paid.html`, `payout_failed.html`
- [ ] Tarea: `send_payout_notification(payout_id)` — envia email a admin/company
- [ ] Management command `payout_summary` — reporte diario PDF
- [ ] Manual QA checklist:
  - [ ] Crear payout desde pending commissions → draft
  - [ ] Approve → processing → paid (mock bank)
  - [ ] Retención SRI generada correctamente
  - [ ] Email recibido por stakeholder
  - [ ] Dashboard stats actualizan
- [ ] Django check 0 issues
- [ ] Commit final: `feat(payout): full M5-A implementation`

**Commits:** `feat(payout): notifications + QA`
**Tests:** E2E manual (5 escenarios), Django check

---

## 📈 Testing Strategy

**Unit tests:** 75+ (models, services, calculators, bank providers)
**Integration tests:** 40+ (API endpoints, Celery tasks, SRI generation)
**Manual QA:** 5 escenarios críticos (end-to-end payout flow)

**Test coverage target:** 85%

---

## 🚀 Deployment Considerations

**Environment variables:**
```bash
# Bank credentials (por banco)
BANK_PRODUBANCO_API_KEY=...
BANK_PRODUBANCO_SECRET=...
BANK_PICHINCHA_USER=...
BANK_PICHINCHA_PASSWORD=...
BANK_GUAYAQUIL_TOKEN=...

# Payout config
PAYOUT_AUTO_APPROVE=false
PAYOUT_RETENTION_RATE=10.5  # %retención SRI
PAYOUT_RETAIN_UNTIL_THRESHOLD=100  # USD mínimos para pagar
```

**Docker:**
- `docker-compose.prod.yml` — agregar service `payout-worker` (si masa crítica)
- O reusar `worker` existente con cola `payouts`

**Migrations:**
- `makemigrations` + `migrate` — 6 nuevas tablas
- Data migration: default `CommissionRule` (sales=5%, purchases=3%)

**Rollback:**
- `rollback.sh` ya existente — detener stack + git reset
- Payout-specific: manual DB rollback si transacción bancaria ya ejecutada (complejo — irreversible)

---

## 📊 Success Metrics

- **Automatización:** 100% comisiones pagadas sin intervención manual
- **Accuracy:** Cálculos coinciden con hoja Excel (±0.01%)
- **Uptime:** Payout worker disponible 99.5%
- **SRI compliance:** 100% retenciones generadas y validadas
- **Error rate:** < 0.5% fallos bancarios (retry automático)

---

## ⚠️ Dependencies & Blockers

**Dependencias externas:**
- API bancarias (Produbanco/Pichincha/Guayaquil) — necesitamos credenciales testing
- `facturacion_ec` — ya integrado, usar para retenciones
- Celery + Redis — existente

**Blockers:**
- [ ] Acceso a sandbox bancario (Ecuador) — **antes de Phase M5-A.3**
- [ ] Modelo `Company` extendido con campos bancarios (si no existe)
- [ ] Aprobación legal de retenciones SRI (comisión tipo servicios)

---

## 🎯 Next Steps (Inmediate)

1. ✅ Architect analysis complete (este documento)
2. **Kickoff coding-agent** con este plan (PAUL phases)
3. Graphify analysis (opcional — revisar modelos existentes antes de codificar)
4. Implementación Phase M5-A.1 (Models) → commit + tests
5. Iterate sequentially through phases

---

**Plan status:** 📋 APPROVED — awaiting coding-agent kickoff
**Owner:** JARVIS (OpenClaw Assistant)
**Fecha:** 2026-05-13
