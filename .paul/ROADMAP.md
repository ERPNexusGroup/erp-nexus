# ERP Nexus — Roadmap (PAUL)

**Version:** 1.0.0-alpha  
**Last Updated:** 2026-05-10

---

## 🎯 Milestones

### **M0 — Core Foundation** ✅ COMPLETED
**Target:** Semana 1  
**Status:** ✅ Done

**Deliverables:**
- [x] 11 core Django apps configuradas
- [x] Multi-tenant middleware (`ActiveCompanyMiddleware`)
- [x] ModuleRegistry básico
- [x] Settings base (development + production)
- [x] Docker Compose stack (PostgreSQL + Redis)
- [x] Project documentation suite (14 documentos)

**Outcome:** Core listo para módulos.

---

### **M1 — facturacion Complete** 🔥 current
**Target:** Semana 4  
**Status:** 🔄 In Progress (40%)

**Objective:** Módulo de facturación electrónica Ecuador completo como referencia.

**Phases:**
- **Phase 1.1** — Services layer (XML, signature, SRI client) — ⬜ 0%
- **Phase 1.2** — API completion + integration — ⬜ 0%
- **Phase 1.3** — Tests + validation — ⬜ 0%
- **Phase 1.4** — Extract to separate repo — ⬜ 0%

**Success:** Módulo funcional end-to-end, tests >70%, repo separado en GitHub.

---

### **M2 — Marketplace & Module System** 📋 Planned
**Target:** Semana 6  
**Status:** ⬜ Not Started

**Objective:** Sistema de marketplace funcional para instalar módulos.

**Phases:**
- **Phase 2.1** — ModuleInstaller mejorado (descarga git, validación)
- **Phase 2.2** — Marketplace UI en admin
- **Phase 2.3** — License management (free/paid)
- **Phase 2.4** — Registry externo (catálogo oficial)

**Success:** Instalar `facturacion` desde GitHub oficial, activar/desactivar modules.

---

### **M3 — inventory Module** 📋 Planned
**Target:** Semana 8  
**Status:** ⬜ Not Started

**Objective:** Gestión de inventarios y stock.

**Phases:**
- **Phase 3.1** — Models: Warehouse, Product, StockMovement
- **Phase 3.2** — API endpoints
- **Phase 3.3** — Integration with facturacion (stock deduction)
- **Phase 3.4** — Dashboard + reports

**Success:** Módulo inventory v0.1.0 funcionando.

---

### **M4 — sales Module** 📋 Planned
**Target:** Semana 10  
**Status:** ⬜ Not Started

**Objective:** Cotizaciones → Órdenes → Facturas.

**Phases:**
- **Phase 4.1** — Quotation & SalesOrder models
- **Phase 4.2** — State machine (draft → confirmed → shipped)
- **Phase 4.3** — Generate invoice from order (integrate facturacion)
- **Phase 4.4** — Dashboard sales metrics

**Success:** Módulo sales v0.1.0.

---

### **M5 — Docker & Production** 📋 Planned
**Target:** Semana 11  
**Status:** ⬜ Not Started

**Objective:** Stack Docker listo para producción.

**Phases:**
- **Phase 5.1** — Multi-stage Dockerfile optimizado
- **Phase 5.2** — Docker Compose production (Gunicorn + Nginx)
- **Phase 5.3** — CI/CD GitHub Actions
- **Phase 5.4** — Deploy demo (Railway/Render)

**Success:** `docker-compose up` → ERP Nexus Live en producción.

---

### **M6 — Beta & Polish** 📋 Planned
**Target:** Semana 12  
**Status:** ⬜ Not Started

**Objective:** Release v1.0.0 estable.

**Phases:**
- **Phase 6.1** — Bugfixing (M1-M5)
- **Phase 6.2** — Test coverage >80%
- **Phase 6.3** — Documentation final (INSTALL, DEVELOPMENT, API)
- **Phase 6.4** — Release v1.0.0 + GitHub release

**Success:** v1.0.0 en GitHub, 100+ installations objetivo.

---

## 📋 Phase Details

