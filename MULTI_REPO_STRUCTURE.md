# 📁 Estructura Multi-Repo — ERP Nexus (Hybrid Model)

**Versión:** 1.0.0-alpha  
**Fecha:** 2026-05-10  
**Arquitectura:** Hybrid — Essential modules en core, Optional modules como plugins

---

## 🎯 Filosofía

ERP Nexus usa **modelo híbrido**:

### **Tier 1 — Core Repository (`erp-nexus/`)**
Contiene **todo lo esencial** para un ERP funcional:

```
erp-nexus/                    # Core repo (único necesario para MVP)
├── apps/                     # 19 Django apps
│   ├── core_users/           # Framework
│   ├── core_companies/       # Framework
│   ├── core_events/          # Framework
│   ├── core_api/             # Framework
│   ├── core_marketplace/     # Framework
│   │
│   ├── facturacion/          # Essential — Integrated
│   ├── inventory/            # Essential — Integrated
│   ├── sales/                # Essential — Integrated
│   ├── purchases/            # Essential — Integrated
│   ├── notifications/        # Essential — Integrated
│   ├── permissions/          # Essential — Integrated
│   ├── dashboard/            # Essential — Integrated
│   └── print_manager/        # Essential — Integrated
│
├── erp_nexus/
├── docker/
├── README.md
└── (archivos core)
```

**Instalación básica:**
```bash
git clone https://github.com/ERPNexus/erp-nexus.git
cd erp-nexus
uv sync
python manage.py migrate  # Crea TODAS las tablas (facturacion, inventory, …)
python manage.py runserver
# → ERP completo funcionando
```

**No necesitas instalar plugins** para facturar o gestionar inventario.

---

### **Tier 2 — Optional Plugin Repos (extensions)**

Estos módulos **NO están en el core**. Se instalan via Marketplace:

```
Organización GitHub: ERPNexus/
│
├── erp-nexus/              ← CORE (framework + essential) ⬅ USADO POR TODOS
│
├── hr/                     ← PLUGIN opcional
│   ├── hr/
│   ├── README.md
│   └── __meta__.py
│
├── accounting_adv/         ← PLUGIN opcional
├── crm/                    ← PLUGIN opcional
├── project_mgmt/           ← PLUGIN opcional
├── pos/                    ← PLUGIN opcional
├── ecommerce/              ← PLUGIN opcional
│
└── sdk-nexus/              ← SDK (dev tools)
    └── nexus-cli/          ← CLI tool
```

**Instalación de plugin:**
```bash
# Sobre core ya instalado
python manage.py install_module --git https://github.com/ERPNexus/hr.git
python manage.py migrate hr
```

---

## 📦 Cuándo Usar Cada Tipo

### **Essential Modules (en core):**
| Módulo | Ubicación | ¿Desinstalable? |
|--------|-----------|-----------------|
| facturacion | `apps/facturacion/` | ❌ NO |
| inventory | `apps/inventory/` | ❌ NO |
| sales | `apps/sales/` | ❌ NO |
| purchases | `apps/purchases/` | ❌ NO |
| notifications | `apps/notifications/` | ❌ NO |
| permissions | `apps/permissions/` | ❌ NO |
| dashboard | `apps/dashboard/` | ❌ NO |
| print_manager | `apps/print_manager/` | ❌ NO |

**Razón:** Son funciones core de cualquier ERP. Todo negocio necesita facturar, llevar inventario, gestionar ventas.

---

### **Optional Plugins (repos separados):**
| Plugin | Repo | ¿Desinstalable? |
|--------|------|-----------------|
| hr | `github.com/ERPNexus/hr` | ✅ SÍ |
| accounting_adv | `github.com/ERPNexus/accounting_adv` | ✅ SÍ |
| crm | `github.com/ERPNexus/crm` | ✅ SÍ |
| project_mgmt | `github.com/ERPNexus/project_mgmt` | ✅ SÍ |
| pos | `github.com/ERPNexus/pos` | ✅ SÍ |
| ecommerce | `github.com/ERPNexus/ecommerce` | ✅ SÍ |

**Razón:** Son verticales/industria específicos. No todas las empresas los necesitan.

---

## 🗺️ Estructura de Directorios (local dev)

