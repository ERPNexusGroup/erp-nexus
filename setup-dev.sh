#!/bin/bash
# ============================================
# Quick Setup Script — ERP Nexus
# ============================================
# Ejecutar: source setup-dev.sh  (o bash setup-dev.sh)

set -e  # Salir en primer error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "   ERP Nexus — Setup Development"
echo "=========================================="
echo ""

# 1. Verificar Python
echo -e "${YELLOW}→ Verificando Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 no encontrado. Instálalo primero.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $(python3 --version)${NC}"

# 2. Instalar uv si no existe
echo -e "${YELLOW}→ Verificando uv (package manager)...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}  Instalando uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Agregar al PATH para esta sesión
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo -e "${GREEN}✓ uv $(uv --version)${NC}"
fi

# 3. Crear venv e instalar deps
echo -e "${YELLOW}→ Instalando dependencias...${NC}"
uv sync
echo -e "${GREEN}✓ Dependencias instaladas${NC}"

# 4. Configurar .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}→ Creando .env desde .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env creado${NC}"
fi

# 5. Database setup
echo -e "${YELLOW}→ Configurando base de datos...${NC}"
if [ "$DATABASE_URL" = "sqlite:///./db.sqlite3" ]; then
    echo "  Usando SQLite (default)"
else
    echo "  Usando PostgreSQL: $DATABASE_URL"
    # Esperar a que PostgreSQL esté listo
    echo "  Esperando PostgreSQL..."
    sleep 3
fi

uv run python manage.py migrate --noinput
echo -e "${GREEN}✓ Migraciones aplicadas${NC}"

# 6. Bootstrap superadmin
echo -e "${YELLOW}→ Creando superusuario...${NC}"
if ! uv run python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists()" | grep -q "True"; then
    uv run python manage.py bootstrap_superadmin \
        --username admin \
        --email admin@local \
        --password admin123
    echo -e "${GREEN}✓ Superusuario creado${NC}"
else
    echo -e "${GREEN}✓ Superusuario ya existe${NC}"
fi

# 7. Cargar datos iniciales (catálogos)
echo -e "${YELLOW}→ Cargando datos iniciales...${NC}"
uv run python manage.py bootstrap_data --noinput || true
echo -e "${GREEN}✓ Datos iniciales cargados${NC}"

# 8. Instalar módulo de ejemplo (facturacion_ec si existe)
if [ -d "modules/facturacion_ec" ]; then
    echo -e "${YELLOW}→ Instalando módulo facturacion_ec...${NC}"
    uv run python manage.py install_module ./modules/facturacion_ec
    echo -e "${GREEN}✓ Módulo facturacion_ec instalado${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "   ✅ Setup completado!"
echo "==========================================${NC}"
echo ""
echo "🚀 Para iniciar el servidor:"
echo "   uv run python manage.py runserver"
echo ""
echo "📍 Luego abre: http://localhost:8000/admin"
echo "   Usuario: admin"
echo "   Password: admin123"
echo ""
echo "📚 Documentación API: http://localhost:8000/api/v1/docs/"
echo ""
