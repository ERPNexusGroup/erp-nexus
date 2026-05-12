# Monitoring Stack — ERP Nexus Production

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                     ERP Nexus Production                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────────────┐ │
│  │  Web    │  │ Worker  │  │ Beat    │  │   Nginx SSL      │ │
│  │ :8000   │  │ :8000   │  │         │  │   :80/:443       │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────────┬─────────┘ │
│       │            │            │                 │            │
│       ▼            ▼            ▼                 ▼            │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Prometheus (:9090)                     │ │
│  │  Scrape: django, celery, cadvisor, node, alertmanager    │ │
│  │  Retention: 30d | Rules: monitoring/prometheus/alerts/   │ │
│  └───────────────────────────┬───────────────────────────────┘ │
│                              │                                 │
│                              ▼                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                     Grafana (:3000)                       │ │
│  │  Dashboard: ERP Nexus — Production Monitoring            │ │
│  │  Provisioning: monitoring/grafana/provisioning/           │ │
│  └───────────────────────────┬───────────────────────────────┘ │
│                              │                                 │
│                              ▼                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                  AlertManager (:9093)                     │ │
│  │  Routing: Slack (critical) + Email (warning)             │ │
│  │  Inhibit: critical→warning same service                  │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │cAdvisor │   │Node     │   │Postgres │   │Redis    │
   │:8080    │   │Exporter │   │         │   │         │
   │         │   │:9100    │   │         │   │         │
   └─────────┘   └─────────┘   └─────────┘   └─────────┘
```

## Componentes

### Prometheus

- **Imagen:** `prom/prometheus:v2.52.0`
- **Puerto:** 9090 (UI + API)
- **Config:** `monitoring/prometheus/prometheus.yml`
- **Almacenamiento:** `promdata` volumen Docker (retención 30d)
- **Scrape jobs:**
  - `django` → `web:8000/metrics/`
  - `celery` → `worker:8000/metrics/`
  - `cadvisor` → `cadvisor:8080/metrics`
  - `node` → `node-exporter:9100/metrics`
  - `alertmanager` → `alertmanager:9093/metrics`

### Grafana

- **Imagen:** `grafana/grafana:10.4.2-oss`
- **Puerto:** 3000
- **Admin:** `$GRAFANA_ADMIN_USER` / `$GRAFANA_ADMIN_PASSWORD`
- **Provisioning:**
  - Datasources: `monitoring/grafana/provisioning/datasources/prometheus.yml`
  - Dashboards: `monitoring/grafana/provisioning/dashboards/erp_nexus.yml`
  - Config: `monitoring/grafana/provisioning/config/grafana.ini`
- **Dashboards:** `monitoring/grafana/dashboards/erp_nexus.json`
- **Almacenamiento:** `grafanadata` volumen Docker
- **SMTP:** configurado via env vars para alertas email

### cAdvisor

- **Imagen:** `gcr.io/cadvisor/cadvisor:v0.49.1`
- **Puerto:** 8080
- **Métricas:** CPU, memoria, red, filesystem por contenedor
- **Volumen:** mounts `/` y `/var/run` readonly

### Node Exporter

- **Imagen:** `prom/node-exporter:v1.7.0`
- **Puerto:** 9100
- **Métricas:** CPU, RAM, disco, I/O, red del host
- **Collectors:** filesystem, cpu, mem, diskstats, netdev, etc.

### AlertManager

- **Imagen:** `prom/alertmanager:v0.27.0`
- **Puerto:** 9093
- **Config:** `monitoring/alertmanager/alertmanager.yml`
- **Canales:**
  - Slack: `#alerts-erp-nexus` (críticas)
  - Email: `ADMIN_ALERT_EMAIL` (warnings), `DB_ADMIN_EMAIL` (DB), `DEVOPS_ALERT_EMAIL` (infra)
- **Inhibiciones:** critical+warnings mismo servicio; DBdown→inhibe slow queries

## Variables de Entorno

```bash
# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<generar-seguro>
GRAFANA_SECRET_KEY=$(openssl rand -hex 32)

# SMTP (para alertas Grafana + AlertManager email)
SMTP_HOST=smtp.gmail.com:587
SMTP_USER=alerts@tu-dominio.com
SMTP_PASSWORD=<app-password-o-key>
ALERT_FROM_EMAIL=alerts@tu-dominio.com

# Destinatarios email
ADMIN_ALERT_EMAIL=admin@tu-dominio.com
DB_ADMIN_EMAIL=dba@tu-dominio.com
DEVOPS_ALERT_EMAIL=devops@tu-dominio.com

# Slack (webhook entrante)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Sentry (si se usa self-hosted)
SENTRY_SECRET_KEY=$(openssl rand -hex 32)
```

## Dashboards

### ERP Nexus — Production Monitoring

**9 paneles:**

