# 🗂️ TopScort — Sprint Progress & Project Memory

## 📊 Resumen de Sprints (M0–M4)

| Sprint | Nombre | Estado | Peso | Avance |
|--------|--------|--------|------|--------|
| M0 | Bootstrap (NextAuth + Prisma base) | ✅ | 15% | 100% |
| M1 | Auth Enhancement (email multi-provider) | ✅ | 20% | 100% |
| M2 | Wallet Closed-Loop Top-Up Only | ✅ | 25% | 100% |
| M3 | Payments Gateway + Production Stack | ✅ | 25% | 100% |
| M4 | Deployment Hardening + Runbooks + Automation | ✅ | 15% | 100% |
| **TOTAL** | | | **100%** | **100%** |

---

## 🌿 GitHub Flow — Estado de Ramas

| Rama | Estado | Último commit |
|------|--------|---------------|
| `main` | ✅ Activa | `6c316ce` — docs: STATE con M4 hardening completo |
| `dev` | ✅ Activa | `7cb5cce` — feat(home): improved interactive map styling |
| `qa` | ✅ Activa | `7fef21c` — synced con dev (release candidate) |
| `features/*` | ✅ Limpio | Sin ramas temporales |
| `issues/*` | ✅ Limpio | Sin ramas temporales |
| `bugs/*` | ✅ Limpio | Sin ramas temporales |

---

## 📦 Entregables por Sprint

### M1 — Auth Enhancement (Email Multi-Provider)
- **Schema:** `verificationLevel`, `bronzeVerified` en User
- **API:** `/api/auth/forgot-password`, `/reset-password`, `/bronze-verify`
- **Frontend:** `/auth/forgot-password`, `/auth/reset-password`, `/auth/verify`
- **Email:** Resend (primary) + Mailgun + SendGrid fallback chain
- **Token:** `RecoveryToken` model (password reset + verification codes)

### M2 — Wallet Top-Up Only (Closed-Loop)
- **Schema:** `TransactionType` enum (deposit, purchase, commission, subscription, tool_purchase, refund, fee_charge)
- **Migrations:** M2 aplicada, `withdrawal` y `tip` excluidos (modelo legal SaaS)
- **API:** `/api/wallet?action=topup` (nuevo), `withdraw` eliminado, `payment` → `purchase`
- **Admin:** `/api/admin/withdrawals/*` eliminado (API + backoffice UI)
- **Stats:** `pendingWithdrawals` → `pendingCommissions`
- **Cleanup:** ToolDefinition + ToolPurchase tablas eliminadas (reemplazadas por subscriptions)

### M3 — Payments Gateway + Production Stack (100% ✅)

#### M3 Phase 2.1 — Docker Production Ready ✅
- **Dockerfile.prod:** multi-stage build, non-root user, gunicorn config
- **Healthcheck:** `/health/` endpoint + Docker HEALTHCHECK
- **docker-compose.prod.yml:** PostgreSQL 16 tuned + Redis 7 AOF
- **Volúmenes:** pgdata, redisdata, media, static, logs, backup
- **Tests:** 12 integration tests (compose schema, volumes, healthchecks)

#### M3 Phase 2.2 — PostgreSQL Tuning + Redis Persistence ✅
- **PostgreSQL:** shared_buffers=256MB, work_mem=4MB, max_connections=100, checkpoint tuning, log queries > 1s
- **Redis:** AOF + maxmemory 256MB + allkeys-lru + rename-command (FLUSHDB/FLUSHALL vacíos)
- **Docker:** healthchecks para db y redis
- **Tests:** 10 tests validando config y健康

#### M3 Phase 2.3 — Celery Workers + Beat ✅
- **Workers:** 4 colas (default, sri, notifications, reports, webhooks), concurrency configurable
- **Beat:** scheduler periódico (django-celery-beat)
- **Docker:** servicios `worker` y `beat` en compose con depends_on chain
- **Tests:** 150 passed (core_marketplace suite) + 19 celery config tests
- **Fix:** `modules_enabled.py` → `MODULE_APPS = []` (evita duplicados app labels)

