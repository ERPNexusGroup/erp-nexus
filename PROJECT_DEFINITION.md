# 📋 Definición del Proyecto — ERP Nexus

**Proyecto:** ERP Nexus Framework  
**Versión:** 1.0.0-alpha  
**Fecha de creación:** 2026-05-10  
**Estado:** En desarrollo activo — Fase 1  
**Licencia:** MIT  
**Mantenedor:** ERP Nexus Team  
**URL:** `github.com/ERPNexus/erp-nexus`

---

## 🎯 ¿Qué es ERP Nexus?

ERP Nexus es un **framework Django modular** para construir sistemas ERP desde bloques independientes.

### **Problema que resuelve:**
Los ERP tradicionales son monolíticos: todo el código en un solo repo, despliegue conjunto, imposible elegir módulos. ERP Nexus separa el **core framework** de los **módulos de negocio**, permitiendo:
- Instalar solo lo que necesitas
- Actualizar módulos independientemente
- Crear módulos custom sin tocar el core
- Marketplace de módulos (gratuitos + de pago)

### **Analogía:**
- **ERP Nexus Core** → WordPress (framework)
- **Módulos** → Plugins de WordPress
- **Marketplace** → Directorio de plugins
- **Cliente** → Instala solo Facturación + Inventario (no necesita HR ni CRM)

---

## 🏗️ Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTE (Empresa)                         │
│  Usa: Facturación + Inventario + Ventas (solo lo que necesita)  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│               ERP NEXUS CORE (Framework)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Django + Config + Multi-tenant + Marketplace Engine     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Module Registry — Catálogo + Instalador                  │  │
│  │  [facturacion_ec] [inventory] [sales] ...               │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  MÓDULO A       │  │  MÓDULO B       │  │  MÓDULO C       │
│  facturacion_ec │  │  inventory      │  │  sales          │
│                 │  │                 │  │                 │
│  (Git repo)     │  │  (Git repo)     │  │  (Git repo)     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## 🎯 Objetivos del Proyecto

### **Primario:**
1. **Framework modular** — Core mínimo, módulos opcionales
2. **Multi-tenant nativo** — Una instancia, múltiples empresas
3. **Marketplace integrado** — Descargar/activar módulos desde UI
4. **Extensible por terceros** — Cualquier dev puede crear módulos

### **Secundarios:**
5. **API-first** — Todo exponible vía REST/GraphQL
6. **Seguro por defecto** — Validación company, permisos granulares
7. **Escalable** — 100+ empresas en un solo servidor
8. **Documentado** — Cada módulo tiene su README + API docs

---

## 📉 Fuera del Alcance (v1.0)

❌ **NO incluye:**
- Frontend SPA (React/Vue) — Solo admin Django (Jazzmin)
- Módulos: CRM, HR, Manufacturing, Projects
- Mobile app nativa
- Integraciones bancarias/pasarelas
- AI/ML features (post v1.0)
- Multi-idioma (i18n) — Español únicamente (v1.x)

---

## 👥 Público Objetivo

| Segmento | Necesidad | Módulos que usará |
|----------|-----------|-------------------|
| **Empresas Ecuador** | Facturación electrónica SRI | facturacion_ec, inventory, sales |
| **Startups latinoamérica** | ERP liviano | Core + 2-3 módulos |
| **Desarrolladores** | Extender ERP | Crear módulos custom |
| **Consultores** | Implementar para clientes | Varios módulos + customización |

---

## 🏆 Visión a Largo Plazo

**Año 1 (v1.x):**
- Core estable + 5 módulos oficiales
- 100 instalaciones activas
- Marketplace con 10+ módulos community

**Año 2 (v2.x):**
- Frontend React (SPA)
- Mobile app (React Native)
- Integración bancaria automática
- AI para预测 compras

**Año 3 (v3.x):**
- 1000+ empresas usando ERP Nexus
- Marketplace de módulos de pago
- Certified partner program
- SaaS multi-tenant hosting propio

---

## 💰 Modelo de Negocio

### **Open Core:**
- **Core ERP Nexus:** MIT (gratuito, open source)
- **Módulos oficiales:**
  - `facturacion_ec` — Freemium (10 facturas/mes gratis)
  - `inventory` — Gratis (sin límite)
  - `sales` — Gratis (sin límite)
  - `accounting` — De pago ($29/mes)

### **Marketplace:**
- Módulos community → gratuitos
- Módulos certified → revisados por ERP Nexus
- Módulos enterprise → con soporte SLA

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Razón |
|------|------------|-------|
| **Backend** | Django 5.x + Python 3.12 | Madurez, ecosistema, ORM |
| **API** | Django Ninja | FastAPI-like, OpenAPI autogenerado |
| **DB** | PostgreSQL 15+ | ACID, JSONField, GIS opcional |
| **Cache** | Redis | Sesiones, cache queries |
| **Colas** | Celery + Redis | Tareas asíncronas (facturación masiva) |
| **Auth** | Django JWT (simplejwt) | Tokens stateless |
| **Admin** | Jazzmin | Theme moderno, responsive |
| **Docs** | MkDocs / OpenAPI Swagger | Documentación viva |
| **Tests** | pytest + pytest-django | Cobertura >80% |
| **CI/CD** | GitHub Actions | Automatización tests + deploy |
| **Docker** | Docker + docker-compose | Deploy multi-service |
| **Monitoring** | Sentry (opcional) | Error tracking |