| Panel | Tipo | Métrica | Descripción |
|-------|------|---------|-------------|
| HTTP Request Rate | timeseries | `sum(rate(django_http_responses_total[1m])) by (status_code)` | Requests por segundo por código |
| HTTP Error Rate | timeseries (%) | `rate(django_http_responses_total{status=~"5.."}) / total` | Porcentaje errores 5xx |
| Response Latency | timeseries (s) | `histogram_quantile(0.50/0.95/0.99, ...)` | P50/P95/P99 latencia |
| DB Query Duration | timeseries (s) | `histogram_quantile(0.99, django_db_query_duration_seconds_bucket)` | P99 consultas DB |
| Celery Queue Length | gauge | `celery_queue_length` | Tareas pendientes |
| Host CPU & Memory | timeseries (%) | `node_cpu_seconds_total`, `node_memory_*` | Uso CPU y memoria |
| Disk Usage % | timeseries (%) | `node_filesystem_*` | Porcentaje disco usado |
| Service Health | stat | `up{job=~"..."} ` | Estado servicios (1=up) |
| Active Alerts | stat | `ALERTS{alertstate="firing/pending"}` | Alertas activas |

**Variables:** `$host` (filtra nodo), `$service` (filtra servicio)

## Reglas de Alerta

### Critical (notificación inmediata Slack + Email)

| Alerta | Condición | For | Descripción |
|--------|-----------|-----|-------------|
| `HighResponseLatency` | P95 > 1s | 5m | Latencia alta en Django |
| `High5xxErrorRate` | Tasa 5xx > 5% | 2m | Errores servidor elevados |
| `DatabaseDown` | `up{job="postgres"} == 0` | 1m | PostgreSQL inaccesible |
| `RedisDown` | `up{job="redis"} == 0` | 1m | Redis inaccesible |
| `ContainerDown` | `up{job=~"django\|celery\|cadvisor\|nginx"} == 0` | 2m | Contenedor caído |
| `SSLCertificateExpiring` | cert expiry < 7d | 1h | Certificado por expirar |

### Warnings (notificación email)

| Alerta | Condición | For | Descripción |
|--------|-----------|-----|-------------|
| `HostHighCPU` | CPU > 90% | 5m | CPU host saturado |
| `HostLowMemory` | Mem libre < 10% | 5m | Memoria host baja |
| `DiskSpaceLow` | Disco libre < 15% | 10m | Espacio disco crítico |
| `SlowDatabaseQueries` | P99 query > 2s | 10m | Consultas DB lentas |
| `CeleryQueueLengthHigh` | queue length > 100 | 15m | Cola Celery acumulando |

## Comandos de Verificación

```bash
# Prometheus
curl http://localhost:9090/metrics         # Métricas expuestas
curl http://localhost:9090/targets          # Targets activos
curl http://localhost:9090/rules            # Reglas cargadas
curl http://localhost:9090/alerts           # Alertas activas

# Grafana
curl http://localhost:3000/api/health       # Health check API
# Login: admin + $GRAFANA_ADMIN_PASSWORD
# → Dashboards → "ERP Nexus — Production Monitoring"

# cAdvisor
curl http://localhost:8080/metrics          # Container metrics
curl http://localhost:8080/                # UI web

# Node Exporter
curl http://localhost:9100/metrics          # Host metrics

# AlertManager
curl http://localhost:9093                  # UI
curl -X POST http://localhost:9093/-/reload # Recargar config
```

## Troubleshooting

| Problema | Diagnóstico | Solución |
|----------|-------------|----------|
| No hay métricas en Prometheus | `curl localhost:9090/targets` → targets DOWN | Verificar `/metrics/` endpoint en app, network Docker |
| Dashboard no carga | `curl localhost:3000` → 503 | Verificar volumen `grafanadata`, logs `docker-compose logs grafana` |
| Alertas no llegan a Slack | `curl localhost:9093` → config ok | Verificar `SLACK_WEBHOOK_URL`, network, inhibitions |
| cAdvisor sin datos | `curl localhost:8080/metrics` vacío | Verificar mounts `/` y `/var/run` (privilegiado) |
| Reglas no activas | `curl localhost:9090/rules` → errores YAML | Validar YAML syntax, recargar Prometheus (`kill -HUP`) |

## Retención de Datos

| Servicio | Retención | Config |
|----------|-----------|--------|
| Prometheus | 30 días | `--storage.tsdb.retention.time=30d` |
| cAdvisor | en memoria (no persistente) | — |
| Node Exporter | en memoria (no persistente) | — |
| Grafana | persistente en volumen `grafanadata` | — |
| AlertManager | estado en `alertmanagerdata` volumen | — |

## Enlaces Útiles

- Prometheus UI: http://localhost:9090
- Grafana: http://localhost:3000
- cAdvisor: http://localhost:8080
- Node Exporter metrics: http://localhost:9100/metrics
- AlertManager: http://localhost:9093
- Runbooks: `docs/ALERTING_RULES.md`

---

**Nota:** Para que las métricas Django estén disponibles, instalar `django-prometheus` y configurar `INSTALLED_APPS`, `MIDDLEWARE` y `urls.py` (ver Phase 2.5 guide).
