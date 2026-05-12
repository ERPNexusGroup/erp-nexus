# Alerting Rules & Runbooks — ERP Nexus

## Visión General

Este documento describe cada regla de alerta, su propósito, pasos de diagnóstico y acciones de remediación.

## Estructura de Runbooks

Cada runbook contiene:
- **Descripción:** Qué problema detecta la alerta
- **Severidad:** Impacto en el servicio
- **Diagnóstico:** Comandos para investigar la causa
- **Remediación:** Pasos para resolver
- **Post-mortem:** Acciones para prevenir recurrencia

---

## Critical Alerts (Slack + Email)

### HighResponseLatency

**Descripción:** La latencia P95 de respuesta de Django supera 1 segundo.

**Severidad:** critical

**Métrica:** `histogram_quantile(0.95, sum(rate(django_http_response_time_seconds_bucket[5m])) by (le)) > 1.0`

**Diagnóstico:**
```bash
# 1. Ver latencia actual en Prometheus
curl -s 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,sum(rate(django_http_response_time_seconds_bucket[5m]))by(le))' | jq .

# 2. Identificar endpoints lentos
curl -s 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,sum(rate(django_http_response_time_seconds_bucket[5m]))by(endpoint))' | jq .

# 3. Ver queries DB lentas (si django-prometheus está instrumentado)
curl -s 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.99,sum(rate(django_db_query_duration_seconds_bucket[5m]))by(view))' | jq .

# 4. Logs Django (en el contenedor)
docker-compose -f docker-compose.prod.yml logs -f web | grep -i "slow"

# 5. Estado cache Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli info stats
```

**Remediación:**
1. Si es un endpoint específico → revisar código, agregar índices DB, optimizar query
2. Si es general → verificar carga CPU/memoria del contenedor web
3. Verificar conexiones DB: `docker-compose exec db pg_stat_activity`
4. Reiniciar worker si Celery está bloqueando recursos: `docker-compose restart worker`
5. Escalar horizontalmente (aumentar workers Gunicorn): ajustar `WEB_WORKERS` en `.env.prod`

**Post-mortem:**
- Registrar endpoint lento en tickets de optimización
- Considerar query result caching (Redis)
- Agregar APM (como Sentry) para trazas distribuidas

---

### High5xxErrorRate

**Descripción:** Tasa de errores 5xx supera 5% en ventana de 2 minutos.

**Severidad:** critical

**Métrica:** `sum(rate(django_http_responses_total{status=~"5.."}[5m])) / sum(rate(django_http_responses_total[5m])) > 0.05`

**Diagnóstico:**
```bash
# 1. Ver códigos 5xx específicos
curl -s 'http://localhost:9090/api/v1/query?query=sum(rate(django_http_responses_total{status=~"5.."}[5m]))by(status_code)' | jq .

# 2. Endpoints que devuelven 5xx
curl -s 'http://localhost:9090/api/v1/query?query=sum(rate(django_http_responses_total{status=~"5.."}[5m]))by(endpoint,status_code)' | jq .

# 3. Logs de errores Django
docker-compose -f docker-compose.prod.yml logs -f web --tail=100 | grep -i "error\|exception\|traceback"

# 4. Verificar exception rate en Sentry (si integrado)
# Ir a Sentry UI → Issues → filtrar por environment=production

# 5. Estado base de datos
docker-compose -f docker-compose.prod.yml exec db pg_isready
```

**Remediación:**
1. Si 502/504 → Nginx no alcanza Gunicorn: reiniciar `web`: `docker-compose restart web`
2. Si 500 → excepción en código: revisar logs, revertir deploy reciente si es rollback
3. Si DB connection errors → verificar max_connections en PostgreSQL, aumentar si es necesario
4. Si Redis caído → `docker-compose restart redis` (alertará `RedisDown` paralelamente)
5. Si persiste → escala horizontal de workers

**Post-mortem:**
- Analizar stack trace en logs → crear ticket bug
- Agregar validación de errores en CI/CD para ese endpoint
- Considerar circuit breaker para dependencias externas

---

### DatabaseDown

**Descripción:** PostgreSQL no responde (up == 0).

