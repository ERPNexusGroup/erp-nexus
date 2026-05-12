# M3 Phase 2.4 — SSL/TLS + Nginx Reverse Proxy

**Estado:** ✅ COMPLETADO (2026-05-12)
**Commit:** 7033989 → 5021d6a
**Tests:** 45 integration tests passed

## 🎯 Objetivo

Configurar Nginx como reverse proxy con terminación SSL/TLS (Let's Encrypt) para producción:

- HTTP → HTTPS 301 redirect + HSTS (max-age 1 año)
- TLSv1.2 y TLSv1.3 con cifrado moderno (ECDHE, AES128-GCM-SHA256)
- Security headers estrictos (CSP, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy)
- Serving eficiente de static/media files con caching agresivo
- Compresión gzip (text/css, application/javascript, etc.)
- Certbot para certificados auto-renovables cada 12h (webroot challenge)
- Volúmenes Docker persistentes para Certbot (certbot_conf, certbot_data)
- Health checks + monitorización básica

## 📦 Entregables

### Archivos creados/modificados

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `nginx/nginx.conf` | nuevo | Configuración Nginx completa con TLS, headers, proxy, static/media |
| `docker-compose.prod.yml` | mod | Agregados servicios `nginx` y `certbot`, volúmenes certbot |
| `docs/SSL_NGINX.md` | nuevo | Guía de deploy, configuración, comandos, troubleshooting |
| `apps/core_marketplace/tests/test_ssl_nginx_integration.py` | nuevo | Suite de 45 tests de integración |
| `.env.prod.example` | mod | Agregadas `DOMAIN` y `SSL_EMAIL` |

### Configuración Nginx clave

```nginx
worker_processes auto;
events { worker_connections 1024; }

http {
    # --- HTTP → HTTPS redirect (puerto 80) ---
    server {
        listen 80;
        server_name _;
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        location / { return 301 https://$server_name$request_uri; }
    }

    # --- HTTPS server (puerto 443) ---
    server {
        listen 443 ssl http2;
        server_name $DOMAIN;

        # SSL certificates (Let's Encrypt)
        ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
        ssl_dhparam /etc/nginx/ssl/dhparam.pem;

        # TLS protocols
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:...;
        ssl_prefer_server_ciphers off;
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-Frame-Options DENY always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

        # Static files (1y cache)
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable, max-age=31536000";
            access_log off;
        }

        # Media files (30d cache)
        location /media/ {
            alias /app/media/;
            expires 30d;
            add_header Cache-Control "public, max-age=2592000";
            access_log off;
        }

        # Proxy to Gunicorn
        location / {
            proxy_pass http://web:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
        }

        # Health check
        location /health/ { proxy_pass http://web:8000/health/; access_log off; }
    }
}
```

### Docker Compose (certbot + nginx)

```yaml
services:
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl/dhparam.pem:/etc/nginx/ssl/dhparam.pem:ro
      - certbot_conf:/etc/letsencrypt:ro
      - certbot_data:/var/lib/letsencrypt:ro
      - static:/app/static:ro
      - media:/app/media:ro
    depends_on:
      web:
        condition: service_healthy
      certbot:
        condition: service_started

  certbot:
    image: certbot/certbot
    volumes:
      - certbot_conf:/etc/letsencrypt
      - certbot_data:/var/lib/letsencrypt
      - ./nginx/certbot/www:/var/www/certbot:rw
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew --quiet --no-self-upgrade; sleep 12h & wait $${!}; done;'"
    restart: unless-stopped

volumes:
  certbot_conf:
  certbot_data:
```

## ✅ Tests de validación (45 tests)

```
TestNginxConfiguration          7 PASSED  (archivos, bloques, puertos)
TestSSLConfiguration            6 PASSED  (dhparams, cert paths, protocols, ciphers)
TestSecurityHeaders             6 PASSED  (HSTS, CSP, X-Frame, X-Content, X-XSS, Referrer)
TestStaticAndMedia              4 PASSED  (locations, caching headers)
TestHTTPtoHTTPSRedirect         3 PASSED  (server block 80, ACME, 301 redirect)
TestDockerComposeIntegration   10 PASSED  (nginx service, ports, certbot, depends_on, volumes ro)
TestCertbotVolumes              5 PASSED  (volúmenes definidos, mounts conf/data/webroot)
TestEnvironmentVariables        4 PASSED  (DOMAIN, SSL_EMAIL en .env.prod.example)

─────────────────────────────────────────────────────
45 passed, 1 warning in 0.11s ✅
```

## 🔧 Comandos post-deploy

```bash
# 1. Generar DH params para perfect forward secrecy (2048-bit)
openssl dhparam -out nginx/ssl/dhparam.pem 2048

# 2. Configurar DOMAIN y SSL_EMAIL en producción
#    Editar .env.prod o variables del entorno del servidor

# 3. Arrancar stack completo
docker-compose -f docker-compose.prod.yml up -d

# 4. Obtener certificado SSL inicial (una vez)
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d $DOMAIN \
  --email $SSL_EMAIL \
  --agree-tos \
  --no-eff-email \
  --force-renewal

# 5. Reiniciar nginx para cargar certificado
docker-compose -f docker-compose.prod.yml restart nginx

# 6. Verificar logs de certbot (renovación automática cada 12h)
docker-compose -f docker-compose.prod.yml logs certbot -f
```

## 📚 Documentación

- `docs/SSL_NGINX.md` — Guía completa de despliegue SSL + Nginx
- `nginx/nginx.conf` — Configuración reference
- `docker-compose.prod.yml` — Servicios nginx + certbot

## ⚠️ Notas

- **dhparam.pem** no está versionado (archivo generado). Generar en deploy con `openssl dhparam`.
- Certbot renueva automáticamente cada 12h. Monitorear logs en producción.
- Los certificados residen en volúmenes Docker `certbot_conf` y `certbot_data` (persistentes).
- HSTS preload: una vez en producción verificar en <https://hstspreload.org/>.
- CSP actual permite `unsafe-inline` para compatibilidad; considerar CSP estricto en futuras iteraciones.

---

**Migración desde HTTP → HTTPS:**

Una vez certificado activo, todo tráfico en puerto 80 redirige 301 → 443. Actualizar `NEXT_PUBLIC_APP_URL` y `DOMAIN` en `.env.prod` a `https://$DOMAIN`.
