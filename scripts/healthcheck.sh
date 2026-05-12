#!/usr/bin/env bash
# ERP Nexus — Stack Healthcheck
# Verifica el estado de todos los servicios del stack de producción.
# Uso: ./scripts/healthcheck.sh [--verbose]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE}[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

VERBOSE="${1:---quiet}"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ok()    { echo -e "${GREEN}✅${NC} $*"; }
fail()  { echo -e "${RED}❌${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠️${NC} $*"; }
info()  { echo -e "${BLUE}ℹ️${NC} $*"; }

FAILED=0
TOTAL=0

check() {
    ((TOTAL++))
    local description="$1"
    local condition="$2"
    local warning_msg="${3:-}"

    if eval "$condition" >/dev/null 2>&1; then
        ok "$description"
    else
        ((FAILED++))
        if [[ -n "$warning_msg" ]]; then
            fail "$description — $warning_msg"
        else
            fail "$description"
        fi
    fi
}

info_cmd() {
    if [[ "$VERBOSE" == "--verbose" ]]; then
        echo "   ↳ $*"
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ERP Nexus — Stack Healthcheck"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ─── Docker Compose ────────────────────────────────────────────────────────────
info "Verificando Docker Compose..."

check "docker-compose.yml existe" \
    "test -f docker-compose.prod.yml"

check "Servicios definidos en compose" \
    "docker-compose -f docker-compose.prod.yml config --services 2>/dev/null | grep -q ."

# ─── Contenedores corriendo ────────────────────────────────────────────────────
info "Contenedores en ejecución:"
CONTAINERS=("db" "redis" "web" "worker" "beat" "nginx" "prometheus" "grafana" "cadvisor" "node-exporter" "alertmanager")

for c in "${CONTAINERS[@]}"; do
    check "  $c" \
        "docker-compose -f docker-compose.prod.yml ps -q $c 2>/dev/null | xargs -r docker inspect -f '{{.State.Running}}' 2>/dev/null | grep -q true" \
        "contenedor no existe o no está corriendo"
done

# ─── Healthchecks Docker ───────────────────────────────────────────────────────
info "Healthchecks de servicios:"
check "DB (PostgreSQL) healthy" \
    "docker-compose -f docker-compose.prod.yml ps db | grep -q 'healthy'" \
    "verificar logs: docker-compose logs db"

check "Redis healthy" \
    "docker-compose -f docker-compose.prod.yml ps redis | grep -qi 'healthy'" \
    "verificar logs: docker-compose logs redis"

check "Web (Gunicorn) healthy" \
    "docker-compose -f docker-compose.prod.yml ps web | grep -qi 'healthy'" \
    "verificar logs: docker-compose logs web"

# ─── HTTP Endpoints ────────────────────────────────────────────────────────────
info "HTTP endpoints:"

check "Django /health/ respondiendo" \
    "curl -sf http://localhost:8000/health/ >/dev/null 2>&1" \
    "web puede estar caído o puerto no expuesto"

check "Prometheus metrics endpoint" \
    "curl -sf http://localhost:9090/metrics >/dev/null 2>&1" \
    "Prometheus no responde en 9090"

check "Grafana accesible" \
    "curl -sf http://localhost:3000/api/health >/dev/null 2>&1" \
    "Grafana caído o puerto bloqueado"

check "cAdvisor metrics" \
    "curl -sf http://localhost:8080/metrics >/dev/null 2>&1" \
    "cAdvisor no expone métricas"

check "Node Exporter metrics" \
    "curl -sf http://localhost:9100/metrics >/dev/null 2>&1" \
    "Node Exporter caído"

check "AlertManager UI" \
    "curl -sf http://localhost:9093 >/dev/null 2>&1" \
    "AlertManager no responde"

# ─── SSL Certificate (si Nginx SSL habilitado) ─────────────────────────────────
if curl -skf "https://localhost/health/" >/dev/null 2>&1; then
    info "SSL/TLS:"
    check "  HTTPS endpoint responde" \
        "curl -skf https://localhost/health/ >/dev/null 2>&1"

    # Verificar certificado
    CERT_EXPIRY=$(echo | openssl s_client -connect localhost:443 -servername localhost 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
    if [[ -n "$CERT_EXPIRY" ]]; then
        CERT_EPOCH=$(date -d "$CERT_EXPIRY" +%s 2>/dev/null || echo 0)
        NOW_EPOCH=$(date +%s)
        DAYS_LEFT=$(( (CERT_EPOCH - NOW_EPOCH) / 86400 ))
        if [[ $DAYS_LEFT -gt 0 ]]; then
            ok "  Certificado SSL válido (expira en $DAYS_LEFT días)"
        else
            fail "  Certificado SSL expirado o expira pronto"
        fi
    fi
else
    info "SSL/TLS: no configurado o no detectable en localhost"
fi

# ─── Bases de datos conectables ───────────────────────────────────────────────
info "Conectividad a bases de datos:"

check "PostgreSQL acepta conexiones" \
    "PGPASSWORD='${POSTGRES_PASSWORD:?}' psql -h localhost -p 5432 -U '${POSTGRES_USER:-erp}' -d '${POSTGRES_DB:-erp_nexus}' -c 'SELECT 1' >/dev/null 2>&1" \
    "verificar NETWORK en docker-compose o firewall"

check "Redis responde a PING" \
    "redis-cli -h localhost -p 6379 -a '${REDIS_PASSWORD:?}' PING | grep -q PONG" \
    "verificar password o conexión"

# ─── Logs de errores recientes ─────────────────────────────────────────────────
info "Revisión rápida de logs (últimas 10 líneas de errores):"

ERRORS_WEB=$(docker-compose -f docker-compose.prod.yml logs web --tail=1000 2>/dev/null | grep -i "error\|exception\|traceback" | tail -5 || true)
if [[ -n "$ERRORS_WEB" ]]; then
    warn "  Web tiene errores recientes:"
    echo "$ERRORS_WEB" | sed 's/^/    /'
else
    ok "  Web sin errores recientes"
fi

ERRORS_DB=$(docker-compose -f docker-compose.prod.yml logs db --tail=500 2>/dev/null | grep -i "error\|fatal\|panic" | tail -3 || true)
if [[ -n "$ERRORS_DB" ]]; then
    warn "  DB tiene errores recientes:"
    echo "$ERRORS_DB" | sed 's/^/    /'
else
    ok "  DB sin errores recientes"
fi

# ─── Disco y memoria ───────────────────────────────────────────────────────────
info "Recursos del host:"

DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [[ "$DISK_USAGE" -lt 85 ]]; then
    ok "  Disco: ${DISK_USAGE}% usado"
else
    fail "  Disco: ${DISK_USAGE}% usado (>=85% crítico)"
fi

MEM_AVAILABLE=$(awk '/MemAvailable/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)
MEM_TOTAL=$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo 1)
MEM_PCT=$(( (MEM_TOTAL - MEM_AVAILABLE) * 100 / MEM_TOTAL ))
if [[ $MEM_PCT -lt 90 ]]; then
    ok "  Memoria: ${MEM_PCT}% usado"
else
    fail "  Memoria: ${MEM_PCT}% usado (>=90% crítico)"
fi

# ─── Resumen ───────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}✅ TODOS LOS SERVICIOS SALUDABLES (${TOTAL}/${TOTAL})${NC}"
    echo ""
    info "Stack listo para producción."
    exit 0
else
    echo -e "${RED}❌ FALLARON $FAILED DE $TOTAL CHEQUEOS${NC}"
    echo ""
    warn "Revise los servicios marcados con ❌ y consulte:"
    echo "  - Logs:        docker-compose -f docker-compose.prod.yml logs -f [servicio]"
    echo "  - Reiniciar:  docker-compose -f docker-compose.prod.yml restart [servicio]"
    echo "  - Escalar:     docker-compose -f docker-compose.prod.yml up -d --scale web=2"
    echo "  - Runbooks:   docs/ALERTING_RULES.md"
    exit 1
fi
