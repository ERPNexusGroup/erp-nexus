# M3 Phase 2.2 — PostgreSQL + Redis Production

**Fecha:** 2026-05-11
**Estado:** PLAN PENDING → APPLY NEXT
**Estimado:** 6h

## Objetivo
Configuración de producción para PostgreSQL y Redis:
- Backups automáticos (diario) con rotación
- Tuning de PostgreSQL (connection pooling, WAL, autovacuum)
- Redis persistencia (AOF) y configuración segura
- Scripts de mantenimiento (vacuum, analyze, pg_stat_statements)
- Monitoreo básico (health, slow queries, cache hit ratio)

## Entregables

### 1. PostgreSQL Production Tuning (`docker-compose.prod.yml` extension)
```yaml
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      # Ajustes producción
      POSTGRES_INITDB_ARGS: "--auth-host=md5 --auth-local=trust"
      PGDATA: /var/lib/postgresql/data/pgdata
    command: >
      postgres
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c maintenance_work_mem=64MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=16MB
      -c default_statistics_target=100
      -c random_page_cost=1.1
      -c effective_io_concurrency=200
      -c work_mem=4MB
      -c max_connections=100
      -c max_wal_size=1GB
      -c min_wal_size=80MB
```

### 2. Backup Automático (script `scripts/backup-db.sh`)
```bash
#!/bin/bash
# Backup PostgreSQL → /backup/erp_nexus_YYYY-MM-DD.sql.gz
# Retención: 7 días diarios + 4 semanas semanales

BACKUP_DIR="/backup"
DATE=$(date +%Y-%m-%d)
DAILY="$BACKUP_DIR/daily/daily_$DATE.sql.gz"
WEEKLY="$BACKUP_DIR/weekly/weekly_$(date +%Y-%U).sql.gz"

docker compose exec -T db pg_dump -U erp erp_nexus | gzip > "$DAILY"

# Rotación diaria (7 días)
find "$BACKUP_DIR/daily" -name "daily_*.sql.gz" -mtime +7 -delete

# Copia semanal (cada domingo)
if [ "$(date +%u)" = "7" ]; then
    cp "$DAILY" "$WEEKLY"
    find "$BACKUP_DIR/weekly" -name "weekly_*.sql.gz" -mtime +28 -delete
fi
```

### 3. Restore Script (`scripts/restore-db.sh`)
```bash
#!/bin/bash
# Restore desde backup
# Uso: ./scripts/restore-db.sh backup_20260511.sql.gz

BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "Uso: $0 <backup-file>"
    exit 1
fi

# Parar contenedores (opcional — para consistencia)
docker compose down

# Restaurar
gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U erp erp_nexus

echo "✅ Restore completado"
```

### 4. Redis Production Config (`docker-compose.prod.yml` Redis service)
```yaml
  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --appendonly yes
      --appendfsync everysec
      --save 60 1000
      --rename-command FLUSHDB ""
      --rename-command FLUSHALL ""
```

### 5. Health Checks Extendidos
- PostgreSQL: `pg_isready -U erp` (ya en compose)
- Redis: `redis-cli --raw incr ping`
- Slow queries log en PostgreSQL (log_min_duration_statement = 1000ms)

### 6. pg_stats_sustained (stats collector)
```sql
-- En Dockerfile o init script
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_stat_kcache;
```

### 7. Documentación (`docs/PROD_DB_TUNING.md`)
- Parámetros explicados
- Cómo restaurar backup
- Monitoreo con `pg_top`, `redis-cli info`
- Alertas sugeridas (disk space, connection count, cache hit ratio)

## Tareas

| # | Tarea | Estimado | Estado |
|---|-------|----------|--------|
| 2.2.1 | Ajustar `docker-compose.prod.yml` (PostgreSQL tuning) | 1h | ⏳ |
| 2.2.2 | Crear `scripts/backup-db.sh` (backup diario + rotación) | 1h | ⏳ |
| 2.2.3 | Crear `scripts/restore-db.sh` | 0.5h | ⏳ |
| 2.2.4 | Ajustar Redis config (AOF, maxmemory, rename-command) | 0.5h | ⏳ |
| 2.2.5 | Agregar `pg_stat_statements` extension | 0.5h | ⏳ |
| 2.2.6 | Documentar en `docs/PROD_DB_TUNING.md` | 1h | ⏳ |
| 2.2.7 | Tests de backup/restore (mock) | 1h | ⏳ |
| 2.2.8 | Validación: docker compose up + backup exitoso | 0.5h | ⏳ |

**Total:** ~6h

## Criterios de Éxito
- [ ] Backup diario automático (7 días retención)
- [ ] Restore desde backup verificado
- [ ] PostgreSQL tuning aplicado (connection pooling, WAL)
- [ ] Redis persistencia AOF + maxmemory policy
- [ ] pg_stat_statements disponible
- [ ] Documentación completa

## Dependencias
- Phase 2.1 (Docker stack) ✅
- Acceso a volumen `pgdata` para backups

## Riesgos
- Backup en contenedor puede excluirse de volumen → usar volumen externo o host mount
- Tuning muy agresivo puede causar OOM → monitorear en staging primero
