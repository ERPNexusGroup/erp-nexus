# ADR-006: Plugin Architecture — Core + Módulos Independientes

**Estado:** ✅ Aceptado  
**Fecha:** 2026-05-10  
**Contexto:** Fase 0.6 — Restructure  
**Decisores:** Walter Cun, ERP Nexus Team

---

## 📋 Contexto

¿Cómo estructurar ERP Nexus para soportar módulos de negocio (facturación, inventario, ventas)?

### **Problema:**
El código actual mezcla core framework con módulos de negocio en un solo repo:
```
erp-nexus/
├── apps/              # Core framework
├── modules/
│   ├── facturacion_ec/   # ❌ Debería ser externo
│   ├── accounting_basic/ # ❌ Demo, no debería estar
│   └── inventory_basic/  # ❌ Demo, no debería estar
```

**Consecuencia:**
- ❌ No hay verdadera modularidad (todo en un repo)
- ❌ Imposible instalar solo facturación sin inventory
- ❌ Updates de un módulo requieren deploy completo
- ❌ Módulos de terceros difícil de empaquetar

---

## 🎯 Decisión

**Plugin-based Architecture (Django Apps como Plugins)**

### **Core (erp-nexus/):**
- Framework Django minimalista
- NO contiene módulos de negocio
- Contiene ModuleRegistry (catálogo + instalador)
- Expone APIs para plugins
- Event Bus para comunicación

### **Plugins (repos separados):**
- Cada módulo es repo Git independiente
- Son Django Apps estándar
- Se instalan/desinstalan en caliente
- Versionado independiente
- Dependen del core (no al revés)

---

## 🏗️ Arquitectura

```
┌──────────────────────────────────────────────┐
│          ERP Nexus Ecosystem                 │
├──────────────────────────────────────────────┤
│                                              │
│  ┌───────────────────────────────────────┐ │
│  │  CORE (erp-nexus repo)                │ │
│  │  - Django framework                   │ │
│  │  - Multi-tenant middleware            │ │
│  │  - ModuleRegistry (DB + installer)    │ │
│  │  - Event Bus                          │ │
│  │  - API layer (Django Ninja)           │ │
│  │  - Admin panel                        │ │
│  └───────────────────────────────────────┘ │
│                     │                        │
│                     │ plugins install        │
│                     ▼                        │
│  ┌───────────────────────────────────────┐ │
│  │  Plugin: facturacion_ec               │ │
│  │  (repo separado)                      │ │
│  │  - models.py                          │ │
│  │  - api/routes.py                      │ │
│  │  - services/                          │ │
│  └───────────────────────────────────────┘ │
│                     │                        │
│                     │ plugins install        │
│                     ▼                        │
│  ┌───────────────────────────────────────┐ │
│  │  Plugin: inventory                    │ │
│  │  (repo separado)                      │ │
│  │  - models.py                          │ │
│  │  - api/routes.py                      │ │
│  └───────────────────────────────────────┘ │
│                                              │
│  Runtime: Core + Plugins cargados en        │
│           INSTALLED_APPS dinámicamente      │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 📦 Estructura de un Plugin

```
facturacion_ec/                # Repo Git
├── facturacion_ec/            # Django app
│   ├── __init__.py
│   ├── apps.py               # AppConfig
│   ├── models.py
│   ├── admin.py
│   ├── urls.py
│   ├── api/routes.py         # API endpoints
│   ├── services/             # Business logic
│   ├── templates/
│   ├── static/
│   ├── tests/
│   └── __meta__.py           # Metadata (requerido)
│
├── README.md
├── LICENSE
├── pyproject.toml            # Dependencias
└── .github/workflows/ci.yml
```

**`__meta__.py`:**
```python
MODULE_META = {
    "technical_name": "facturacion_ec",
    "version": "0.1.0",
    "depends": ["core_companies>=0.5.0"],
    "min_erp_version": "0.5.0",
    "repo": "https://github.com/ERPNexus/facturacion_ec",
}
```

---

## 🔄 Installation Flow

```bash
# Admin instala plugin
$ python manage.py install_module --git https://github.com/ERPNexus/facturacion_ec.git

# Internamente:
1. Clona a ~/.erp-nexus/modules/facturacion_ec/
2. Valida __meta__.py
3. Crea Module record en DB
4. Añade "facturacion_ec" a INSTALLED_APPS (runtime)
5. Ejecuta: manage.py migrate facturacion_ec
6. Emite evento: module.installed
```

---

## ✅ Ventajas

| Ventaja | Explicación |
|---------|-------------|
| **Modularidad real** | Core no contiene código de negocio |
| **Versionado independiente** | facturacion_ec v1.0 puede existir sin core v1.0 |
| **Plugins de terceros** | Cualquier developer puede crear plugin |
| **Instalación selectiva** | Cliente instala solo lo que necesita |
| **CI/CD aislado** | Cada plugin tiene su propio pipeline |
| **Rollback fácil** | Desinstalar plugin = eliminar directorio |

---

## ⚠️ Trade-offs

| Trade-off | Mitigación |
|-----------|------------|
| **Más repos** (6+) | GitHub organization agrupa todo |
| **Dependencias cross-repo** | SemVer estricto, compatibility matrix |
| **Developer setup** | `sdk-nexus bootstrap` clona todo |
| **Core change rompe plugins** | Deprecation warnings, 2-cycle policy |

---

## 🔗 Alternativas Consideradas

### **Alt A: Monorepo (actual)**
- ❌ Rechazado: No hay true modularity
- Todos los módulos en `modules/` dentro core
- Deploy todo-o-nada

### **Alt B: Python Packages (PyPI)**
- ✅ Considerado: plugins como `pip install facturacion_ec`
- ❌ Problema: Django apps necesitan estar en INSTALLED_APPS
- ✅ Solución: Package includes Django app, install via `pip` luego `INSTALLED_APPS += [...]`

**Decisión:** Git-based install (`install_module --git`) + PyPI opcional.

---

## 📋 Implementation Tasks

**Phase 0.6 — Multi-Repo Separation:**
1. Extraer `facturacion_ec/` a repo separado (`repos/facturacion_ec/`)
2. Eliminar módulos demo (`accounting_basic`, `inventory_basic`, `demo_flow`)
3. Limpiar core settings (remover references a `modules/`)
4. Eliminar `modules_enabled.py` estático
5. Documentar arquitectura plugin

---

## 🔮 Futuro

- **v0.7.x** — Marketplace UI (catálogo de plugins)
- **v0.8.x** — SDK (`sdk-nexus`) para crear plugins
- **v0.9.x** — Plugin auto-update
- **v1.0.0** — 3+ plugins oficiales + marketplace estable

---

**Referencias:**
- `ARCHITECTURE_PLUGIN.md` — Guía completa
- `MODULE_SPEC.md` — Contrato técnico de plugins
- `MULTI_REPO_STRUCTURE.md` — Organización de repos
