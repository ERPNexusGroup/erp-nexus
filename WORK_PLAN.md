# 🗺️ Plan de Trabajo — ERP Nexus

**Versión:** 1.0.0-alpha  
**Fecha:** 2026-05-10  
**Duración totalestimada:** 12 semanas  
**Meta:** Release v1.0.0 estable

---

## 🎯 Fases del Proyecto

### **FASE 0 — Definición y Setup (Semana 1)** ✅ COMPLETADO

| Tarea | Estado | Entregable |
|-------|--------|------------|
| Definir arquitectura modular | ✅ | `ARCHITECTURE.md` |
| Especificación de módulos | ✅ | `MODULE_SPEC.md` |
| Reglas de codificación | ✅ | `CODING_STANDARDS.md` |
| Requisitos funcionales | ✅ | `REQUIREMENTS.md` |
| Core base Django configurado | ✅ | 11 apps core |
| Marketplace engine | ✅ | Registro/activación módulos |
| Sistema multi-tenant | ✅ | `ActiveCompanyMiddleware` |

---

### **FASE 1 — Módulo Demostración: facturacion_ec (Semanas 2-4)** 🔥 ACTUAL

**Objetivo:** Tener un módulo completo y funcional como referencia.

#### **Semana 2: Modelos + Admin**
- [x] 10 modelos creados (LicenseType, Customer, Product, Invoice, etc.)
- [x] Admin Django personalizado
- [x] Migraciones aplicadas
- [ ] **Documentar** estructura de modelos
- [ ] **Tests unitarios** modelos (70% cobertura)

#### **Semana 3: Servicios Core**
- [ ] `xml_generator.py` — Generación XML SRI
- [ ] `digital_signature.py` — Firma con certificado .p12
- [ ] `validator.py` — Validación RUC, cédula, totals
- [ ] `sri_client.py` — Cliente SOAP para API SRI
- [ ] **Tests** servicios (mocks de SRI)

#### **Semana 4: API + Integración**
- [ ] 7 endpoints REST funcionando
- [ ] Integración end-to-end (crear → XML → firma → envío)
- [ ] **Pendiente:** Certificado SRI pruebas
- [ ] **Demo pública** (Docker + datos de prueba)
- [ ] Documentación API (Swagger)

**Entregable Semana 4:**
- Módulo `facturacion_ec` v0.1.0 completo
- API documentada en `/api/v1/docs`
- Video demo de flujo factura → SRI

---

### **FASE 2 — Refactorización y Estabilidad (Semanas 5-6)**

#### **Objetivos:**
1. **Extraer facturacion_ec a repo separado**
   - [ ] Crear `github.com/ERPNexus/facturacion_ec`
   - [ ] Mover código del módulo
   - [ ] Configurar CI/CD independiente
   - [ ] Actualizar Marketplace para discovering externo

2. **Mejorar instalador de módulos**
   - [ ] `ModuleInstaller` class (descarga git, verifica, instala)
   - [ ] Rollback en caso de fallo
   - [ ] Actualizaciones in-place
   - [ ] Validación de dependencias

3. **Licenciamiento y pagos (opcional)**
   - [ ] Sistema de licencias por módulo
   - [ ] Integración Stripe (para módulos de pago)
   - [ ] Validación de licencia en runtime

---

### **FASE 3 — Módulo Inventory (Semanas 7-8)**

**Objetivo:** Implementar gestión de inventarios.

#### **Semana 7: Modelos + Core**
- [ ] Models: `Warehouse`, `Product`, `StockMovement`, `InventoryAdjustment`
- [ ] Admin + CRUD básico
- [ ] Migraciones
- [ ] Services: `adjust_stock()`, `transfer_between_warehouses()`

#### **Semana 8: API + Features**
- [ ] API: list/createdetail products
- [ ] API: stock movements (ingress/egress/transfer)
- [ ] Dashboard: resumen inventario por warehouse
- [ ] Reports: stock levels, movements history

**Entregable:** Módulo `inventory` v0.1.0

---

### **FASE 4 — Módulo Sales (Semanas 9-10)**

**Objetivo:** Cotizaciones → Órdenes → Facturas (integración con facturacion_ec).

#### **Semana 9: Cotizaciones + Órdenes**
- [ ] Models: `Quotation`, `QuotationLine`, `SalesOrder`, `SalesOrderLine`
- [ ] Flujo: Quote → Order (estados: draft/confirmed/shipped)
- [ ] Cálculo de totales + impuestos
- [ ] Integración con inventory (reservar stock)

#### **Semana 10: Facturación desde Órdenes**
- [ ] Generar factura desde SalesOrder
- [ ] Actualizar inventory (stock consumido)
- [ ] Dashboard: ventas por período, por vendedor
- [ ] Reports mensuales

**Entregable:** Módulo `sales` v0.1.0

---

### **FASE 5 — Docker + Despliegue (Semana 11)**

#### **Objetivo:** Dockerizar todo el stack.

- [ ] `Dockerfile` core ERP Nexus
- [ ] `docker-compose.yml` con:
  - PostgreSQL + Redis
  - ERP Nexus (Gunicorn + Nginx)
  - Celery workers (opcional)
  - Flower (monitor Celery)
- [ ] `docker-compose.dev.yml` para desarrollo
- [ ] Scripts: `docker-build.sh`, `docker-push.sh`
- [ ] README deployment
- [ ] Deploy demo en Railway/Render

**Entregable:** Stack Docker listo, deploy de prueba público