```
/home/wcun/.openclaw/workspace/
├── repos/
│   ├── erp-nexus/          ← CORE (clonado)
│   │   ├── apps/
│   │   │   ├── core_users/
│   │   │   ├── facturacion/
│   │   │   └── ...
│   │   └── erp_nexus/
│   │
│   ├── facturacion_ec/     ❌ YA NO EXISTE (fusionado en core)
│   ├── inventory/          ❌ YA NO EXISTE (fusionado en core)
│   │
│   ├── hr/                 ← PLUGIN (futuro, clonar cuando se necesite)
│   ├── crm/                ← PLUGIN (futuro)
│   └── sdk-nexus/          ← SDK (dev)
│
└── .erp-nexus/             ← Runtime (datos, módulos instalados)
    ├── media/
    └── logs/
```

---

## 🔄 Workflow de Desarrollo

### **Desarrollar Core (essential modules incluidos):**
```bash
cd repos/erp-nexus/
# Editar apps/facturacion/...
pytest apps/facturacion/tests/
git commit -m "feat(facturacion): add SRI validation"
```

### **Desarrollar Plugin Opcional (hr, crm, …):**
```bash
# Clonar plugin separado
git clone https://github.com/ERPNexus/hr.git
cd hr
# Desarrollar independientemente
pytest hr/tests/
git tag -a v0.1.0
git push origin v0.1.0
# Publicar en GitHub → aparece en Marketplace
```

### **Instalar Plugin en Dev:**
```bash
cd repos/erp-nexus
python manage.py install_module ../hr/
```

---

## 🆚 Comparación con Otras Estrategias

| Estrategia | Core Contiene | Plugins | Ventaja | Desventaja |
|------------|---------------|---------|---------|------------|
| **Plugin-Only** | Solo framework | TODO es plugin | Max modularidad | Fricciónalta (instalar 5+ plugins para ERP funcional) |
| **Monorepo Todo** | Framework + todos módulos | Ninguno | Simple | No extensible, deploy todo-o-nada |
| **Hybrid (nosotros)** | Framework + Essential | Optional extensions | ✅ Balance perfecto | Core más grande (pero organizado) |

---

## 📋 Check: Essential vs Optional

**Pregunta clave:** ¿Este módulo es esencial para que unERP sea un ERP?

| Módulo | ¿Essential? | Razón |
|--------|-------------|-------|
| Facturación | ✅ SÍ | Todo ERP factura |
| Inventario | ✅ SÍ | Todo ERP lleva stock |
| Ventas | ✅ SÍ | Todo ERP tiene ventas |
| Compras | ✅ SÍ | Todo ERP tiene compras |
| Notificaciones | ✅ SÍ | Comunicación core |
| Permisos | ✅ SÍ | Seguridad core |
| Dashboard | ✅ SÍ | Vista unificada |
| Print Manager | ✅ SÍ | Documentos PDF |
| HR | ❌ NO | No todas las empresas tienen empleados |
| CRM | ❌ NO | Solo algunas necesitan pipeline complejo |
| contabilidad avanzada | ❌ NO | Especializado |
| POS | ❌ NO | Solo retail |

---

## 🔧 Para Desarrolladores de Plugins

### **Crear un plugin opcional:**
```bash
# Usar SDK (futuro)
sdk-nexus create my_plugin --type=extension

# O manual: clonar template
cp -r erp-nexus/_template_module/ my_plugin/
cd my_plugin
# Editar __meta__.py, apps.py, models.py
```

### **Publicar plugin:**
```bash
git init
git remote add origin git@github.com:ERPNexus/my_plugin.git
git push -u origin main
#自动 aparece en Marketplace (cuando Marketplace esté activo)
```

### **Instalar plugin:**
```bash
python manage.py install_module --git https://github.com/ERPNexus/my_plugin.git
```

---

## ❌ Qué NO es esta arquitectura

- ❌ **NO** es plugin-only (WordPress style)
- ❌ **NO** es monorepo con todo mezclado
- ✅ **ES** Hybrid: Core con essential modules + optional plugins externos

---

## 🔗 Related

- `ARCHITECTURE_HYBRID.md` — Guía arquitectónica principal
- `ADR/007-hybrid-architecture.md` — Decisión arquitectónica
- `PROJECT_DEFINITION.md` — Scope del proyecto
- `MODULE_SPEC.md` — Contratos para Essential vs Optional modules

---

**Nota:** Este documento reemplaza la visión anterior de multi-repo completa. Ahora solo los **plugins opcionales** viven en repos separados. Los **módulos esenciales** viven en `erp-nexus/apps/`.
