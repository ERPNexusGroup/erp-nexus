# 🐘 Nginx SSL Reverse Proxy — ERP Nexus

**Guía de despliegue HTTPS (Let's Encrypt) con Nginx**
**Versión:** 1.0.0
**Fecha:** 2026-05-12

---

## 📋 Índice

1. [Prerrequisitos](#prerrequisitos)
2. [Generar DH params](#generar-dh-params)
3. [Primer certificado SSL](#primer-certificado-ssl)
4. [Despliegue Nginx](#despliegue-nginx)
5. [Verificación](#verificación)
6. [Auto-renew](#auto-renew)
7. [Troubleshooting](#troubleshooting)
8. [Checklist](#checklist)

---

## Prerrequisitos

- **Dominio público** con registro `A` apuntando a la IP del servidor
- **Puertos 80 y 443 abiertos** en el firewall/host
- Stack M3 Phases 2.1–2.3 desplegados y funcionando
- Variables `DOMAIN` y `SSL_EMAIL` en `.env.prod` (o `.env` local)

---

## Generar DH params

Los **Diffie-Hellman parameters** habilitan perfect forward secrecy (PFS).

```bash
cd /home/wcun/.openclaw/workspace/repos/erp-nexus
mkdir -p nginx/ssl
openssl dhparam -out nginx/ssl/dhparam.pem 2048
chmod 600 nginx/ssl/dhparam.pem
```

> El archivo `dhparam.pem` (~2KB) puede committearse o ignorarse vía `.gitignore`. Nginx lo lee en runtime.

---

## Primer certificado SSL

### Opción A — Standalone (recomendado primera vez)

```bash
# Detener nginx temporalmente si ya corre (puerto 80 en uso)
docker compose -f docker-compose.prod.yml stop nginx

# Obtener certificado (Let's Encrypt)
docker compose run --rm certbot certbot certonly \\
  --standalone \\
  --domains "${DOMAIN}" \\
  --email "${SSL_EMAIL}" \\
  --agree-tos \\
  --no-eff-email \\
  --force-renewal
```

### Opción B — Webroot (Nginx ya corriendo)

```bash
mkdir -p nginx/certbot/www

docker compose run --rm certbot certbot certonly \\
  --webroot -w /var/www/certbot \\
  --domains "${DOMAIN}" \\
  --email "${SSL_EMAIL}" \\
  --agree-tos
```

**Éxito:**
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/${DOMAIN}/fullchain.pem
```

---

## Despliegue Nginx

```bash
docker compose -f docker-compose.prod.yml up -d nginx
docker compose logs -f nginx
```

**Puertos expuestos:**
- `80` — HTTP → redirect automático a HTTPS
- `443` — HTTPS (servidor principal)

---

## Verificación

### 1. HTTP → HTTPS redirect

```bash
curl -I http://${DOMAIN}
# Esperado: HTTP/1.1 301 Moved Permanently
# Location: https://${DOMAIN}/
```

### 2. Security headers (HTTPS)

```bash
curl -I https://${DOMAIN} | grep -iE "strict-transport|frame-options|content-type-options|xss-protection|referrer-policy"
```

**Esperado:**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

### 3. Certificado SSL válido

```bash
echo | openssl s_client -connect ${DOMAIN}:443 -servername ${DOMAIN} 2>/dev/null \\
  | openssl x509 -noout -dates -subject
```

Salida:
```
notBefore=May 12 00:00:00 2026 GMT
notAfter=Aug 10 23:59:59 2026 GMT
subject= /CN=${DOMAIN}
```

### 4. SSL Labs Rating

Visita: `https://www.ssllabs.com/ssltest/analyze.html?d=${DOMAIN}`
**Objetivo:** calificación **A** o **A+**

---

## Auto-renew

Certbot renueva automáticamente cada 12 horas dentro del contenedor:

```yaml
# docker-compose.prod.yml — certbot service
entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew --quiet --no-self-upgrade; sleep 12h & wait $${!}; done;'"
```

### Probar renovación (dry-run)

```bash
docker compose -f docker-compose.prod.yml run --rm certbot renew --dry-run
```

Sin errores → auto-renew OK ✅

### Logs de renovación

```bash
docker compose -f docker-compose.prod.yml logs -f certbot
```

Buscar: `Certbot renewal outcome: success`

---

## Troubleshooting

| Problema | Diagnóstico | Solución |
|----------|-------------|----------|
| `certbot: Too many certificates` | Rate limit Let's Encrypt (50/semana) | Usar `--dry-run` en tests, esperar 1 semana |
| `NXDOMAIN` | Dominio no resuelve a IP | Verificar registro A DNS (`dig ${DOMAIN}`) |
| Nginx 502 Bad Gateway | Gunicorn no escucha en 8000 | `docker compose ps web`; `docker compose logs web` |
| Cert no encontrado por Nginx | Certbot no ejecutado o volúmenes mal montados | `docker compose exec nginx ls /etc/letsencrypt/live/` |
| HSTS persistente en browser | Cache HSTS previo | Probar en modo incógnito o limpiar HSTS en browser |
| Static files 404 | `collectstatic` no ejecutado | `docker compose exec web python manage.py collectstatic --noinput` |

---

## Checklist — Phase 2.4 COMPLETADO

- [ ] `nginx/nginx.conf` existe con sintaxis válida
- [ ] `nginx/ssl/dhparam.pem` generado (2048-bit)
- [ ] `docker-compose.prod.yml` incluye servicios `nginx` + `certbot`
- [ ] `docker-compose.prod.yml` declara volúmenes: `certbot_conf`, `certbot_data`, `static`, `media`
- [ ] `.env.prod` contiene `DOMAIN` y `SSL_EMAIL`
- [ ] `docs/SSL_NGINX.md` documentación completa
- [ ] `apps/core_marketplace/tests/test_ssl_nginx_integration.py` ≥12 assertions pasan
- [ ] **Primer certificado obtenido** (certbot manual)
- [ ] Nginx levanta sin errores: `docker compose logs nginx`
- [ ] HTTP → HTTPS redirect funciona (`curl -I http://${DOMAIN}` → 301)
- [ ] HTTPS 200 OK + security headers (`curl -I https://${DOMAIN}`)
- [ ] Auto-renew dry-run exitoso (`certbot renew --dry-run`)
- [ ] SSL Labs rating **A** o superior

---

## 🔄 Siguiente Fase

Una vez checklist completo → **M3 Phase 2.5 — Monitoring Stack**
(Prometheus + Grafana + AlertManager + Sentry)