---

### **FASE 6 — Beta + Polishing (Semana 12)**

#### **Objetivo:** Estabilizar y documentar.

- [ ] Bugfixing de Fases 1-5
- [ ] Mejorar cobertura tests (>80%)
- [ ] Escribir guías:
  - `INSTALL.md` — Instalación desde cero
  - `DEVELOPMENT.md` — Guía desarrolladores módulos
  - `API_REFERENCE.md` — Docs API completas
  - `MODULE_DEVELOPMENT.md` — Cómo crear módulos
- [ ] Demo video (5 min)
- [ ] Preparar release v1.0.0
- [ ] Crear GitHub Discussions/Issues templates

---

## 📊 Timeline (Gantt simplificado)

```
Semana:  1    2    3    4    5    6    7    8    9    10   11   12
         ────────────────────────────────────────────────────────────
FASE 0   ████████████
FASE 1           ████████████████████████  ← Estamos aquí
FASE 2                       ██████████████
FASE 3                               ██████████████
FASE 4                                       ██████████████
FASE 5                                               ██████████████
FASE 6                                                       ██████████████
Release                                                       │ v1.0.0
```

---

## 🎯 Hitos (Milestones)

| Hito | Fecha | Entregable |
|------|-------|------------|
| **M0** — Core funcional | Semana 1 | 11 apps + marketplace |
| **M1** — facturacion_ec demo | Semana 4 | Módulo completo + API |
| **M2** — Módulo separado | Semana 6 | Repo independiente facturacion_ec |
| **M3** — Inventory listo | Semana 8 | Módulo inventory v0.1 |
| **M4** — Sales listo | Semana 10 | Módulo sales v0.1 |
| **M5** — Docker listo | Semana 11 | Stack Docker funcional |
| **M6** — Release v1.0.0 | Semana 12 | GitHub estable + docs |

---

## 📋 Tablero de Tareas (Trello/Linear-style)

### **Sprint Actual (FASE 1 — Semana 3)**

| Tarea | Prioridad | Estimación | Estado |
|-------|-----------|------------|--------|
| XML generator (XSD SRI) | Alta | 8h | ⬜ Pendiente |
| Firma digital (.p12) | Alta | 6h | ⬜ Pendiente |
| SRI client (SOAP) | Alta | 8h | ⬜ Pendiente |
| Validator (RUC/cedula) | Media | 4h | ⬜ Pendiente |
| Tests unitarios servicios | Media | 8h | ⬜ Pendiente |
| Integración end-to-end | Alta | 6h | ⬜ Pendiente |

**Total Sprint:** ~40 horas

---

## 🔄 Workflow Semanal

```
Lunes
├── Planning: qué hacer esta semana
├── Revisar avance FASE anterior
└── Actualizar WORK_PLAN.md

Martes - Jueves
├── Desarrollo focused (coding)
├── Tests diarios
└── Commits diarios

Viernes
├── Demo de lo hecho
├── Documentar
├── Commit final semana
└── Revisión Next sprint
```

---

## 📈 Métricas de Progreso

| Métrica | Actual | Objetivo (Sem 4) | Objetivo (Sem 12) |
|---------|--------|------------------|-------------------|
| Apps core | 11/11 ✅ | 11/11 | 11/11 |
| Módulos completos | 1/3 | 1/3 | 3/3 |
| Tests unitarios | ~20% | >70% | >80% |
| Cobertura API | 40% | >80% | >90% |
| Docs | 30% | 60% | 100% |

---

## 🚨 Bloqueos y Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Certificado SRI no disponible | Media | Alto | Modo pruebas sin certificado; mock SRI |
| API SRI inestable | Baja | Alto | Retry logic + cola de reintentos |
| Complejidad multi-tenant | Media | Alto | Tests multi-company exhaustivos |
| Módulos muy acoplados | Media | Medio | Enforce ModuleSpec, code reviews |
| Equipo limitado (1 persona) | Alta | Alto | Enfocarse en MVP,少 scope creep |

---

## 💡 Decisiones Pendientes

1. **¿Dockerizar módulos también?**
   - Sí: Cada módulo tiene su Dockerfile
   - No: Solo core se dockeriza, módulos como Python packages

2. **¿Soporte multi-db (PostgreSQL + MySQL)?**
   - Prioridad PostgreSQL (recomendado)
   - MySQL como v1.1

3. **¿Async tasks (Celery)?**
   - Sí: Para envíos SRI, reportes, emails
   - No: Sync suficiente para MVP (<100 facturas/día)

4. **¿Frontend público?**
   - Post v1.0: React/Vue SPA
   - v1.0: Solo admin + API

---

## 📞 Contacto y Comunicación

- **Repositorio principal:** `github.com/ERPNexus/erp-nexus`
- **Discusiones:** GitHub Discussions
- **Issues:** GitHub Issues (bug reports, feature requests)
- **Wiki:** Documentación detallada
- **Demo:** `demo.erpnexus.ec` (después de Fase 5)

---

## ✅ Checklist de Revisiones Semanales

**Cada viernes:**
- [ ] ¿Avanzamos según plan?
- [ ] ¿Qué se bloqueó esta semana?
- [ ] ¿Necesitamos ajustar scope/estimaciones?
- [ ] Documentar decisiones tomadas
- [ ] Actualizar WORK_PLAN.md

---

**Última actualización:** 2026-05-10 — Iniciando FASE 1 (facturacion_ec)
