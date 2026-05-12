#!/usr/bin/env bash
# ERP Nexus — Database Backup & Restore Script
# Uso:
#   ./scripts/backup.sh              # Crear backup
#   ./scripts/backup.sh --restore <file>  # Restaurar backup
#   ./scripts/backup.sh --list             # Listar backups

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backup}"
PG_CONTAINER="erp_nexus_db"
DATE_NOW="$(date +%Y%m%d_%H%M%S)"
BACKUP_PREFIX="erp_nexus_prod_${DATE_NOW}"

mkdir -p "$BACKUP_DIR"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ─── Cargar variables de entorno ─────────────────────────────────────────────
if [[ -f "$PROJECT_ROOT/.env.prod" ]]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env.prod" | grep '=' | cut -d= -f1)
else
    warn ".env.prod no encontrado, usando valores por defecto"
fi

DB_NAME="${POSTGRES_DB:-erp_nexus}"
DB_USER="${POSTGRES_USER:-erp}"

# ─── Comando: backup ─────────────────────────────────────────────────────────
cmd_backup() {
    info "Iniciando backup de base de datos..."
    info "  Base de datos: $DB_NAME"
    info "  Usuario: $DB_USER"
    info "  Contenedor: $PG_CONTAINER"
    info "  Directorio: $BACKUP_DIR"

    # Verificar contenedor corriendo
    if ! docker ps --filter "name=$PG_CONTAINER" --filter "status=running" | grep -q "$PG_CONTAINER"; then
        error "Contenedor $PG_CONTAINER no está corriendo. Iniciar stack primero."
        exit 1
    fi

    # Archivo backup
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_PREFIX}.sql.gz"
    info "Creando backup: $BACKUP_FILE"

    # Ejecutar pg_dump dentro del contenedor
    docker exec "$PG_CONTAINER" bash -c \
        "PGPASSWORD='${POSTGRES_PASSWORD}' pg_dump -U '${DB_USER}' -d '${DB_NAME}' --format=plain --no-owner --no-acl" \
        2>/dev/null | gzip > "$BACKUP_FILE"

    if [[ $? -eq 0 ]]; then
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        info "✅ Backup completado: $BACKUP_FILE (${SIZE})"
    else
        error "❌ Falló el backup"
        exit 1
    fi
}

# ─── Comando: restore ─────────────────────────────────────────────────────────
cmd_restore() {
    local BACKUP_FILE="$1"

    if [[ ! -f "$BACKUP_FILE" ]]; then
        error "Archivo no encontrado: $BACKUP_FILE"
        exit 1
    fi

    warn "⚠️  RESTAURAR BASE DE DATOS BORRARÁ TODOS LOS DATOS ACTUALES"
    read -p "¿Estás SEGURO? (escribe 'RESTORE' para confirmar): " CONFIRM
    if [[ "$CONFIRM" != "RESTORE" ]]; then
        echo "❌ Restore cancelado."
        exit 0
    fi

    info "Iniciando restore desde: $BACKUP_FILE"
    info "Deteniendo servicios que usan DB (worker, beat, web)..."
    docker-compose -f "$PROJECT_ROOT/docker-compose.prod.yml" stop worker beat web || true

    info "Restaurando base de datos..."
    gunzip -c "$BACKUP_FILE" | docker exec -i "$PG_CONTAINER" bash -c \
        "PSQL_PASSWORD='${POSTGRES_PASSWORD}' psql -U '${DB_USER}' -d '${DB_NAME}'" 2>/dev/null

    if [[ $? -eq 0 ]]; then
        info "✅ Restore completado"
    else
        error "❌ Falló el restore"
        exit 1
    fi

    info "Reiniciando servicios..."
    docker-compose -f "$PROJECT_ROOT/docker-compose.prod.yml" up -d web worker beat

    info "Verificando健康 de Django..."
    sleep 5
    if curl -sf "http://localhost:8000/health/" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Django健康检查 OK${NC}"
    else
        warn "⚠️  Django no responde en /health/ — revisar logs"
    fi
}

# ─── Comando: list ────────────────────────────────────────────────────────────
cmd_list() {
    echo "📁 Backups disponibles en $BACKUP_DIR:"
    echo ""
    if [[ -d "$BACKUP_DIR" ]]; then
        ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null | awk '{print $9, "(" $5 ")"}' | sort || echo "   (ningún backup encontrado)"
    else
        warn "Directorio de backups no existe: $BACKUP_DIR"
    fi
}

# ─── Main ─────────────────────────────────────────────────────────────────────
case "${1:-backup}" in
    backup)
        cmd_backup
        ;;
    restore)
        if [[ -z "${2:-}" ]]; then
            error "Uso: $0 restore <archivo-backup.sql.gz>"
            exit 1
        fi
        cmd_restore "$2"
        ;;
    list|--list|-l)
        cmd_list
        ;;
    --help|-h)
        cat << EOF
Uso: $0 [comando] [opciones]

Comandos:
  backup              Crear backup de la base de datos (por defecto)
  restore <archivo>   Restaurar backup desde archivo .sql.gz
  list                Listar backups disponibles
  --help, -h          Mostrar esta ayuda

Variables de entorno (desde .env.prod):
  POSTGRES_DB         Nombre de la base de datos (default: erp_nexus)
  POSTGRES_USER       Usuario PostgreSQL (default: erp)
  POSTGRES_PASSWORD   Contraseña (requerida)
  BACKUP_DIR          Directorio de backups (default: ./backup)

Ejemplos:
  $0 backup
  $0 restore backup/erp_nexus_prod_20250512_010101.sql.gz
  $0 list
EOF
        ;;
    *)
        error "Comando desconocido: $1"
        echo "Uso: $0 [backup|restore|list]"
        exit 1
        ;;
esac
