#!/bin/bash
# ============================================
# ERP NEXUS — Setup Completo + Módulo facturacion_ec
# Autor: ERP Nexus Group
# ============================================

set -e  # Salir en primer error

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "  ERP NEXUS — Instalador Automático"
echo "=========================================="
echo ""

# 1. Verificar que estamos en el directorio correcto
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: Ejecutar desde directorio raíz de erp-nexus${NC}"
    exit 1
fi

# 2. Instalar uv si no existe
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}⚠️  Instalando uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.cargo/env"
fi

# 3. Instalar dependencias core
echo "📦 Instalando dependencias core..."
uv sync

# Dependencias adicionales facturación
echo "📦 Instalando librerías facturación (jinja2, lxml, signxml, httpx, cryptography)..."
uv pip install jinja2 lxml signxml httpx cryptography 2>/dev/null || true

# 4. Migraciones core
echo "🗄️  Aplicando migraciones core..."
uv run python manage.py migrate --noinput

# 5. Crear superusuario si no existe
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

# 6. Instalar módulo facturacion_ec
echo ""
echo "📦 Instalando módulo facturacion_ec..."
if [ -d "modules/facturacion_ec" ]; then
    uv run python manage.py module_install modules/facturacion_ec --no-input 2>/dev/null || \
    uv run python manage.py module_install modules/facturacion_ec
else
    echo -e "${RED}❌ Módulo facturacion_ec no encontrado en modules/${NC}"
    exit 1
fi

# 7. Migraciones del módulo
echo "📄 Aplicando migraciones facturacion_ec..."
uv run python manage.py makemigrations facturacion_ec
uv run python manage.py migrate facturacion_ec

# 8. Seed: planes de licencia
echo "💰 Configurando planes de licencia..."
uv run python manage.py shell -c "
from modules.facturacion_ec.models import LicenseType
planes = [
    ('free', 'Free (10 facturas/mes)', 'Plan gratuito para pruebas', 0, 10, False, False),
    ('monthly_10', 'Plan Mensual \$10/mes', 'Facturas ilimitadas, actualizaciones', 10.0, 0, True, True),
    ('yearly_100', 'Plan Anual \$100/año', 'Facturas ilimitadas, prioridad', 100/12, 0, True, True),
    ('lifetime_3500', 'Lifetime + Updates \$3,500', 'Pago único, acceso completo', 3500, 0, True, True),
    ('lifetime_750', 'Lifetime (sin updates) \$750', 'Pago único, solo bug fixes', 750, 0, False, False),
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
            'is_active': True,
        }
    )
print('✅ Planes de licencia configurados (5)')
"

# 9. Verificar módulo cargado
echo ""
echo "🔍 Verificando carga de módulo..."
uv run python manage.py shell -c "
from django.conf import settings
if 'modules.facturacion_ec' in settings.INSTALLED_APPS:
    print('✅ Módulo facturacion_ec cargado en INSTALLED_APPS')
else:
    print('❌ Módulo NO cargado')
    exit(1)
"

# 10. Resumen final
echo ""
echo "=========================================="
echo -e "${GREEN}✅ INSTALACIÓN COMPLETA${NC}"
echo "=========================================="
echo ""
echo "🌐 ERP Nexus listo:"
echo "   URL:      http://localhost:8000/admin"
echo "   Usuario:  admin"
echo "   Clave:    admin1234"
echo ""
echo "📦 Módulo facturacion_ec instalado:"
echo "   - 10 modelos (Customer, Product, Invoice, LicenseType, etc.)"
echo "   - Admin integrado"
echo "   - API REST en /api/facturacion/"
echo "   - 5 planes de licencia configurados"
echo ""
echo "🧪 Para probar:"
echo "   1. Ir a admin → Crear Company (con RUC válido)"
echo "   2. Crear Customer y Product"
echo "   3. Crear Invoice manualmente"
echo ""
echo "📖 Docs:"
echo "   - docs/INSTALL.md"
echo "   - modules/facturacion_ec/README.md"
echo "   - ERP_NEXUS_BUSINESS_PLAN.md"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
echo "   Para enviar facturas a SRI necesitas certificado digital."
echo "   Configurar en settings.py: FACTURACION_EC_CERT_PATH y FACTURACION_EC_CERT_PASSWORD"
echo ""
