# M3 Phase 2.1 — Docker Production Image — APPLY IN PROGRESS

**Fecha:** 2026-05-11
**Estado:** 🔄 APPLY IN PROGRESS
**Commit:** `feat(m3): add Docker production image (2.1)` (en progreso)

## Entregables Completados ✅

| # | Tarea | Archivo | Estado |
|---|-------|---------|--------|
| 2.1.1 | `Dockerfile.prod` multi-stage | `Dockerfile.prod` | ✅ CREADO |
| 2.1.2 | `docker-compose.prod.yml` | `docker-compose.prod.yml` | ✅ CREADO |
| 2.1.3 | `entrypoint.sh` (migrate + collectstatic) | `entrypoint.sh` | ✅ CREADO |
| 2.1.4 | Endpoint `/health/` | `erp_nexus/urls.py` | ✅ AGREGADO |
| 2.1.5 | `.dockerignore` | `.dockerignore` | ✅ CREADO |
| 2.1.6 | Documentación `DEPLOYMENT.md` | `docs/DEPLOYMENT.md` | ✅ CREADO |
| 2.1.7 | Tests integración Docker | `apps/core_marketplace/tests/test_docker_integration.py` | ✅ CREADO |
| 2.1.8 | Validación: `gunicorn` en dependencies | `pyproject.toml` | ✅ AGREGADO |

## Pendiente ⏳

- [ ] Test de integración real Docker (opcional — requiere Docker daemon en CI)
- [ ] Validación build `docker compose build` (manual o CI)

## Archivos Creados/Modificados

```
Dockerfile.prod                # Multi-stage: builder + runtime
docker-compose.prod.yml        #db + redis + web stack
entrypoint.sh                  # migrate → collectstatic → gunicorn
erp_nexus/urls.py              # + health_check view + /health/
.dockerignore                  # excluye tests, docs, .git, .venv, etc.
docs/DEPLOYMENT.md             # Guía completa de despliegue
.env.prod.example              # Plantilla variables de entorno
apps/core_marketplace/tests/test_docker_integration.py
pyproject.toml                 # [project] + gunicorn dependency
```

## Cómo Probar Localmente

```bash
# 1. Copiar variables de entorno
cp .env.prod.example .env.prod
# editar .env.prod con valores reales

# 2. Build de imagen
docker compose -f docker-compose.prod.yml build

# 3. Levantar stack
docker compose -f docker-compose.prod.yml up -d

# 4. Healthcheck
curl http://localhost/health/
# {"status": "healthy", "db": "ok"}

# 5. Ver logs
docker compose logs -f web
```

## Criterios de Éxito (Checklist)

- [x] Dockerfile multi-stage (builder + runtime)
- [x] Non-root user `erp` (UID 1000)
- [x] HEALTHCHECK configurado
- [x] Entrypoint ejecuta migrate + collectstatic
- [x] Volúmenes: media, static, logs, pgdata
- [x] `/health/` endpoint responde JSON
- [x] gunicorn en dependencias
- [x] Documentación completa
- [ ] (Opcional) Tests de integración Docker infraestructura

## Notas Técnicas

- **Base images:** `python:3.13-slim` (builder + runtime), `postgres:16-alpine`, `redis:7-alpine`
- **Build-time:** `uv venv` + `uv pip install --no-dev -e .`
- **Runtime:** solo venv + código fuente (sin build-essential)
- **Puertos:** 80→8000 (HTTP). SSL/TLS agregar en Phase 2.4 (Nginx + Certbot)
- **Logs:** Gunicorn escribe en `/app/logs/` (volumen `logs`)
- **Colección static:** Una sola vez en entrypoint (no en cada arranque)
