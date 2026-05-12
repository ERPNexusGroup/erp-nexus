# M3 Phase 2.5 — Monitoring Stack

**Estado:** ✅ COMPLETADO (2026-05-12)
**Commit:** (pendiente)
**Tests:** 53 integration tests passed

## 🎯 Objetivo

Stack completo de monitoreo y observabilidad para producción:

| Componente | Imagen | Puerto | Propósito |
|------------|--------|--------|-----------|
| **Prometheus** | `prom/prometheus:v2.52.0` | 9090 | Recolección y almacenamiento de métricas |
| **Grafana** | `grafana/grafana:10.4.2-oss` | 3000 | Dashboards visuales + alertas UI |
| **cAdvisor** | `gcr.io/cadvisor/cadvisor:v0.49.1` | 8080 | Métricas de contenedores Docker |
| **Node Exporter** | `prom/node-exporter:v1.7.0` | 9100 | Métricas del host (CPU, RAM, Disk) |
| **AlertManager** | `prom/alertmanager:v0.27.0` | 9093 | Enrutamiento y gestión de alertas |

## 📦 Entregables

| Archivo | Estado | Descripción |
|---------|--------|-------------|
| `monitoring/prometheus/prometheus.yml` | ✅ | Config scrape jobs (django, celery, cadvisor, node, alertmanager) |
| `monitoring/prometheus/alerts/erp_nexus_rules.yml` | ✅ | 12 reglas de alerta (7 critical + 5 warnings) |
| `monitoring/grafana/provisioning/datasources/prometheus.yml` | ✅ | Data source Prometheus auto-config |
| `monitoring/grafana/provisioning/dashboards/erp_nexus.yml` | ✅ | Dashboard provisionado |
| `monitoring/grafana/provisioning/config/grafana.ini` | ✅ | Config: admin, SMTP, seguridad |
| `monitoring/grafana/dashboards/erp_nexus.json` | ✅ | Dashboard predefinido (9 paneles) |
| `monitoring/alertmanager/alertmanager.yml` | ✅ | Rutas de alerta: Slack + Email |
| `docker-compose.prod.yml` | ✅ | Servicios de monitoreo agregados + volúmenes |
| `.env.prod.example` | ✅ | Variables Grafana, SMTP, canales de notificación |
| `apps/core_marketplace/tests/test_monitoring_integration.py` | ✅ | 53 tests de validación |

## 🔧 Configuración detallada

### Prometheus (`prometheus.yml`)

Scrape配置:
- **django**: puerto 8000, path `/metrics/` (django-prometheus)
- **celery**: puerto 8000 (métricas worker via django-prometheus)
- **cadvisor**: puerto 8080 (container CPU/memory/network)
- **node-exporter**: puerto 9100 (host metrics)
- **alertmanager**: puerto 9093 (health check)

Retención: **30 días** (configurado en docker-compose command flag).

### Reglas de alerta (`erp_nexus_rules.yml`)

#### Grupo: `erp_nexus_critical` (7 alertas)
| Alert | Condition | For | Severity |
|-------|-----------|-----|----------|
| `HighResponseLatency` | P95 > 1s | 5m | critical |
| `High5xxErrorRate` | 5xx rate > 5% | 2m | critical |
| `DatabaseDown` | `up{job="postgres"} == 0` | 1m | critical |
| `RedisDown` | `up{job="redis"} == 0` | 1m | critical |
| `ContainerDown` | `up{job=~"django\|celery\|cadvisor\|nginx"} == 0` | 2m | critical |
| `SSLCertificateExpiring` | cert expiry < 7d | 1h | critical |

#### Grupo: `erp_nexus_warnings` (5 alertas)
| Alert | Condition | For | Severity |
|-------|-----------|-----|----------|
| `HostHighCPU` | CPU > 90% | 5m | warning |
| `HostLowMemory` | Mem libre < 10% | 5m | warning |
| `DiskSpaceLow` | Disco libre < 15% | 10m | warning |
| `SlowDatabaseQueries` | P99 query > 2s | 10m | warning |
| `CeleryQueueLengthHigh` | queue length > 100 | 15m | warning |

### Grafana Dashboard (`erp_nexus.json`)

**9 paneles:**
1. HTTP Request Rate (rps) — timeseries
2. HTTP Error Rate (5xx %) — timeseries (percent)
3. Response Latency (P50/P95/P99) — timeseries (seconds)
4. Database Query Duration P99 — timeseries (seconds)
5. Celery Queue Length — gauge
6. Host CPU & Memory Utilisation — timeseries (percent)
7. Disk Usage % — timeseries (percent)
8. Service Health — stat (up=1)
9. Active Alerts — stat (firing/pending)

**Variables模板:**
- `$host` — filtra por nodo
- `$service` — filtra por servicio

### AlertManager (`alertmanager.yml`)

**Rutas:**
- `severity=critical` → `slack-erp-nexus`
- `severity=warning` → `email-admin`
- `service=postgres` → `email-db-admin`
- `service=redis` → `email-devops`

**Inhibiciones:**
- Critical + warning del mismo servicio → no duplicar
- DatabaseDown inhibe SlowDatabaseQueries

