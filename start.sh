#!/bin/bash
# Quick start — ERP Nexus con facturacion_ec

cd "$(dirname "$0")"

echo "🚀 Iniciando ERP Nexus..."
echo ""

# Verificar venv
if [ ! -d ".venv" ]; then
    echo "📦 Instalando dependencias..."
    uv sync
fi

# Aplicar migraciones (si hay cambios)
echo "🗄️  Actualizando base de datos..."
uv run python manage.py migrate --noinput

# Iniciar server
echo ""
echo "🌐 ERP Nexus corriendo en:"
echo "   http://localhost:8000/admin"
echo "   Usuario: admin"
echo "   Contraseña: admin1234"
echo ""
echo "📦 Módulos activos:"
echo "   - Core: 11 apps (auth, companies, currency, chart_of_accounts...)"
echo "   - facturacion_ec: Facturación Electrónica Ecuador"
echo ""
uv run python manage.py runserver
