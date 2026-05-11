# 📚 Documentation — Developer/Architecture

Esta carpeta contiene **toda la documentación técnica** de ERP Nexus para desarrolladores.

## 📂 Estructura

| Archivo | Propósito |
|---------|-----------|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Diseño técnico global del sistema (core, modules, event bus, multi-tenant) |
| [`ARCHITECTURE_HYBRID.md`](ARCHITECTURE_HYBRID.md) | Arquitectura híbrida: módulos esenciales integrados vs. plugins |
| [`ARCHITECTURE_PLUGIN.md`](ARCHITECTURE_PLUGIN.md) | Sistema de plugins marketplace (instalación, catálogo, dependencias) |
| [`MODULE_SPEC.md`](MODULE_SPEC.md) | Cómo construir un módulo ERP Nexus (structure, `__meta__.py`, hooks) |
| [`MODULE_INTEGRATION_STATUS.md`](MODULE_INTEGRATION_STATUS.md) | Tabla de módulos: estado, ubicación, dependencias |
| [`GRAPH_HEALTH.md`](GRAPH_HEALTH.md) | Diagnóstico del grafo de conocimiento (Graphify) y salud del codebase |
| [`API_REFERENCE.md`](API_REFERENCE.md) | Referencia completa de endpoints REST (Django Ninja) |
| [`CODING_STANDARDS.md`](CODING_STANDARDS.md) | Estilos de código, convenciones, linters, commits |
| [`DEVELOPMENT.md`](DEVELOPMENT.md) | Guía para desarrolladores: setup local, debugging, testing |
| [`REQUIREMENTS.md`](REQUIREMENTS.md) | Requerimientos funcionales y no-funcionales del sistema |
| [`WORK_PLAN.md`](WORK_PLAN.md) | Roadmap, milestones, tareas pendientes |
| [`PROJECT_DEFINITION.md`](PROJECT_DEFINITION.md) | Definición del proyecto: objetivos, alcance, stakeholders |
| [`MULTI_REPO_STRUCTURE.md`](MULTI_REPO_STRUCTURE.md) | Estructura multi-repo, sync, git submodules/monorepo strategy |
| [`INSTALL.md`](INSTALL.md) | Guía de instalación paso a paso (local, Docker, producción) |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Cómo contribuir: workflow, PR checklist, code review |
| [`DOCS_INDEX.md`](DOCS_INDEX.md) | Índice general de toda la documentación del proyecto |

## 🎯 Cuándo usar qué

| Necesidad | Archivo |
|-----------|---------|
| Entender la arquitectura global | `ARCHITECTURE.md` |
| Saber cómo construir un módulo | `MODULE_SPEC.md` |
| Ver estado de integración de módulos | `MODULE_INTEGRATION_STATUS.md` |
| Desarrollar features nuevas | `DEVELOPMENT.md` + `CODING_STANDARDS.md` |
| Reportar bugs o enviar PRs | `CONTRIBUTING.md` |
| Consultar API endpoints | `API_REFERENCE.md` |
| Revisar roadmap | `WORK_PLAN.md` |
| Instalar en local/prod | `INSTALL.md` |

## 📖 Documentación de Usuario (Raíz)

Los documentos **para usuarios finales** están en la raíz del repositorio:

- [`README.md`](../README.md) — Introducción y quick start
- [`CHANGELOG.md`](../CHANGELOG.md) — Historial de releases
- [`docker-compose.yml`](../docker-compose.yml) — Despliegue con Docker

---

**Nota:** Esta carpeta es para **desarrolladores**. Los usuarios finales deben empezar por [`README.md`](../README.md).
