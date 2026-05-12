# 🗄️ PostgreSQL + Redis Production Tuning — ERP Nexus

**Guía de optimización de base de datos y cache para producción**
**Versión:** 1.0.0
**Fecha:** 2026-05-11

---

## 📊 PostgreSQL Tuning

### Parámetros Aplicados (docker-compose.prod.yml)

| Parameter | Valor | Justificación |
|-----------|-------|---------------|
| `shared_buffers` | 256MB | ~25% de RAM en sistema dedicado (asumiendo 1GB+) |
| `effective_cache_size` | 1GB | Estimación de cache OS +PG (paraplanificador) |
| `maintenance_work_mem` | 64MB | Memoria para VACUUM, CREATE INDEX |
| `checkpoint_completion_target` | 0.9 | Spread checkpoint I/O (reduce spikes) |
| `wal_buffers` | 16MB | Auto-tuned en PG 13+, pero explícito para seguridad |
| `default_statistics_target` | 100 | Mejor plan accuracy (default 100) |
| `random_page_cost` | 1.1 | SSD storage (vs 4.0 para HDD) |
| `effective_io_concurrency` | 200 | SSD parallelism |
| `work_mem` | 4MB | Memoria por operación sort/hash (por conexión) |
| `max_connections` | 100 | Límite prudente para Django app |
| `max_wal_size` | 1GB | Checkpoint frequency tuning |
| `min_wal_size` | 80MB | Min WAL retention |
| `log_min_duration_statement` | 1000ms | Log queries > 1 segundo (slow query log) |

### Extensiones Instaladas

```sql
-- Ejecutadas por scripts/init-db.sql al crear la DB
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;  -- Estadísticas de queries
CREATE EXTENSION IF NOT EXISTS pg_stat_kcache;      -- CPU/I/O stats
CREATE EXTENSION IF NOT EXISTS pg_qualstats;        -- Calidad de filtros
CREATE EXTENSION IF NOT EXISTS pg_wait_sampling;    -- Wait events sampling
```

**Uso:**
```sql
-- Top 10 queries más lentas
SELECT query, calls, total_time, rows, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Cache hit ratio (buffers)
SELECT round(100.0 * sum(blks_hit) / nullif(sum(blks_hit + blks_read), 0), 2) as cache_hit_ratio
FROM pg_stat_database
WHERE datname = 'erp_nexus';
```

---

## 🔄 Redis Tuning

### Configuración Aplicada (docker-compose.prod.yml)

| Parameter | Valor | Justificación |
|-----------|-------|---------------|
| `maxmemory` | 256mb | Límite para evitar OOM |
| `maxmemory-policy` | `allkeys-lru` | Evict keys menos recientes (LRU) |
| `appendonly` | `yes` | Durability — WAL-style AOF |
| `appendfsync` | `everysec` | Balance: performance + seguridad (cada segundo) |
| `save` | `60 1000` | Backup RDB cada 60s si ≥1000 cambios |
| `requirepass` | `${REDIS_PASSWORD}` | Auth obligatoria |
| `rename-command FLUSHDB/FLUSHALL` | `""` | Deshabilitar comandos peligrosos |

### Persistencia Redis

- **AOF (Append-Only File):** Cada escritura se loguea. `appendfsync everysec` implica posible pérdida de 1s en crash.
- **RDB snapshots:** Cada 60 segundos si hay ≥1000 cambios (backup para restart rápido).
- **Hybrid:** AOF + RDB (mejor de ambos: durability + fast restart).

### Monitoreo Redis

```bash
# Info general
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" info

# Memoria
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" info memory

# Keyspace por DB
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" info keyspace

# Slowlog (últimas 10 operaciones lentas)
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" slowlog get 10
```

---

## 📦 Scripts de Mantenimiento

### Backup Diario (`scripts/backup-db.sh`)

```bash
./scripts/backup-db.sh
```

- **Ubicación backups:** `/backup/daily/` y `/backup/weekly/`
- **Formato:** `erp_nexus_YYYYMMDD_HHMMSS.sql.gz`
- **Rotación:** 
  - Diarios: 7 días retención
  - Semanales (domingo): 4 semanas retención

**Cron (ejemplo):**
```cron
0 2 * * * cd /opt/erp-nexus && ./scripts/backup-db.sh >> /var/log/erp-backup.log 2>&1
```

### Restore (`scripts/restore-db.sh`)

```bash
# Restaurar backup específico
./scripts/restore-db.sh daily/erp_nexus_20260511_120000.sql.gz

# Restaurar el más reciente
./scripts/restore-db.sh latest
```

> El restore detiene el contenedor `web` temporalmente, recrea la DB, y restaura desde dump.

### Mantenimiento (`scripts/maintenance-db.sh`, `maintenance-redis.sh`)

```bash
./scripts/maintenance-db.sh    # VACUUM ANALYZE + estadísticas
./scripts/maintenance-redis.sh # Info, memoria, slowlog
```

---

## 🚨 Alertas Sugeridas (Phase 2.5)

| Métrica | Umbral | Acción |
|---------|--------|--------|
| Disk usage (pgdata) | >85% | Limpiar backups antiguos, expandir volumen |
| DB connections | >80 de max_connections | Investigar leaks, escalar |
| Cache hit ratio (PG) | <95% | Aumentar shared_buffers o memoria |
| Redis memory used | >80% de maxmemory | Revisar TTL keys, escalar |
| Slow queries (>1s) | >10/hora | Optimizar índices, revisar queries |
| Backup fallido | Último backup >24h | Alertar inmediatamente |

---

## 🔧 Troubleshooting

### PostgreSQL

| Problema | Diagnóstico | Solución |
|----------|-------------|----------|
| Queries lentas | `pg_stat_statements` top 10 | Agregar índices, reescribir query |
| Conexiones agotadas | `SELECT count(*) FROM pg_stat_activity;` | Aumentar `max_connections` o pooling (pgBouncer) |
| Alto I/O | `SELECT * FROM pg_stat_database;` | Ajustar `effective_io_concurrency`, considerar más RAM |
| Disk llenándose | `du -sh /var/lib/postgresql/data` | Limpiar backups, logs, VACUUM FULL (programado) |

### Redis

| Problema | Diagnóstico | Solución |
|----------|-------------|----------|
| Evictions频繁 | `info stats` → `evicted_keys` | Aumentar `maxmemory` o ajustar TTL |
| Latencia alta | `slowlog get` | Optimizar keys, usar pipelining |
| Persistencia fallida | `info persistence` | Verificar disco, `appendfsync always/always` (riesgo) |

---

## 📈 Monitoreo Futuro (Phase 2.5)

- **Grafana dashboards** para PostgreSQL (pg_stat_statements, cache hit, connections)
- **Sentry** para errores de aplicación
- **Prometheus exporters**:
  - `postgres_exporter` → métricas PG
  - `redis_exporter` → métricas Redis
- **AlertManager** → Slack/Telegram notifications

---

## 🔐 Seguridad

- **PostgreSQL:** contraseña en `.env.prod`, no en Dockerfile
- **Redis:** `requirepass`, comandos `FLUSHDB/FLUSHALL` deshabilitados
- **Backups:** cifrar con `gpg` si van a storage externo
- **Red:** Docker bridge network aislada (erp_nexus_net)

---

## 📚 Referencias

- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/runtime-config.html)
- [Redis Persistence](https://redis.io/docs/management/persistence/)
- [Docker Compose Volumes](https://docs.docker.com/compose/compose-file/compose-file-v3/#volumes)