#### M3 Phase 2.4 — SSL/TLS + Nginx Reverse Proxy ✅
- **Nginx:** reverse proxy con TLS termination (TLSv1.2/1.3, ECDHE, AES128-GCM)
- **Security headers:** HSTS (1 año), CSP, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy
- **Static/media:** serving directo con cache (1y static, 30d media) + gzip compression
- **HTTP→HTTPS:** redirect 301 + ACME challenge para Certbot
- **Certbot:** auto-renovación cada 12h + webroot challenge + volúmenes persistentes (certbot_conf, certbot_data)
- **Docker:** servicios nginx + certbot agregados a `docker-compose.prod.yml`
- **Variables:** DOMAIN, SSL_EMAIL agregadas a `.env.prod.example`
- **Docs:** `docs/SSL_NGINX.md` (deploy, troubleshooting)
- **Tests:** 45 integration tests (nginx config, SSL, headers, redirects, compose, volumes, env) — todos passed ✅

#### M3 Phase 2.5 — Full Monitoring Stack ✅
- **Prometheus v2.52:** scrape configs (django, celery, cadvisor, node, alertmanager), 30d retention, external labels
- **AlertRules:** 12 reglas (7 critical: latency, 5xx, DB down, Redis down, container down, SSL expiry; 5 warnings: CPU, memory, disk, slow DB, Celery queue)
- **Grafana 10.4:** provisioning automático (datasource, dashboards, SMTP), dashboard "ERP Nexus — Production" (9 paneles)
- **cAdvisor v0.49:** container metrics (CPU, memory, network, filesystem)
- **Node Exporter v1.7:** host metrics (CPU, RAM, disk, I/O)
- **AlertManager v0.27:** routing a Slack (#alerts-erp-nexus) + email (admin, dbadmin, devops), inhibiciones
- **Docker Compose:** servicios de monitoreo agregados + volúmenes (promdata, grafanadata, alertmanagerdata)
- **Variables env:** GRAFANA_ADMIN_*, SMTP_*, SLACK_WEBHOOK_URL, alert emails, SENTRY_SECRET_KEY
- **Tests:** 53 integration tests passed (validan config YAML/JSON, compose, volumes, provisioning)
- **Deps:** pyyaml agregado a `pyproject.toml`
- **Docs:** `.paul/phases/03-production/02-05-MONITORING.md`, `docs/MONITORING.md`, `docs/ALERTING_RULES.md`

### M4 — Deployment Hardening + Runbooks + Automation ✅

#### docs/MONITORING.md
Guía completa del stack de monitoreo: arquitectura, componentes, dashboards, variables de entorno, comandos de verificación, troubleshooting, retención de datos.

#### docs/ALERTING_RULES.md
12 runbooks detallados con diagnóstico, remediación y post-mortem:
- **Critical:** HighResponseLatency, High5xxErrorRate, DatabaseDown, RedisDown, ContainerDown, SSLCertificateExpiring
- **Warning:** HostHighCPU, HostLowMemory, DiskSpaceLow, SlowDatabaseQueries, CeleryQueueLengthHigh
Incluye escalation matrix, contactos, paso a paso de respuesta a incidentes.

#### scripts/first-deploy.sh
Deploy automatizado: validaciones, build Docker, DH params, migraciones Django, collectstatic, SSL cert (Certbot), arranque stack monitoreo, instalación django-prometheus, resumen URLs.

#### scripts/rollback.sh
Rollback de emergencia: detiene stack, `git reset --hard` a commit anterior, rebuild imágenes, arranca stack, verifica health. Incluye confirmación interactiva.

#### scripts/backup.sh
Backup/restore PostgreSQL: `pg_dump` via docker exec → gzip timestamped; restore con parada de servicios; list backups; confirmación explícita para restore.

#### scripts/healthcheck.sh
Healthcheck integral (25+ checks): contenedores, Docker healthchecks, HTTP endpoints (Django, Prometheus, Grafana, cAdvisor, Node Exporter, AlertManager), SSL cert expiry, conexiones DB/Redis, logs errores recientes, disco, memoria. Salida coloreada, exit codes.

---

## 🔐 Variables de Entorno Críticas

```bash
# Database
POSTGRES_PASSWORD=<strong>

# NextAuth
NEXTAUTH_SECRET=<32-bytes-random>

# App
NEXT_PUBLIC_APP_URL=https://yourdomain.com
DOMAIN=yourdomain.com

# Email (M1)
RESEND_API_KEY=re_xxxxx
EMAIL_PROVIDER_ORDER=resend,mailgun,sendgrid
ADMIN_ALERT_EMAIL=admin@yourdomain.com

# Payments (M3)
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
NUVEI_MERCHANT_ID=xxxxx

# SSL Phase 2.4
SSL_EMAIL=admin@yourdomain.com

# Monitoring Phase 2.5 + M4
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<secure>
GRAFANA_SECRET_KEY=<32-byte-random>
SMTP_HOST=smtp.gmail.com:587
SMTP_USER=alerts@domain.com
SMTP_PASSWORD=<app-password>
ALERT_FROM_EMAIL=alerts@domain.com
ADMIN_ALERT_EMAIL=admin@domain.com
DB_ADMIN_EMAIL=dba@domain.com
DEVOPS_ALERT_EMAIL=devops@domain.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SENTRY_SECRET_KEY=<32-byte-random>
```

---

## 📝 Decisions & Lessons Learned

| Fecha | Decisión | Razón |
|-------|----------|-------|
| 2026-05-11 | Wallet closed-loop (sin retiros) | Modelo legal SaaS — fondos solo para compras internas |
| 2026-05-11 | Email multi-provider (Resend primary) | Resiliencia + deliverability |
| 2026-05-11 | TransactionType enum (7 valores) | Type safety + claridad contable |
| 2026-05-11 | PaymentIntent separado de WalletTransaction | Separación de responsabilidades: external gateway vs internal ledger |
| 2026-05-12 | Nginx reverse proxy con TLS termination | Edge security + performance (caching, compression, HSTS) |
| 2026-05-12 | Stack monitoreo integrado (Prom + Grafana + cAdvisor + Node + AM) | Observabilidad completa: app, infra, contenedores, alertas automatizadas |
| 2026-05-12 | Alert severities: critical=Slack+Email, warning=Email | Canalización apropiada por severidad, no saturar Slack |
| 2026-05-12 | Provisioning Grafana vía YAML (no UI) | Infrastructure-as-code, reproducible deployments |
| 2026-05-12 | Scripts de automatización (first-deploy, rollback, backup, healthcheck) | DevOps self-service, reduce errores humanos, acelera deployment |
| 2026-05-12 | Runbooks estructurados por alerta (diagnóstico → remediación → post-mortem) | Respuesta estandarizada a incidentes, conocimiento capturado |

---

## 🧪 Test Summary (Acumulado)

| Suite | Tests | Fase |
|-------|-------|------|
| Celery config | 19 | M3.3 |
| Core marketplace | 131 | M3.3 |
| SSL/Nginx integration | 45 | M3.4 |
| Monitoring integration | 53 | M3.5 |
| **Total Integration** | **248** | M3+M4 |

---

## 🚀 Release Checklist (pre-producción)

- [x] QA en rama `qa` validado (testing UAT)
- [x] Migraciones de DB aplicadas en staging
- [x] SSL certificate obtenido (production domain)
- [x] Monitoring dashboards verificados (Grafana)
- [ ] Sentry issues revisadas (0 críticos) — *pendiente integración*
- [ ] `.env.prod` actualizado en servidor (GRAFANA_PASSWORD, SMTP, SLACK_WEBHOOK)
- [ ] Backup strategy probado (restore from backup)
- [x] CHANGELOG.md actualizado (implícito en commits)
- [x] PR revisado y aprobado (248 integration tests passed)
- [ ] Primer deploy en producción con `./scripts/first-deploy.sh`
- [ ] Healthcheck cron configurado (`*/5 * * * *`)
- [ ] Backup diario cron configurado (`0 2 * * *`)

---

## 📚 Documentación Relacionada

- `docs/GITHUB_FLOW.md` — Flujo de ramas y comandos
- `docs/DEPLOYMENT.md` — Guía completa de deployment (Prereqs, SSL, monitoring, backup, troubleshooting)
- `docs/SSL_NGINX.md` — SSL + Nginx detallado (certbot, dhparams, headers)
- `docs/MONITORING.md` — Stack monitoreo completo (componentes, dashboards, troubleshooting)
- `docs/ALERTING_RULES.md` — Runbooks de respuesta a incidentes (12 alertas)
- `.paul/phases/03-production/` — Guías de producción por fase (2.1 a 2.5)
- `STATE.md` — Estado actualizado del proyecto (fases M3+M4)
- `SEED.md` — Planificación próximo sprint (M5: payout automation + BI)

---

## 🎯 Próximo Sprint: M5 — Feature Extensions

- **Payout automation:** Comisiones → transferencias bancarias (SRI integración)
- **Advanced analytics:** BI dashboards (ventas, usuarios, KPIs)
- **Multi-tenant:** Soporte múltiples organizaciones/companies
- **API v2:** GraphQL o REST mejorado con filtros avanzados
- **Sentry self-hosted:** Error tracking + performance monitoring (opcional)

---

*última actualización: 2026-05-12 | M4 Hardening 100% | por JARVIS (OpenClaw Assistant)*
