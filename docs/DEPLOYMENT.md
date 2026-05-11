# 📦 DEPLOYMENT — ERP Nexus Producción

**Guía de despliegue con Docker (multi-stage)**
**Versión:** 1.0.0
**Fecha:** 2026-05-11

---

## 📋 Prerrequisitos

- Docker Engine ≥ 24.0 (con soporte BuildKit)
- Docker Compose v2
- 4 GB RAM mínimo (recomendado 8 GB)
- Puerto 80 (HTTP) o 443 (HTTPS) disponible
- Acceso a internet para pull de imágenes base

---

## 🔧 Variables de Entorno

Crea `.env.prod` en la raíz del proyecto:

```bash
# ─── PostgreSQL ─────────────────────────────────────────────────────────────
POSTGRES_DB=erp_nexus
POSTGRES_USER=erp
POSTGRES_PASSWORD=<contraseña-segura-aqui>

# ─── Redis ──────────────────────────────────────────────────────────────────
REDIS_PASSWORD=<redis-password-opcional>

# ─── Django ─────────────────────────────────────────────────────────────────
SECRET_KEY=<django-secret-key-generado>
DEBUG=0
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# ─── Email (opcional) ───────────────────────────────────────────────────────
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=<contraseña-app>

# ─── SRI Ecuador (facturación electrónica — opcional) ───────────────────────
FACTURACION_CERT_PATH=/app/media/certs/cert.p12
FACTURACION_CERT_PASSWORD=<cert-password>
SRI_AMBIENTE=1  # 1=pruebas, 2=producción

# ─── GitHub Integration (Marketplace auto-discovery) ───────────────────────
GITHUB_TOKEN=<token-con-repo-read>
GITHUB_ORG=ERPNexusGroup
```

> **Importante:** Nunca comitre `.env.prod`. Agregar a `.gitignore`.

---

## 🏗️ Build de la Imagen

```bash
# Construir imagen (desde raíz del proyecto)
docker build -f Dockerfile.prod -t erp-nexus:latest .

# O usando docker compose (compila automáticamente)
docker compose -f docker-compose.prod.yml build
```

**Tamaño esperado:** ~400–500 MB (multi-stage elimina build tools).

---

## 🚀 Primer Arranque

```bash
# Levantar todos los servicios (db + redis + web)
docker compose -f docker-compose.prod.yml up -d

# Ver estado
docker compose -f docker-compose.prod.yml ps

# Ver logs (seguimiento en vivo)
docker compose -f docker-compose.prod.yml logs -f web

# Healthcheck
curl http://localhost/health/
# {"status": "healthy", "db": "ok"}
```

Los volúmenes persistentes se crean automáticamente:
- `pgdata/` — datos PostgreSQL
- `media/` — uploads de usuarios
- `static/` — archivos estáticos colectados
- `logs/` — logs de Gunicorn (acces.log, error.log)

---

## 🔍 Logs y Monitoreo

```bash
# Logs de la aplicación web
docker compose logs -f web

# Logs de base de datos
docker compose logs -f db

# Métricas (sin PAN)
docker stats erp_nexus_web erp_nexus_db erp_nexus_redis
```

**Rotación de logs:** Los logs de Gunicorn se escriben en `/app/logs/` (volumen `logs`). Configurar logrotate externo o `docker logs` con `--log-opt max-size`.

---

## 💾 Backup y Restore

### Backup de base de datos
```bash
docker compose exec db pg_dump -U erp erp_nexus > backup_$(date +%Y%m%d).sql
```

### Restore
```bash
docker compose exec -T db psql -U erp erp_nexus < backup_20260511.sql
```

### Backup de archivos media
```bash
docker compose cp erp_nexus_web:/app/media/ ./media-backup/
# o rsync desde volumen
rsync -av volume_pgdata/ backup/
```

---

## 🔄 Actualización (Rolling Update)

```bash
# 1. Pull de nueva imagen (si usas registry externo)
docker pull erp-nexus:latest

# 2. Rebuild local (si hay cambios en código)
docker compose -f docker-compose.prod.yml build

# 3. Restart con cero downtime (Gunicorn graceful reload)
docker compose -f docker-compose.prod.yml up -d --no-deps --build web

# 4. Ejecutar migraciones en el contenedor nuevo
docker compose exec web python manage.py migrate --noinput
```

**Nota:** El `entrypoint.sh` ya ejecuta migraciones automáticamente al iniciar. Si necesitas forzar:
```bash
docker compose exec web python manage.py migrate --noinput
```

---

## 🛡️ SSL/TLS (HTTPS)

Para producción con SSL, agrega Nginx como reverse proxy con Certbot:

```yaml
# docker-compose.prod.yml adicional
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro  # certificados Let's Encrypt
    depends_on:
      - web
    networks:
      - erp_nexus_net
```

O usa Traefik/Caddy como proxy automático.

---

## 📊 Métricas de Salud

Endpoint integrado:
```
GET /health/
Response 200: {"status": "healthy", "db": "ok"}
Response 503: {"status": "unhealthy", "db": "error", ...}
```

Docker HEALTHCHECK configurado en `Dockerfile.prod`:
- Interval: 30s
- Timeout: 5s
- Retries: 3
- Start period: 20s

---

## 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| Container se reinicia | `docker compose logs web` — revisar traceback Django |
| DB connection refused | Verificar `POSTGRES_PASSWORD` y que contenedor `db` esté healthy |
| Static files 404 | Ejecutar `docker compose exec web python manage.py collectstatic --noinput` |
| Permisos en media/ | `docker compose exec web chown -R erp:erp /app/media` |
| Healthcheck falla | Verificar que `DEBUG=0` y `ALLOWED_HOSTS` incluya dominio o IP |

---

## 🏷️ Tags y Versionado

```bash
# Tag por fecha
docker tag erp-nexus:latest erp-nexus:2026-05-11

# Push a registry (si tienes uno)
docker tag erp-nexus:latest registry.example.com/erp-nexus:latest
docker push registry.example.com/erp-nexus:latest
```

---

## 📝 Notas de Producción

- Usa `DEBUG=0` siempre en producción
- Configura `ALLOWED_HOSTS` con tus dominios
- Habilita sentry o logging externo (pendiente Phase 2.5)
- Backup automático diario de `pgdata/` y `media/`
- Considera CDN para `/static/` y `/media/` en Scale

---

**Siguientes fases:**
- M3 Phase 2.2 — PostgreSQL + Redis producción (backups, replica)
- M3 Phase 2.3 — Celery workers
- M3 Phase 2.4 — SSL + Nginx
- M3 Phase 2.5 — Monitoring (Prometheus + Grafana + Sentry)
