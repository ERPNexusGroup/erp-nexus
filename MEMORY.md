# 🗂️ TopScort — Sprint Progress & Project Memory

## 📊 Resumen de Sprints (M0–M4)

| Sprint | Nombre | Estado | Peso | Avance |
|--------|--------|--------|------|--------|
| M0 | Bootstrap (NextAuth + Prisma base) | ✅ | 15% | 100% |
| M1 | Auth Enhancement (email multi-provider) | ✅ | 20% | 100% |
| M2 | Wallet Closed-Loop Top-Up Only | ✅ | 25% | 100% |
| M3 | Payments Gateway Foundation | ✅ | 25% | 100% |
| M4 | Monitoring + SSL + Nginx | ✅ | 15% | 100% |
| **M4.1** | **Home UX — Map Styling** | ✅ | - | 100% | - | 100% |
| **TOTAL** | | | **100%** | **100%** | | **100%** | **100%** |

---

## 🌿 GitHub Flow — Estado de Ramas

| Rama | Estado | Último commit |
|------|--------|---------------|
| `main` | ✅ Activa | `460cc36` — docs: SEED + PAUL init |
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
- ** migrations:** M2 aplicada, `withdrawal` y `tip` excluidos (modelo legal)
- **API:** `/api/wallet?action=topup` (nuevo), `withdraw` eliminado, `payment` → `purchase`
- **Admin:** `/api/admin/withdrawals/*` eliminado (API + backoffice UI)
- **Stats:** `pendingWithdrawals` → `pendingCommissions`
- **Cleanup:** ToolDefinition + ToolPurchase tablas eliminadas (reemplazadas por subscriptions)

### M3 — Payments Gateway Foundation
- **Schema:** `PaymentProvider` (config), `PaymentIntent` (intenciones), `WalletTransaction.paymentIntentId`
- **API:** `/api/payments/intent` (stub), `/api/payments/webhook` (placeholder), `/api/payments/providers`
- **Wallet:** topup endpoint integra PaymentIntent → pending deposit
- **Types:** `PaymentIntentStatus`, `PaymentProviderName` enums

### M3 Phase 2.4 — SSL + Nginx Reverse Proxy ✅
- **Nginx:** reverse proxy con TLS termination (TLSv1.2/1.3), HSTS header (max-age 1 año)
- **Certbot:** auto-renovación cada 12h + webroot challenge + volúmenes persistentes
- **Seguridad:** CSP, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy
- **Static/media:** serving directo desde Nginx con cache (1y static, 30d media) + gzip compression
- **Docker:** servicios nginx + certbot en `docker-compose.prod.yml` con dependencias
- **Tests:** 45 integration tests validando SSL, headers, redirects, volúmenes, env vars
- **Docs:** `docs/SSL_NGINX.md` — despliegue, configuración, troubleshooting

### M4 — Monitoring Stack + SSL + Nginx
- **Monitoring:** Prometheus + Grafana + cAdvisor + Node Exporter + AlertManager
- **SSL:** Nginx reverse proxy con Let's Encrypt (certbot auto-renew)
- **Docker:** `docker-compose.prod.yml` (stack completo), `Dockerfile.prod` (multi-stage)
- **Docs:** `docs/DEPLOYMENT.md` guía completa (prereqs, SSL, monitoring, backup, troubleshooting)

### M4.1 — Home UX Map Improvements
- **Mapa interactivo:** relieve topográfico con estilo neutro (adaptativo tema dark/light)
- **Países activos:** marcadores dorados/naranjas con efecto glow + animaciones hover (scale)
- **Países inactivos:** marcadores grises sutiles
- **Controles de mapa:** zoom + pan + fullscreen integrados
- **Leyenda overlay:** explicativa de colores de marcadores
- **Centro del mapa:** Sudamérica (long -60°, lat -15°, zoom 2.5)
- **Contenedor:** cristal esmerilado (glassmorphism) con borde redondeado
- **Tooltip hint:** centered badge debajo del mapa

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

# Monitoring (M4)
GRAFANA_ADMIN_PASSWORD=<secure>
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

---

## 📝 Decisions & Lessons Learned

| Fecha | Decisión | Razón |
|-------|----------|-------|
| 2026-05-11 | Wallet closed-loop (sin retiros) | Modelo legal SaaS — fondos solo para compras internas |
| 2026-05-11 | Email multi-provider (Resend primary) | Resiliencia + deliverability |
| 2026-05-11 | TransactionType enum (7 valores) | Type safety + claridad contable |
| 2026-05-11 | PaymentIntent separado de WalletTransaction | Separación de responsabilidades: external gateway vs internal ledger |

---

## 🚀 Release Checklist (pre-merge a `main`)

- [ ] QA en rama `qa` validado (testing UAT)
- [ ] Migraciones de DB aplicadas en staging
- [ ] SSL certificate obtenido (production domain)
- [ ] Monitoring dashboards verificado (Grafana)
- [ ] Sentry issues revisadas (0 críticos)
- [ ] `.env.prod` actualizado en servidor
- [ ] Backup strategy probado (restore from backup)
- [ ] CHANGELOG.md actualizado
- [ ] PR revisado y aprobado (2+ reviewers)
- [ ] Merge a `main` + tag semver (ej: `v1.0.0-m4`)

---

## 📚 Documentación Relacionada

- `docs/GITHUB_FLOW.md` — Flujo de ramas y comandos
- `docs/DEPLOYMENT.md` — Guía completa de deployment (SSL, monitoring, backup)
- `docs/API.md` — Especificación de endpoints (por crear)
- `SEED.md` — Planificación de próximo sprint (M5: payout automation)

---

*última actualización: 2026-05-11 | por JARVIS (OpenClaw Assistant)*