---

## 📁 Estructura Final del Repo

```
erp-nexus/                    # ERP Nexus Core
├── apps/                     # 11 core apps
│   ├── core_auth/
│   ├── core_companies/
│   ├── core_marketplace/
│   └── ...
├── erp_nexus/
│   ├── __init__.py
│   ├── settings.py           # Config centralizada
│   ├── urls.py               # URLs core
│   ├── wsgi.py
│   ├── asgi.py
│   └── modules_enabled.py    # AUTO-GENERADO (no editar)
├── modules/                  # ⚠️  SOLO development: módulos locales
│   └── facturacion_ec/       # (en prod se instalan desde marketplace)
├── docs/                     # Documentación del core
├── tests/                    # Tests core (marketplace, middleware)
├── scripts/                  # Scripts util (install_module, etc.)
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml            # Tests + lint en cada PR
├── pyproject.toml            # Dependencias Python (uv)
├── requirements.txt          # Para producción
├── manage.py
├── README.md                 # Página principal
├── ARCHITECTURE.md           # Diseño técnico
├── REQUIREMENTS.md           # Requisitos funcionales/no-funcionales
├── CODING_STANDARDS.md       # Reglas de código
├── MODULE_SPEC.md            # Cómo construir módulos
├── WORK_PLAN.md              # Roadmap temporal
└── LICENSE (MIT)
```

---

## 🎓 Cómo Empezar a Desarrollar

### **Setup en 5 minutos:**
```bash
# 1. Clone el repo
git clone https://github.com/ERPNexus/erp-nexus.git
cd erp-nexus

# 2. Instalar dependencias
uv sync
uv pip install -e .

# 3. Aplicar migraciones
uv run python manage.py migrate

# 4. Crear superusuario
uv run python manage.py createsuperuser

# 5. Levantar servidor
uv run python manage.py runserver
# → http://localhost:8000/admin
```

### **Crear un módulo nuevo:**
```bash
# Usar cookiecutter template
uv run python scripts/create_module.py mi_modulo

# O manualmente: copiar modules/ejemplo_modulo/ → modules/mi_modulo/
# Editar __meta__.py, models.py, etc.
# Registrar en marketplace/admin
```

---

## 📚 Documentación

| Documento | Propósito | Ubicación |
|-----------|-----------|-----------|
| `README.md` | Introducción + quickstart | Raíz |
| `ARCHITECTURE.md` | Diseño técnico, diagramas | Raíz |
| `REQUIREMENTS.md` | Requisitos funcionales/no-funcionales | Raíz |
| `CODING_STANDARDS.md` | Reglas de codificación | Raíz |
| `MODULE_SPEC.md` | Cómo crear módulos | Raíz |
| `WORK_PLAN.md` | Roadmap temporal | Raíz |
| `docs/` | Guías detalladas | `/docs/` |
| `API Reference` | Documentación interactiva | `/api/v1/docs` |

---

## 🤝 Cómo Contribuir

1. **Fork** el repo
2. **Crear branch** (`feat/mi-feature` o `fix/issue-123`)
3. **Seguir CODING_STANDARDS.md**
4. **Tests** — Añadir tests para cambios
5. **Commit** — Conventional Commits
6. **PR** — Describir cambios + referencia issue

**Ver:** `CONTRIBUTING.md` (próximo a crearse)

---

## 📄 Licencia

MIT License — Ver `LICENSE`

```
Copyright (c) 2026 ERP Nexus Team

Se concede permiso, libre de cargos, a cualquier persona que obtenga una copia
de este software y de la documentación asociada (el "Software"), a utilizar
el Software sin restricción, incluyendo sin limitación los derechos a usar,
copiar, modificar, fusionar, publicar, distribuir, sublicenciar, y/o vender
copias del Software...
```

---

## 📞 Soporte y Contacto

- **Issues:** `github.com/ERPNexus/erp-nexus/issues`
- **Discussions:** `github.com/ERPNexus/erp-nexus/discussions`
- **Email:** dev@erpnexus.ec
- **Website:** `erpnexus.ec` (futuro)
- **Telegram:** @erpnexus_support (futuro)

---

## 🎯 Próximos Pasos Inmediatos

1. ✅ Documentación base creada (este documento + architecture, coding, module spec)
2. 🔄 **AHORA:** Re-estructurar código existente según arquitectura definida
   - Mover `facturacion_ec` a repo externo
   - Dejar en `erp-nexus/` solo core
   - Implementar marketplace engine
3. 📝 Escribir `CONTRIBUTING.md`
4. 🐳 Crear `docker-compose.yml` completo
5. 🚀 Deploy demo en Railway/Render

---

**¿Listo para empezar?** → Ver `WORK_PLAN.md` para roadmap detallado.