### **Phase 1.1 — Services Layer (facturacion)**

**Task 1.1.1:** XML Generator con validación XSD
- Implement `services/xml_generator.py`
- Usar Jinja2 templates para factura XML
- Validar contra XSD oficial SRI (minimal XSD para desarrollo)
- Tests unitarios (validación XSD, estructura)

**Task 1.1.2:** Digital Signature (.p12)
- Implement `services/digital_signature.py`
- Usar `cryptography` library (PKCS#12)
- Firmar XML según estándar W3C XML-DSig
- Tests con certificado de pruebas SRI

**Task 1.1.3:** SRI Client (SOAP)
- Implement `services/sri_client.py`
- Cliente SOAP para recepción de comprobantes
- URLsambiente 1 (pruebas) vs 2 (producción)
- Manejo de respuestas (aceptado/rechazado)
- Tests con mock SOAP responses

**Task 1.1.4:** Validator
- Validar RUC (módulo 11)
- Validar cédula (módulo 10)
- Validar totals (subtotal + tax = total)
- Validar invoice number format (001-001-000000001)

**Acceptance Criteria:**
- XML生成器 produce XML válido contra XSD
- Firma digital agrega `<Signature>` node correctamente
- SRI client envía SOAP y parsea respuesta
- Validator rechaza RUC inválido
- Tests >80% coverage en services/

---

### **Phase 1.2 — API Completion**

**Task 1.2.1:** Endpoint send-to-sri
- `POST /api/v1/facturacion/invoices/{id}/send/`
- Trigger XML generation + signature + SRI send
- Update `sri_status` (pending → sent/accepted/rejected)

**Task 1.2.2:** XML download endpoint
- `GET /api/v1/facturacion/invoices/{id}/xml/`
- Return XML as attachment

**Task 1.2.3:** Company isolation validation
- Asegurar que TODOS los endpoints filtran por `request.active_company`
- Tests de cross-company access (forbidden)

**Acceptance Criteria:**
- Crear factura → status pending
- Enviar a SRI (pruebas) → status accepted (mock)
- Download XML → returns firmado
- Cross-company query → 404 (data leak prevented)

---

### **Phase 1.3 — Tests + Validation**

**Task 1.3.1:** Unit tests services
- Mock SRI responses
- Test XML structure
- Test signature verification

**Task 1.3.2:** Integration tests
- Full flow: create → XML → sign → send
- Multi-company isolation tests
- Error scenarios (invalid RUC, SRI down)

**Task 1.3.3:** Security tests
- SQL injection attempts (blocked)
- XSS in customer data (escaped)
- Authorization: user can't access other company data

**Acceptance Criteria:**
- `pytest -q` → all PASS
- Coverage `--cov=facturacion` → >70%
- No high/critical issues in `bandit`

---

### **Phase 1.4 — Extract to Separate Repo**

**Task 1.4.1:** Create `github.com/ERPNexus/facturacion`
- Initialize repo
- Push code from `apps/facturacion/`
- Add README, LICENSE, .gitignore

**Task 1.4.2:** Update core ERP Nexus
- Remove `facturacion` from `modules/`
- Add as git submodule or marketplace install
- Update documentation

**Task 1.4.3:** CI/CD for module
- GitHub Actions (tests + publish .npkg)
- Automated release on tag

**Acceptance Criteria:**
- `facturacion` repo exists on GitHub
- ERP Nexus core installs it via `manage.py install_module --git`
- CI passes on PRs

---

## 🔄 Current Loop Tracking

| Loop | Plan | Apply | Unify | Status |
|------|------|-------|-------|--------|
| M1-P1.1 | ⬜ | ⬜ | ⬜ | Not started |
| M1-P1.2 | ⬜ | ⬜ | ⬜ | Not started |
| M1-P1.3 | ⬜ | ⬜ | ⬜ | Not started |
| M1-P1.4 | ⬜ | ⬜ | ⬜ | Not started |

---

**PAUL ROADMAP.md:** Initialized  
**Next:** Run `/paul:plan 1.1` to create executable plan for Phase 1.1
