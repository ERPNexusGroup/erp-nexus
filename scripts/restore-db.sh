#!/bin/bash
# ERP Nexus — Restore Database from Backup

set -e

BACKUP_DIR="/backup"
USAGE="Uso: $0 <backup-file|latest>\nEjemplos:\n  $0 daily/erp_nexus_20260511_120000.sql.gz\n  $0 latest  # restaura el backup más reciente"

if [ -z "$1" ]; then
    echo -e "$USAGE"
    exit 1
fi

RESTORE_FILE=""

if [ "$1" = "latest" ]; then
    # Buscar backup más reciente
    LATEST_DAILY=$(ls -t "$BACKUP_DIR/daily/"*.sql.gz 2>/dev/null | head -1)
    LATEST_WEEKLY=$(ls -t "$BACKUP_DIR/weekly/"*.sql.gz 2>/dev/null | head -1)

    if [ -n "$LATEST_DAILY" ]; then
        RESTORE_FILE="$LATEST_DAILY"
    elif [ -n "$LATEST_WEEKLY" ]; then
        RESTORE_FILE="$LATEST_WEEKLY"
    else
        echo "❌ No se encontró ningún backup en $BACKUP_DIR"
        exit 1
    fi
else
    RESTORE_FILE="$1"
fi

# Verificar que existe
if [ ! -f "$RESTORE_FILE" ]; then
    # Intentar como ruta relativa dentro del volumen backup
    if [ -f "$BACKUP_DIR/$RESTORE_FILE" ]; then
        RESTORE_FILE="$BACKUP_DIR/$RESTORE_FILE"
    else
        echo "❌ Archivo no encontrado: $RESTORE_FILE"
        exit 1
    fi
fi

echo "========================================="
echo "♻️  ERP Nexus — Restore Database"
echo "========================================="
echo "Backup: $RESTORE_FILE"
echo ""

# Confirmación
read -p "⚠️  Esto sobrescribirá la base de datos actual. Continuar? (s/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Restore cancelado"
    exit 1
fi

# Parar contenedor web (opcional — evita writes durante restore)
echo "⏸️  Deteniendo contenedor web..."
docker compose stop web || true

# Drop y recreate database (más limpio que restore directo)
echo "🗑️  Eliminando base de datos actual..."
docker compose exec -T db dropdb -U "${POSTGRES_USER:-erp}" "${POSTGRES_DB:-erp_nexus}" || true
echo "✅ Base de datos eliminada"

echo "🔧 Creando nueva base de datos..."
docker compose exec -T db createdb -U "${POSTGRES_USER:-erp}" "${POSTGRES_DB:-erp_nexus}" || true
echo "✅ Base de datos creada"

# Restore desde backup
echo "📦 Restaurando desde backup..."
gunzip -c "$RESTORE_FILE" | docker compose exec -T db psql -U "${POSTGRES_USER:-erp}" "${POSTGRES_DB:-erp_nexus}"
echo "✅ Restore completado"

# Re-arrancar web
echo "🚀 Iniciando contenedor web..."
docker compose start web || true

echo "========================================="
echo "✅ Restore finalizado exitosamente"
echo "========================================="
