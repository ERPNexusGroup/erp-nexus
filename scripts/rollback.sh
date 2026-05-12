#!/usr/bin/env bash
# ERP Nexus — Emergency Rollback Script
# Revierte a un commit anterior en caso de deployment fallido.
# Uso: ./scripts/rollback.sh [commit-hash|tag]
#   Sin argumento: revierte al último commit estable en main

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ERP Nexus — Emergency Rollback"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─── Determinar commit destino ───────────────────────────────────────────────
if [[ $# -eq 1 ]]; then
    TARGET_COMMIT="$1"
    echo "🎯 Rollback a commit específico: $TARGET_COMMIT"
else
    # Buscar último commit "estable" (que no sea el actual HEAD)
    TARGET_COMMIT=$(git log --oneline -10 | grep -v "^$(git rev-parse --short HEAD)" | head -1 | cut -d' ' -f1)
    if [[ -z "$TARGET_COMMIT" ]]; then
        echo "❌ No hay commits anteriores para rollback."
        exit 1
    fi
    echo "🎯 Rollback al último commit estable: $TARGET_COMMIT"
fi

# Verificar que existe
if ! git cat-file -e "${TARGET_COMMIT}^{commit}" 2>/dev/null; then
    echo "❌ Commit $TARGET_COMMIT no existe."
    exit 1
fi

# ─── Confirmación (requiere flag --force para no accidental) ─────────────────
if [[ "${FORCE:-false}" != "true" ]]; then
    echo ""
    echo "⚠️  ADVERTENCIA: Esto detendrá todos los contenedores y revertirá código."
    echo "   Commit actual: $(git rev-parse --short HEAD)"
    echo "   Commit destino: $TARGET_COMMIT"
    echo ""
    read -p "¿Estás SEGURO? (escribe 'YES' para confirmar): " CONFIRM
    if [[ "$CONFIRM" != "YES" ]]; then
        echo "❌ Rollback cancelado."
        exit 0
    fi
fi

# ─── 1. Detener stack actual ────────────────────────────────────────────────
echo "🛑 Deteniendo stack actual..."
docker-compose -f docker-compose.prod.yml down --remove-orphans || true

# ─── 2. Revertir código a commit anterior ───────────────────────────────────
echo "↩️  Revirtiendo código a $TARGET_COMMIT..."
git reset --hard "$TARGET_COMMIT"
git clean -fd

# ─── 3. Rebuild de imágenes (por si cambió Dockerfile) ──────────────────────
echo "🔨 Rebuilding Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# ─── 4. Aplicar migraciones de DB (si es un commit anterior a la migración actual) ─
echo "🗄️  Aplicando migraciones de DB (revisión)..."
# Nota: Si el rollback es a antes de una migración, hay que revertir migraciones también.
# Esto es delicado — se recomienda dump/restore si hay duda.
# Por seguridad, no ejecutamos migraciones automáticamente aquí.
echo "⚠️  Si el commit anterior tiene migraciones diferentes, ejecuta:"
echo "   docker-compose run --rm web python manage.py migrate"

# ─── 5. Arrancar stack rollback ──────────────────────────────────────────────
echo "🚀 Arrancando stack en estado rollback..."
docker-compose -f docker-compose.prod.yml up -d

# ─── 6. Esperar healthy ──────────────────────────────────────────────────────
echo "⏳ Esperando healthy de servicios..."
for i in {1..30}; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "healthy"; then
        echo "✅ Servicios healthy"
        break
    fi
    echo "   Esperando... ($i/30)"
    sleep 2
done

# ─── 7. Verificar健康检查 endpoint ───────────────────────────────────────────
echo "🔍 Verificando /health/ endpoint..."
if curl -sf "http://localhost:8000/health/" >/dev/null 2>&1; then
    echo "✅ Django respondiendo correctamente"
else
    echo "⚠️  Django no responde en /health/ — revisar logs"
fi

# ─── 8. Notificación ─────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Rollback completado"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Estado actual:"
git log --oneline -1
echo ""
echo "🌐 Servicios corriendo:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "📝 Logs (para verificar):"
echo "   docker-compose logs -f web"
echo "   docker-compose logs -f db"
echo ""
echo "🔔 IMPORTANTE:"
echo "   - Verificar que la DB esté consistente con el código rollbackeado"
echo "   - Si hay migraciones pendientes de revertir, ejecutar:"
echo "     docker-compose run --rm web python manage.py migrate <app> <migration_previous>"
echo "   - Revisar alerts en Slack/Email"
echo ""