## 🔌 Instrumentación de la app

Para que las métricas estén disponibles en `/metrics/`, instalar `django-prometheus`:

```bash
uv add django-prometheus
```

`settings/base.py`:
```python
INSTALLED_APPS += ['django_prometheus']
MIDDLEWARE = (
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
) + MIDDLEWARE + (
    'django_prometheus.middleware.PrometheusAfterMiddleware',
)
```

`urls.py`:
```python
from django.urls import path, include
urlpatterns = [
    path('metrics/', include('django_prometheus.urls')),
    ...  # resto
]
```

Métricas automáticas expuestas:
- `django_http_responses_total` (status_code labels)
- `django_http_response_time_seconds` (histogram buckets)
- `django_db_query_duration_seconds` (histogram)
- `celery_*` (si configurado)

## 🚀 Comandos de rollout

```bash
# 1. Crear directorios de monitoreo (ya creados en repo)
mkdir -p monitoring/{prometheus/{alerts,dashboards},grafana/{provisioning/{datasources,dashboards},dashboards},alertmanager}

# 2. Configurar variables en .env.prod (GRAFANA_ADMIN_PASSWORD, SMTP_*, SLACK_WEBHOOK_URL)

# 3. Arrancar stack de monitoreo
docker-compose -f docker-compose.prod.yml up -d \
  prometheus grafana cadvisor node-exporter alertmanager

# 4. Verificaréndose
curl http://localhost:9090/metrics         # Prometheus
curl http://localhost:3000                 # Grafana (login admin:$GRAFANA_ADMIN_PASSWORD)
curl http://localhost:8080/metrics         # cAdvisor
curl http://localhost:9100/metrics         # Node Exporter
curl http://localhost:9093                 # AlertManager

# 5. Dashboards
# Acceder http://$DOMAIN:3000 → Dashboards → "ERP Nexus"
# (provisioning automático carga erp_nexus.json)

# 6. Configurar alertas en AlertManager (Slack/Email)
# Editar monitoring/alertmanager/alertmanager.yml con webhooks reales
# Recargar: curl -X POST http://localhost:9093/-/reload

# 7. Verificar reglas cargadas en Prometheus
# http://localhost:9090/rules →buscar "erp_nexus_*"

# 8. (Opcional) Sentry self-hosted
# docker-compose -f docker-compose.prod.yml run --rm sentry sentry upgrade
# docker-compose -f docker-compose.prod.yml run --rm sentry sentry createuser
# docker-compose -f docker-compose.prod.yml up -d sentry
```

## 🧪 Tests (53 passed)

| Test Class | Tests | Estado |
|------------|-------|--------|
| TestPrometheusConfiguration | 9 | ✅ |
| TestAlertRules | 6 | ✅ |
| TestGrafanaProvisioning | 8 | ✅ |
| TestAlertManager | 6 | ✅ |
| TestDockerComposeIntegration | 16 | ✅ |
| TestDockerComposeVolumes | 3 | ✅ |
| TestEnvironmentVariables | 5 | ✅ |
| TestIntegration | 2 | ✅ |

## 📊 Métricas monitoreadas

| Métrica | Origen | Descripción |
|---------|--------|-------------|
| `django_http_responses_total` | Django | Request rate por status code |
| `django_http_response_time_seconds` | Django | Latency histogram (P50/P95/P99) |
| `django_db_query_duration_seconds` | Django | DB query latency |
| `celery_queue_length` | Celery | Tareas pendientes por queue |
| `node_cpu_utilisation` | Node Exporter | % CPU usado |
| `node_memory_MemAvailable_bytes` | Node Exporter | Memoria disponible |
| `node_filesystem_avail_bytes` | Node Exporter | Espacio disco libre |
| `container_spec_cpu_quota` | cAdvisor | CPU quota por contenedor |
| `container_memory_usage_bytes` | cAdvisor | Memoria usada por contenedor |
| `up{job="*"}` | Prometheus | Health check por target |

## 🔔 Canales de notificación

| Severity | Canal | Destinatario |
|----------|-------|--------------|
| critical | Slack (#alerts-erp-nexus) | DevOps + On-call |
| critical | Email | ADMIN_ALERT_EMAIL |
| warning | Email | ADMIN_ALERT_EMAIL + DB_ADMIN_EMAIL (DB) + DEVOPS_ALERT_EMAIL (infra) |

## ⚠️ Notas de deployment

- **Grafana SMTP**: configurar `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` para alertas email
- **Slack webhook**: `SLACK_WEBHOOK_URL` obligatorio para alerted críticos
- **Grafana admin**: cambiar `GRAFANA_ADMIN_PASSWORD` en producción
- **Retención Prometheus**: 30 días (ajustable en `docker-compose` command flag)
- **Health checks**: Todos los servicios tienen `depends_on` con condiciones
- **Persistencia**: Datos Prometheus en `promdata`, Grafana en `grafanadata`, AlertManager en `alertmanagerdata`

---

**Siguiente sprint:** Post-M3 — deployment en producción + runbooks de respuesta a incidentes.