**Severidad:** critical

**Métrica:** `up{job="postgres"} == 0` for 1m

**Diagnóstico:**
```bash
# 1. Estado contenedor DB
docker-compose -f docker-compose.prod.yml ps db
docker-compose -f docker-compose.prod.yml logs db --tail=50

# 2. Intento conexión manual
docker-compose -f docker-compose.prod.yml exec db pg_isready -U ${POSTGRES_USER:-erp} -d ${POSTGRES_DB:-erp_nexus}

# 3. Recursos del host (CPU/RAM/disk)
docker stats erp_nexus_db --no-stream

# 4. Ver logs PostgreSQL (crashes, OOM)
docker-compose -f docker-compose.prod.yml exec db cat /var/lib/postgresql/data/logfile 2>/dev/null || echo "Log no accesible"

# 5. Disco lleno?
docker-compose -f docker-compose.prod.yml exec db df -h /var/lib/postgresql/data
```

**Remediación:**
1. Si contenedor caído: `docker-compose start db`
2. Si OOM Killer: aumentar memoria host o ajustar `shared_buffers` y `work_mem` más bajos
3. Si disco lleno: limpiar logs PostgreSQL, rotar WALs, extender volumen
4. Si conexiones agotadas (`max_connections`): aumentar en `docker-compose.prod.yml` command o matar queries idle
5. Si corrupción DB: restaurar desde backup más reciente

**Post-mortem:**
- Revisar `docker logs db` para pila de errores
- Ajustar `max_connections` y connection pooling (pgbouncer)
- Agregar alerta de disco < 10% antes de llenarse

---

### RedisDown

**Descripción:** Redis no responde (up == 0).

**Severidad:** critical

**Métrica:** `up{job="redis"} == 0` for 1m

**Diagnóstico:**
```bash
# 1. Estado contenedor Redis
docker-compose -f docker-compose.prod.yml ps redis
docker-compose -f docker-compose.prod.yml logs redis --tail=50

# 2. Intento conexión
docker-compose -f docker-compose.prod.yml exec redis redis-cli -a ${REDIS_PASSWORD} ping

# 3. Memoria Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli -a ${REDIS_PASSWORD} info memory

# 4. Persistencia AOF
docker-compose -f docker-compose.prod.yml exec redis redis-cli -a ${REDIS_PASSWORD} info persistence

# 5. Verificar volumen redisdata
docker-compose -f docker-compose.prod.yml exec redis df -h /data
```

**Remediación:**
1. Si contenedor caído: `docker-compose restart redis`
2. Si OOM: ajustar `maxmemory 256mb` o aumentar host RAM
3. Si AOF corrompido: `redis-check-aof /data/appendonly.aof` (debug), restaurar desde backup AOF
4. Si persistence fallando: verificar permisos volumen `redisdata`
5. Si persistencia es prioritaria → cambiar a `appendfsync always` (performance penalty)

**Post-mortem:**
- Considerar Redis Cluster si alta disponibilidad requerida
- Backup AOF frecuente (cada hora)
- Monitorear memoria Redis > 80% comowarning

---

### ContainerDown

**Descripción:** Uno de los servicios críticos (django, celery, nginx, cadvisor) está caído.

**Severidad:** critical

**Métrica:** `up{job=~"django|celery|cadvisor|nginx"} == 0` for 2m

**Diagnóstico:**
```bash
# 1. Identificar contenedor caído
curl -s 'http://localhost:9090/api/v1/query?query=up{job=~"django|celery|cadvisor|nginx"}' | jq .

# 2. Estado servicios docker-compose
docker-compose -f docker-compose.prod.yml ps

# 3. Logs del servicio caído (reemplazar <service>)
docker-compose -f docker-compose.prod.yml logs <service> --tail=100

# 4. Healthcheck fallando?
docker-compose -f docker-compose.prod.yml ps | grep -i "unhealthy"
```

**Remediación por servicio:**

**django (web) caído:**
- Verificar logs: `docker-compose logs web`
- Si OOM → aumentar memoria o reducir `WEB_WORKERS`
- Si DB/Redis no conectan → verificar dependencias
- Reiniciar: `docker-compose restart web`

