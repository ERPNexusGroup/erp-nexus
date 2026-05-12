#!/usr/bin/env bash
# ERP Nexus — First Deployment Script
# Este script configura el stack de producción por primera vez en un servidor nuevo.
# Uso: ./scripts/first-deploy.sh [environment]
#   environment: production (default) | staging

set -euo pipefail

ENVIRONMENT="${1:-production}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ERP Nexus — First Deploy (${ENVIRONMENT})"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─── 0. Validaciones previas ───────────────────────────────────────────────
if [[ ! -f "$PROJECT_ROOT/.env.${ENVIRONMENT}" ]]; then
    echo "❌ Error: No existe .env.${ENVIRONMENT}"
    echo "   Copia .env.${ENVIRONMENT}.example a .env.${ENVIRONMENT} y configura variables."
    exit 1
fi

if ! command -v docker &>/dev/null; then
    echo "❌ Docker no está instalado. Instalar: https://docs.docker.com/engine/install/"
    exit 1
fi

if ! command -v docker-compose &>/dev/null; then
    echo "❌ docker-compose no está instalado."
    exit 1
fi

# ─── 1. Variables de entorno ────────────────────────────────────────────────
export $(grep -v '^#' "$PROJECT_ROOT/.env.${ENVIRONMENT}" | grep '=' | cut -d= -f1)

echo "✅ Variables cargadas desde .env.${ENVIRONMENT}"

# ─── 2. Build de imágenes ───────────────────────────────────────────────────
echo "📦 Building Docker images..."
cd "$PROJECT_ROOT"
docker-compose -f docker-compose.${ENVIRONMENT}.yml build --no-cache

# ─── 3. Generar DH params (SSL Phase 2.4) ───────────────────────────────────
if [[ ! -f "$PROJECT_ROOT/nginx/ssl/dhparam.pem" ]]; then
    echo "🔐 Generando DH params (2048-bit)..."
    mkdir -p "$PROJECT_ROOT/nginx/ssl"
    openssl dhparam -out "$PROJECT_ROOT/nginx/ssl/dhparam.pem" 2048 2>/dev/null || true
    echo "✅ dhparam.pem generado"
else
    echo "✅ dhparam.pem ya existe"
fi

# ─── 4. Crear directorios necesarios ────────────────────────────────────────
echo "📁 Creando directorios..."
mkdir -p "$PROJECT_ROOT/nginx/certbot/www"
mkdir -p "$PROJECT_ROOT/monitoring/prometheus/alerts"
mkdir -p "$PROJECT_ROOT/monitoring/grafana/provisioning/{datasources,dashboards,config}"
mkdir -p "$PROJECT_ROOT/monitoring/grafana/dashboards"
mkdir -p "$PROJECT_ROOT/monitoring/alertmanager"

# ─── 5. Validar configuraciones ─────────────────────────────────────────────
echo "🔍 Validando configuraciones..."

# Validar nginx.conf
if command -v nginx &>/dev/null; then
    nginx -t -c "$PROJECT_ROOT/nginx/nginx.conf" 2>/dev/null || echo "⚠️  nginx -t falló (opcional, sin Docker)"
fi

# Validar docker-compose schema (si hay plugin)
docker-compose -f docker-compose.${ENVIRONMENT}.yml config >/dev/null 2>&1 && echo "✅ docker-compose.yml válido"

# Validar YAML files (prometheus, alertmanager, grafana)
if command -v python3 &>/dev/null; then
    python3 -c "import yaml; yaml.safe_load(open('$PROJECT_ROOT/monitoring/prometheus/prometheus.yml'))" && echo "✅ prometheus.yml válido"
    python3 -c "import yaml; yaml.safe_load(open('$PROJECT_ROOT/monitoring/alertmanager/alertmanager.yml'))" && echo "✅ alertmanager.yml válido"
    python3 -c "import yaml; yaml.safe_load(open('$PROJECT_ROOT/monitoring/grafana/provisioning/datasources/prometheus.yml'))" && echo "✅ grafana datasource válido"
fi

# Validar JSON dashboard
python3 -c "import json; json.load(open('$PROJECT_ROOT/monitoring/grafana/dashboards/erp_nexus.json'))" && echo "✅ Grafana dashboard JSON válido"

# ─── 6. Arrancar servicios base (DB + Redis) ─────────────────────────────────
echo "🗄️  Iniciando PostgreSQL + Redis..."
docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d db redis

echo "⏳ Esperandohealthy) de DB y Redis..."
for i in {1..30}; do
    if docker-compose -f docker-compose.${ENVIRONMENT}.yml ps | grep -q "healthy"; then
        echo "✅ DB y Redis healthy"
        break
    fi
    echo "   Esperando... ($i/30)"
    sleep 2
done

# ─── 7. Ejecutar migraciones Django ─────────────────────────────────────────
echo "🔧 Ejecutando migraciones Django..."
docker-compose -f docker-compose.${ENVIRONMENT}.yml run --rm web python manage.py migrate --noinput

