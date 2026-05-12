#!/bin/bash
# ERP Nexus — Backup Automático PostgreSQL
# Retención: 7 días diarios + 4 semanas semanales (domingo)

set -e

BACKUP_DIR="/backup"
DAILY_DIR="$BACKUP_DIR/daily"
WEEKLY_DIR="$BACKUP_DIR/weekly"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="erp_nexus_${TIMESTAMP}.sql.gz"

echo "========================================="
echo "📦 ERP Nexus — Backup Database"
echo "========================================="
echo "Fecha: $(date)"
echo "Backup dir: $BACKUP_DIR"

# Crear directorios si no existen
mkdir -p "$DAILY_DIR" "$WEEKLY_DIR"

# Ejecutar dump
echo "⏳ Creando backup..."
docker compose exec -T db pg_dump -U "${POSTGRES_USER:-erp}" "${POSTGRES_DB:-erp_nexus}" | gzip > "$DAILY_DIR/$BACKUP_FILE"

BACKUP_SIZE=$(du -h "$DAILY_DIR/$BACKUP_FILE" | cut -f1)
echo "✅ Backup creado: $DAILY_DIR/$BACKUP_FILE (${BACKUP_SIZE})"

# Rotación diaria — eliminar backups > 7 días
echo "🗑️  Limpiando backups diarios antiguos (>7 días)..."
find "$DAILY_DIR" -name "*.sql.gz" -mtime +7 -delete || true
echo "   OK"

# Copia semanal cada domingo (day 0 = Sunday in some systems, 7 in others)
DAY_OF_WEEK=$(date +%u)  # 1-7 (1=Monday, 7=Sunday)
if [ "$DAY_OF_WEEK" = "7" ]; then
    WEEKLY_FILE="$WEEKLY_DIR/weekly_$(date +%Y-%U).sql.gz"
    cp "$DAILY_DIR/$BACKUP_FILE" "$WEEKLY_FILE"
    echo "📁 Copia semanal creada: $WEEKLY_FILE"

    # Rotación semanal — eliminar > 4 semanas
    echo "🗑️  Limpiando backups semanales antiguos (>4 semanas)..."
    find "$WEEKLY_DIR" -name "*.sql.gz" -mtime +28 -delete || true
    echo "   OK"
fi

echo "========================================="
echo "✅ Backup completado exitosamente"
echo "========================================="