**celery (worker) caído:**
- Verificar logs: `docker-compose logs worker`
- Si task fallando → restart worker para limpiar estado
- Reiniciar: `docker-compose restart worker`

**nginx caído:**
- Verificar logs: `docker-compose logs nginx`
- Si puerto 80/443 en uso → conflicto con otro proceso
- Reiniciar: `docker-compose restart nginx`

**cadvisor caído:**
- Verificar mounts: `/` y `/var/run` deben estar accesibles
- Reiniciar: `docker-compose restart cadvisor`

**Post-mortem:**
- Agregar alerta específica por servicio para identificar rápido
- Revisar `restart: unless-stopped` en compose (debe reiniciar automáticamente)
- Considerar `restart: always` si es inestable

---

### SSLCertificateExpiring

**Descripción:** Certificado SSL expira en menos de 7 días.

**Severidad:** critical

**Métrica:** `probe_ssl_earliest_cert_expiry - time() < 604800` (7d en segundos)

**Diagnóstico:**
```bash
# 1. Ver fecha expiración actual
curl -s 'http://localhost:9090/api/v1/query?query=probe_ssl_earliest_cert_expiry' | jq .

# 2. Verificar Certbot logs (renovaciones)
docker-compose -f docker-compose.prod.yml logs certbot --tail=50

# 3. Ver archivos certificado en contenedor nginx
docker-compose -f docker-compose.prod.yml exec nginx ls -la /etc/letsencrypt/live/${DOMAIN}/

# 4. Verificar fecha expiración manual
echo | openssl s_client -connect ${DOMAIN}:443 2>/dev/null | openssl x509 -noout -dates
```

**Remediación:**
1. Forzar renovación manual: `docker-compose run --rm certbot certbot renew --force-renewal`
2. Verificar que el challenge HTTP-01 funciona (puerto 80 accesible desde internet)
3. Si falla challenge → verificar firewall, DNS A record apuntando a IP correcta
4. Después de renovar: `docker-compose restart nginx` para recargar certificado
5. SiCertbot falla repetidamente → renovar manualmente vía `certbot certonly` y copiar archivos

**Post-mortem:**
- Agregar alerta a 30 días antes (warning) para dar tiempo
- Automatizar renovación verification en CI/CD
- Configurar auto-renew cada 12h (ya está en compose) pero verificar logs

---

## Warning Alerts (Email)

### HostHighCPU

**Descripción:** Uso de CPU del host supera 90% por 5 minutos.

**Severidad:** warning

**Métrica:** `100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90`

**Diagnóstico:**
```bash
# 1. Ver CPU actual
curl -s 'http://localhost:9100/metrics' | grep node_cpu_seconds_total

# 2. Top procesos consumiendo CPU en host (fuera de Docker)
top -b -n 1 | head -20

# 3. CPU por contenedor
docker stats --no-stream | sort -k3 -hr | head -10

# 4. Load average
uptime

# 5. Número de procesos
ps -e | wc -l
```

**Remediación:**
1. Identificar proceso/container con alta CPU (`docker stats`)
2. Si es web/worker → escalar horizontalmente (más workers o réplicas)
3. Si es proceso host → matar/optimizar proceso problemático
4. Si carga persistente → considerar upgrade de instancia (más CPU)
5. Revisar si hay infinite loops en código reciente

**Post-mortem:**
- Agregar límite de CPU en docker-compose (`cpus:`)
- Implementar autoscaling basado en CPU (K8s o scripts)
- Profiling de código para hotspots

---

### HostLowMemory

**Descripción:** Memoria disponible del host < 10% por 5 minutos.

**Severidad:** warning

**Métrica:** `(node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 < 10`

**Diagnóstico:**
```bash
# 1. Memoria actual
curl -s 'http://localhost:9100/metrics' | grep node_memory_MemAvailable_bytes

# 2. libre/hosts
free -h

# 3. Memoria por contenedor
docker stats --no-stream | sort -k4 -hr | head -10

# 4. OOM Killer events
dmesg | grep -i "out of memory" | tail -20

# 5. Cache buffers (si aparece "available" bajo)
cat /proc/meminfo | grep -E "MemFree|Buffers|Cached|Active|Inactive"
```