# ─── 8. Crear superusuario (opcional) ───────────────────────────────────────
if [[ "${CREATE_SUPERUSER:-false}" == "true" ]]; then
    echo "👤 Creando superusuario..."
    docker-compose -f docker-compose.${ENVIRONMENT}.yml run --rm web python manage.py createsuperuser --noinput || true
fi

# ─── 9. Coleccionar estáticos ───────────────────────────────────────────────
echo "📦 Colectando archivos estáticos..."
docker-compose -f docker-compose.${ENVIRONMENT}.yml run --rm web python manage.py collectstatic --noinput

# ─── 10. Arrancar servicios de aplicación ────────────────────────────────────
echo "🚀 Iniciando Django + Celery..."
docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d web worker beat

echo "⏳ Esperando healthy de web..."
for i in {1..30}; do
    if curl -sf "http://localhost:8000/health/" >/dev/null 2>&1; then
        echo "✅ Django healthy en /health/"
        break
    fi
    echo "   Esperando health... ($i/30)"
    sleep 2
done

# ─── 11. Obtener certificado SSL (solo production) ──────────────────────────
if [[ "$ENVIRONMENT" == "production" ]]; then
    echo "🔒 Obteniendo certificado SSL (Let's Encrypt)..."
    if [[ "${SKIP_CERTBOT:-false}" != "true" ]]; then
        docker-compose -f docker-compose.${ENVIRONMENT}.yml run --rm certbot certbot certonly \
            --webroot -w /var/www/certbot \
            -d "${DOMAIN}" \
            --email "${SSL_EMAIL}" \
            --agree-tos \
            --no-eff-email \
            --force-renewal || echo "⚠️  Certbot falló (verificar DNS/dominio)"
    else
        echo "⏭️  SKIP_CERTBOT=true — saltando obtención certificado"
    fi

    echo "🔄 Reiniciando nginx para cargar certificado..."
    docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d nginx
else
    echo "⏭️  Staging — saltando SSL (usar self-signed o DNS-01 manual)"
fi

# ─── 12. Arrancar stack monitoreo ────────────────────────────────────────────
echo "📊 Iniciando stack de monitoreo..."
docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d \
    prometheus grafana cadvisor node-exporter alertmanager

echo "⏳ Esperando Prometheus healthy (targets up)..."
sleep 5

# Verificar targets
curl -s "http://localhost:9090/targets" | grep -q '"health":"up"' && echo "✅ Prometheus targets healthy" || echo "⚠️  Algunos targets pueden estar down (normal si app no expone /metrics/)"

# ─── 13. Instalar django-prometheus (requerido para métricas) ───────────────
echo "📈 Instalando django-prometheus..."
docker-compose -f docker-compose.${ENVIRONMENT}.yml run --rm web uv add django-prometheus || true

# Reiniciar web para cargar métricas
docker-compose -f docker-compose.${ENVIRONMENT}.yml restart web

# ─── 14. Summary ─────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Deploy completado (${ENVIRONMENT})"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Servicios:"
echo "   Django      → http://localhost:8000"
echo "   Grafana     → http://localhost:3000 (admin: $GRAFANA_ADMIN_PASSWORD)"
echo "   Prometheus  → http://localhost:9090"
echo "   AlertManager→ http://localhost:9093"
echo "   cAdvisor    → http://localhost:8080"
echo "   Node Export → http://localhost:9100/metrics"
echo ""
echo "📊 Next steps:"
echo "   1. Verificar DNS: dig +short $DOMAIN (debe apuntar a IP del servidor)"
echo "   2. Acceder Grafana → Dashboards → 'ERP Nexus — Production Monitoring'"
echo "   3. Verificar métricas en Prometheus: http://localhost:9090/targets"
echo "   4. Probar alertas: detener un servicio temporalmente"
echo "   5. Configurar SMTP en .env (si no lo está) para emails"
echo "   6. Configurar SLACK_WEBHOOK_URL para alertas críticas"
echo ""
echo "🛠️  Comandos útiles:"
echo "   docker-compose -f docker-compose.${ENVIRONMENT}.yml logs -f    # ver logs"
echo "   docker-compose -f docker-compose.${ENVIRONMENT}.yml restart <service>  # reiniciar"
echo "   docker-compose -f docker-compose.${ENVIRONMENT}.yml down     # detener todo"
echo ""
echo "📚 Documentación:"
echo "   docs/DEPLOYMENT.md — Guía completa"
echo "   docs/SSL_NGINX.md — SSL + Nginx"
echo "   docs/MONITORING.md — Monitoreo"
echo "   docs/ALERTING_RULES.md — Runbooks de alertas"
echo ""
echo "🔐 Recuerda cambiar:"
echo "   - GRAFANA_ADMIN_PASSWORD"
echo "   - SMTP_PASSWORD (si usas Gmail, crear App Password)"
echo "   - SLACK_WEBHOOK_URL (crear incoming-webhook en Slack)"
echo ""
