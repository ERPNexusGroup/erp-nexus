#!/bin/bash
# ============================================
# INSTALADOR AUTOMÁTICO - Módulo facturacion_ec
# ERP Nexus Group
# ============================================

set -e  # Salir en primer error

echo "=========================================="
echo "  ERP Nexus - Instalador facturacion_ec"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Verificar entorno
echo "📋 verificando entorno..."
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ ERROR: Ejecutar desde directorio raíz erp-nexus${NC}"
    exit 1
fi

if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}⚠️  Instalando uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.cargo/env"
fi

# 2. Dependencias Python
echo "📦 Instalando dependencias Python..."
uv sync

# Instalar librerías facturación
echo "  - jinja2, lxml, signxml, httpx, cryptography"
uv pip install jinja2 lxml signxml httpx cryptography 2>/dev/null || true

# 3. Migraciones core modules (si no existen)
echo "🗄️  Aplicando migraciones core..."
uv run python manage.py makemigrations core_currency core_chart_of_accounts core_fiscal_year core_config 2>/dev/null || true
uv run python manage.py migrate

# 4. Registrar módulo en catálogo
echo "📝 Registrando módulo en marketplace..."
uv run python manage.py register_facturacion_ec

# 5. Migraciones módulo facturacion_ec
echo "📄 Generando migraciones facturacion_ec..."
if [ -d "modules/facturacion_ec" ]; then
    uv run python manage.py makemigrations facturacion_ec
    echo "✅ Migraciones generadas"

    uv run python manage.py migrate
    echo "✅ Migraciones aplicadas"
else
    echo -e "${RED}❌ Módulo facturacion_ec no encontrado en modules/${NC}"
    exit 1
fi

# 6. Crear superusuario si no existe
echo "👤 Verificando superusuario..."
uv run python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@erpnexus.ec', 'admin1234')
    print('✅ Superusuario creado: admin / admin1234')
else:
    print('✅ Superusuario ya existe')
"

# 7. Seed de planes de licencia
echo "💰 Configurando planes de licencia..."
uv run python manage.py shell -c "
from modules.facturacion_ec.models import LicenseType
planes = [
    ('free', 'Free (10 facturas/mes)', 'Plan gratuito para pruebas', 0, 10, False, False),
    ('monthly_10', 'Plan Mensual \$10/mes', 'Facturas ilimitadas, actualizaciones', 10.0, 0, True, True),
    ('yearly_100', 'Plan Anual \$100/año', 'Facturas ilimitadas, prioridad', 100/12, 0, True, True),
    ('lifetime_3500', 'Lifetime + Updates \$3,500', 'Pago único, acceso completo', 3500, 0, True, True),
    ('lifetime_750', 'Lifetime (sin updates) \$750', 'Pago único, solo fixes', 750, 0, False, False),
]
for p in planes:
    LicenseType.objects.get_or_create(
        plan_id=p[0],
        defaults={
            'display_name': p[1],
            'description': p[2],
            'price_monthly_equivalent': p[3],
            'max_invoices_per_month': p[4],
            'allows_updates': p[5],
            'priority_support': p[6],
        }
    )
print('✅ Planes de licencia configurados (5 planes)')
"

# 8. Información final
echo ""
echo "=========================================="
echo -e "${GREEN}✅ INSTALACIÓN COMPLETADA${NC}"
echo "=========================================="
echo ""
echo "🌐 Acceso admin:"
echo "   URL:  http://localhost:8000/admin"
echo "   User: admin"
echo "   Pass: admin1234"
echo ""
echo "📦 Módulo facturacion_ec instalado:"
echo "   - Models: 10 (Customer, Product, Invoice, etc.)"
echo "   - Admin integrado"
echo "   - API REST en /api/facturacion/"
echo "   - 5 planes de licencia configurados"
echo ""
echo "🚀 Próximos pasos:"
echo "   1. Configurar certificado SRI en settings.py"
echo "   2. Crear Company en admin"
echo "   3. Probar factura de prueba"
echo ""
echo "📖 Documentación: modules/facturacion_ec/README.md"
echo ""