**Remediación:**
1. Identificar contenedores con alta memoria (`docker stats`)
2. Reiniciar contenedores con memory leak: `docker-compose restart <service>`
3. Ajustar límites memoria en `docker-compose.prod.yml` (ej: `mem_limit: 1g`)
4. Si host sin swap → agregar swap temporal: `sudo fallocate -l 2G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`
5. Considerar agregar RAM al servidor

**Post-mortem:**
- Profiler de memoria para leaks (Python objgraph, tracemalloc)
- Límites estrictos en compose (mem_reservation)
- Alertar a 20% libre para headroom

---

### DiskSpaceLow

**Descripción:** Espacio en disco del host < 15% libre por 10 minutos.

**Severidad:** warning

**Métrica:** `(node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 15`

**Diagnóstico:**
```bash
# 1. Espacio actual
curl -s 'http://localhost:9100/metrics' | grep node_filesystem_avail_bytes

# 2. df -h para identificar partición llena
df -h /

# 3. Directorios que más ocupan
sudo du -sh /var/lib/docker/* 2>/dev/null | sort -hr | head -10
sudo du -sh /app/* 2>/dev/null | sort -hr | head -10

# 4. Logs rotados
sudo find /var/log -type f -size +100M -exec ls -lh {} \;

# 5. Volúmenes Docker huérfanos
docker volume ls -qf dangling=true
```

**Remediación:**
1. Limpiar logs antiguos: `sudo find /var/log -type f -mtime +30 -delete`
2. Limpiar imágenes Docker no usadas: `docker system prune -a --volumes` (cuidado)
3. Rotar logs de la aplicación (logrotate configurar)
4. Expandir volumen si es cloud (EBS, etc.)
5. Eliminar backups antiguos (verificar política retención)

**Post-mortem:**
- Configurar log rotation automático (logrotate o docker logging driver)
- Monitoreo de crecimiento de volúmenes semanal
- Política de retención backups (ej: 30 días)

---

### SlowDatabaseQueries

**Descripción:** P99 de duración de consultas DB > 2 segundos por 10 minutos.

**Severidad:** warning

**Métrica:** `histogram_quantile(0.99, sum(rate(django_db_query_duration_seconds_bucket[5m])) by (le)) > 2.0`

**Diagnóstico:**
```bash
# 1. Ver consultas lentas actuales
curl -s 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.99,sum(rate(django_db_query_duration_seconds_bucket[5m]))by(view))' | jq .

# 2. Log queries lentas PostgreSQL (log_min_duration_statement=1000 ya está)
docker-compose -f docker-compose.prod.yml exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# 3. Locks activos
docker-compose -f docker-compose.prod.yml exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT pid, query, state, wait_event_type, wait_event FROM pg_stat_activity WHERE state <> 'idle';"

# 4. Índices faltantes (revisar queries frecuentes)
docker-compose -f docker-compose.prod.yml exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0 AND schemaname = 'public';"

# 5. Connection pooling
docker-compose -f docker-compose.prod.yml exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT count(*) FROM pg_stat_activity;"
```

**Remediación:**
1. Agregar índices en columnas frecuentemente filtradas (`WHERE`, `JOIN`, `ORDER BY`)
2. Optimizar queries N+1: usar `select_related`, `prefetch_related` en Django ORM
3. Considerar materialized views para reports pesados
4. Agregar caching (Redis) para resultados estáticos
5. Si connection pool lleno → aumentar `max_connections` o implementar PgBouncer

**Post-mortem:**
- Configurar `pg_stat_statements` extensión (ya debería estar)
- Review regular de slow query log (una vez por semana)
- Considerar read replicas para queries de reportes

---

### CeleryQueueLengthHigh

**Descripción:** Cola de Celery con más de 100 tareas pendientes por 15 minutos.

**Severidad:** warning

**Métrica:** `celery_queue_length > 100`

