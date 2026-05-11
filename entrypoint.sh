#!/bin/bash
# ERP Nexus — Production Entrypoint
# Ejecuta migraciones, collectstatic y arranca Gunicorn

set -e  # exit on error

echo "========================================="
echo "🚀 ERP Nexus Production Container"
echo "========================================="

# Esperar a que la base de datos esté disponible (timeout 60s)
echo "⏳ Waiting for database..."
timeout=60
counter=0
while ! python -c "import sys; from django.db import connection; sys.exit(0 if connection.ensure_connection() else 1)" 2>/dev/null; do
    counter=$((counter + 1))
    if [ $counter -ge $timeout ]; then
        echo "❌ Timeout waiting for database"
        exit 1
    fi
    echo "   . ($counter/$timeout)"
    sleep 1
done
echo "✅ Database is ready"

# Ejecutar migraciones
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Collect static files (una sola vez en producción)
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Crear directorio de logs si no existe
mkdir -p /app/logs

echo "✅ Starting Gunicorn..."
echo "========================================="

# Arrancar Gunicorn con argumentos pasados al script
exec gunicorn erp_nexus.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${WEB_WORKERS:-4}" \
    --timeout "${WEB_TIMEOUT:-120}" \
    --log-level "${WEB_LOG_LEVEL:-info}" \
    --access-logfile /app/logs/access.log \
    --error-logfile /app/logs/error.log \
    "$@"
