# Tests de verificación SSL + Nginx — ERP Nexus
# Valida configuración Nginx, Certbot, SSL, headers de seguridad

from pathlib import Path
import re

import pytest


BASE = Path(__file__).resolve().parents[3]


class TestNginxConfiguration:
    """Validación de archivos y sintaxis Nginx."""

    def test_nginx_conf_exists(self):
        assert (BASE / "nginx" / "nginx.conf").exists(), "nginx.conf no encontrado"

    def test_nginx_conf_has_worker_processes(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "worker_processes" in content

    def test_nginx_conf_has_events_block(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "events {" in content

    def test_nginx_conf_has_http_block(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "http {" in content

    def test_nginx_conf_has_server_blocks(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert content.count("server {") >= 2, "Se necesitan al menos 2 server blocks (80 y 443)"

    def test_nginx_listen_port_80(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "listen 80" in content or "listen [::]:80" in content

    def test_nginx_listen_port_443_ssl(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "listen 443 ssl http2" in content or "listen [::]:443 ssl http2" in content


class TestSSLConfiguration:
    """Validación de configuración SSL."""

    def test_ssl_dhparams_exist(self):
        assert (BASE / "nginx" / "ssl" / "dhparam.pem").exists(), \
            "dhparam.pem no generado. Ejecutar: openssl dhparam -out nginx/ssl/dhparam.pem 2048"

    def test_ssl_certificate_paths_in_nginx(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "ssl_certificate" in content
        assert "ssl_certificate_key" in content
        assert "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" in content
        assert "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" in content

    def test_ssl_protocols_tls12_and_tls13(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "ssl_protocols TLSv1.2 TLSv1.3" in content

    def test_ssl_ciphers_modern(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "ECDHE" in content and "AES128-GCM-SHA256" in content

    def test_ssl_session_settings(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "ssl_session_timeout" in content
        assert "ssl_session_cache" in content


class TestSecurityHeaders:
    """Validación de headers de seguridad."""

    def test_hsts_header_present(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert 'add_header Strict-Transport-Security' in content
        assert 'max-age=31536000' in content
        assert 'includeSubDomains' in content
        assert 'preload' in content

    def test_x_content_type_options(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "X-Content-Type-Options" in content
        assert "nosniff" in content

    def test_x_frame_options(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "X-Frame-Options" in content
        assert "DENY" in content

    def test_x_xss_protection(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "X-XSS-Protection" in content

    def test_referrer_policy(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "Referrer-Policy" in content

    def test_csp_header(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "Content-Security-Policy" in content


class TestStaticAndMedia:
    """Validación de serving de archivos estáticos y media."""

    def test_static_location_defined(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "location /static/" in content
        assert "alias /app/static/" in content

    def test_media_location_defined(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "location /media/" in content
        assert "alias /app/media/" in content

    def test_static_caching_headers(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        static_block = content.split("location /static/")[1].split("}")[0]
        assert "expires 1y" in static_block or "expires 1 year" in static_block
        assert "Cache-Control" in static_block

    def test_media_caching_headers(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        media_block = content.split("location /media/")[1].split("}")[0]
        assert "expires 30d" in media_block or "expires 30 day" in media_block


class TestHTTPtoHTTPSRedirect:
    """Validación del redirect HTTP → HTTPS."""

    def test_http_server_block_exists(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        servers = content.split("server {")
        assert len(servers) >= 2, "Se necesitan al menos 2 server blocks"
        http_server = servers[1].split("}")[0] if len(servers) > 1 else ""
        assert "listen 80" in http_server or "listen [::]:80" in http_server

    def test_acme_challenge_location(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "/.well-known/acme-challenge/" in content
        assert "root /var/www/certbot" in content

    def test_http_returns_301_redirect(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        servers = content.split("server {")
        http_server = None
        for srv in servers[1:]:
            if "listen 80" in srv or "listen [::]:80" in srv:
                http_server = srv
                break
        assert http_server is not None, "No se encontró server block en puerto 80"
        assert "return 301 https://$server_name$request_uri" in http_server


class TestDockerComposeIntegration:
    """Validación de servicios y volúmenes en docker-compose."""

    def _get_service_block(self, compose: str, service: str) -> str:
        """Extrae el bloque YAML de un servicio (desde 'service:' hasta el siguiente servicio top-level)."""
        lines = compose.splitlines()
        start_idx = None
        base_indent = None
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            if stripped == f"{service}:":
                start_idx = i
                base_indent = indent
                break
        if start_idx is None:
            return ""
        end_idx = len(lines)
        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            stripped = line.lstrip()
            if stripped == "":
                continue
            # Nueva clave top-level (indent <= base_indent y termina en :)
            if len(line) - len(stripped) <= base_indent and stripped.endswith(":"):
                end_idx = i
                break
        return "\\n".join(lines[start_idx:end_idx])

    def test_nginx_service_defined(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "nginx:" in compose, "Servicio nginx no definido"

    def test_nginx_ports_exposed(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        nginx_section = self._get_service_block(compose, "nginx")
        assert '"80:80"' in nginx_section or "'80:80'" in nginx_section
        assert '"443:443"' in nginx_section or "'443:443'" in nginx_section

    def test_certbot_service_defined(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "certbot:" in compose, "Servicio certbot no definido"

    def test_certbot_renew_command(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "certbot renew" in compose, "Comando certbot renew no encontrado"
        assert "sleep 12h" in compose, "Renew cada 12h no configurado"

    def test_nginx_uses_static_volume_readonly(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        nginx_section = self._get_service_block(compose, "nginx")
        assert "static:/app/static:ro" in nginx_section

    def test_nginx_uses_media_volume_readonly(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        nginx_section = self._get_service_block(compose, "nginx")
        assert "media:/app/media:ro" in nginx_section

    def test_nginx_uses_certbot_volumes_readonly(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        nginx_section = self._get_service_block(compose, "nginx")
        assert "certbot_conf:/etc/letsencrypt:ro" in nginx_section
        assert "certbot_data:/var/lib/letsencrypt:ro" in nginx_section

    def test_nginx_depends_on_web(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        nginx_section = self._get_service_block(compose, "nginx")
        assert "depends_on:" in nginx_section
        assert "web:" in nginx_section

    def test_nginx_depends_on_certbot(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        nginx_section = self._get_service_block(compose, "nginx")
        # certbot puede estar como condición o simple (está en depends_on)
        assert "certbot:" in nginx_section or "certbot:" in nginx_section


class TestCertbotVolumes:
    """Validación de volúmenes persistentes Certbot."""

    def test_certbot_conf_volume_defined(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "certbot_conf:" in compose, "Volumen certbot_conf no encontrado"

    def test_certbot_data_volume_defined(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "certbot_data:" in compose, "Volumen certbot_data no encontrado"

    def test_certbot_mounts_conf_volume(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "certbot_conf:/etc/letsencrypt" in compose

    def test_certbot_mounts_data_volume(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "certbot_data:/var/lib/letsencrypt" in compose

    def test_certbot_mounts_webroot(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        # Aceptar ambas formas (relativa o con ./)
        assert ("nginx/certbot/www:/var/www/certbot" in compose or
                "./nginx/certbot/www:/var/www/certbot" in compose)


class TestEnvironmentVariables:
    """Validación de variables de entorno SSL."""

    def test_env_prod_has_domain(self):
        env = (BASE / ".env.prod.example").read_text()
        assert "DOMAIN=" in env, "DOMAIN no definida en .env.prod.example"

    def test_env_prod_has_ssl_email(self):
        env = (BASE / ".env.prod.example").read_text()
        assert "SSL_EMAIL=" in env, "SSL_EMAIL no definida en .env.prod.example"

    def test_env_prod_domain_not_placeholder(self):
        env = (BASE / ".env.prod.example").read_text()
        domain_line = [l for l in env.splitlines() if l.startswith("DOMAIN=")][0]
        value = domain_line.split("=", 1)[1].strip()
        assert value != "", "DOMAIN no debe estar vacía"

    def test_env_prod_ssl_email_valid_format(self):
        env = (BASE / ".env.prod.example").read_text()
        email_line = [l for l in env.splitlines() if l.startswith("SSL_EMAIL=")][0]
        value = email_line.split("=", 1)[1].strip()
        assert "@" in value and "." in value, "SSL_EMAIL debe ser email válido"


class TestGzipCompression:
    """Validación de compresión gzip."""

    def test_gzip_enabled(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        # gzip on; puede tener espacios variables. Buscamos la línea que contenga 'gzip' y 'on'
        gzip_lines = [ln for ln in content.splitlines() if 'gzip' in ln.lower() and 'on' in ln]
        assert len(gzip_lines) > 0, "gzip no habilitado (buscar 'gzip on' en nginx.conf)"

    def test_gzip_types_include_common_assets(self):
        content = (BASE / "nginx" / "nginx.conf").read_text()
        assert "text/css" in content and "application/javascript" in content