**Diagnóstico:**
```bash
# 1. Ver longitud de colas
curl -s 'http://localhost:9090/api/v1/query?query=celery_queue_length' | jq .

# 2. Inspeccionar tareas pendientes (en worker)
docker-compose -f docker-compose.prod.yml exec worker celery -A erp_nexus inspect reserved --destination=erp_nexus_worker@%h

# 3. Tareas activas
docker-compose -f docker-compose.prod.yml exec worker celery -A erp_nexus inspect active --destination=erp_nexus_worker@%h

# 4. Revoked tasks (pueden estar bloqueando)
docker-compose -f docker-compose.prod.yml exec worker celery -A erp_nexus inspect revoked --destination=erp_nexus_worker@%h

# 5. Ver logs worker por errores
docker-compose -f docker-compose.prod.yml logs worker --tail=100 | grep -i "error\|exception\|retry"
```

**Remediación:**
1. Revisar si hay tareas stuck (reserved pero no running) → reiniciar worker: `docker-compose restart worker`
2. Si backlog creciendo → aumentar concurrency worker: `CELERY_WORKER_CONCURRENCY=8` en `.env.prod`
3. Identificar tareas lentas (> 30s) → optimizar o dividir en subtareas
4. Verificar si hay rate limits en APIs externas (SRI, payment gateway)
5. Si frecuente → agregar más workers (escalar horizontalmente)

**Post-mortem:**
- Profiler de tareas Celery (flower o django-celery-results)
- Establecer timeouts por defecto en tareas (`task_time_limit`)
- Monitorear cola por tipo (sri, notifications, reports) separadamente

---

## Inhibitions

Las siguientes inhibiciones evitan notificaciones duplicadas:

| Fuente | Objetivo | Condición |
|--------|----------|-----------|
| `severity=critical` | `severity=warning` | Mismo `service` e `instance` |
| `alertname=DatabaseDown` | `alertname=SlowDatabaseQueries` | Mismo `service` |

---

## Runbook de Respuesta a Incidentes

### Paso 1: Triage (0-5 min)

1. Recibir alerta en Slack/Email
2. Identificar severity (critical → responder inmediato; warning → dentro de 1h)
3. Abrir incidente en canal `#incident-erp-nexus`
4. Ejecutar `./scripts/incident-open.sh <alertname>` (si existe)

### Paso 2: Diagnóstico (5-15 min)

1. Revisar métricas en Grafana: http://localhost:3000/d/erp-nexus-prod
2. Ejecutar comandos de diagnóstico de este runbook
3. Identificar root cause (DB, Redis, CPU, memory, code bug)
4. Comunicar estado en canal cada 5 min

### Paso 3: Remediación (15-30 min)

1. Aplicar remediación inmediata (restart, scale, rollback)
2. Si no se resuelve → escalar a segundo nivel
3. Documentar acciones tomadas en timeline del incidente

### Paso 4: Post-mortem (dentro de 24h)

1. Escribir post-mortem en `docs/INCIDENTS/<fecha>-<alertname>.md`
2. Incluir: timeline, causa raíz, impacto, remediación, acciones preventivas
3. Crear ticket de seguimiento para cada acción preventiva
4. Actualizar runbooks si se descubren nuevos pasos

---

## Escalation Matrix

| Severidad | Nivel 1 (On-call) | Nivel 2 (DevOps) | Nivel 3 (Engineering Manager) |
|-----------|-------------------|------------------|-------------------------------|
| critical | Responder en 5 min | Notificar (Slack mention) | Notificar si > 30min sin resolver |
| warning | Responder en 1h | No requiere (a menos que crítico) | No requiere |

**On-call rotation:** Configurar PagerDuty/Opsgenie en AlertManager routes (fuera de scope actual).

---

## Contactos

| Rol | Email | Slack |
|-----|-------|-------|
| Admin Principal | admin@erp-nexus.com | @admin |
| DevOps | devops@erp-nexus.com | @devops |
| DB Admin | dba@erp-nexus.com | @dba |
| Alert Channel | — | #alerts-erp-nexus |
| Incident Channel | — | #incident-erp-nexus |

---

**Última actualización:** 2026-05-12 (M3 Phase 2.5)
