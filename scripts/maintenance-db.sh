#!/bin/bash
# ERP Nexus — Database Maintenance
# Ejecuta VACUUM, ANALYZE, y reporta estadísticas

set -e

echo "========================================="
echo "🔧 ERP Nexus — Database Maintenance"
echo "========================================="
echo ""

# 1. Vacuum (FULL opcional, por defecto solo VERBOSE)
echo "📊 Running VACUUM ANALYZE..."
docker compose exec -T db vacuumdb -U "${POSTGRES_USER:-erp}" "${POSTGRES_DB:-erp_nexus}" --verbose --analyze
echo "✅ VACUUM ANALYZE completado"
echo ""

# 2. Mostrar estadísticas de actividad
echo "📈 Active connections:"
docker compose exec -T db psql -U "${POSTGRES_USER:-erp}" -d "${POSTGRES_DB:-erp_nexus}" -c \
  "SELECT count(*) as connections, state FROM pg_stat_activity GROUP BY state ORDER BY connections DESC;"
echo ""

# 3. Tamaño de base de datos
echo "💾 Database size:"
docker compose exec -T db psql -U "${POSTGRES_USER:-erp}" -d "${POSTGRES_DB:-erp_nexus}" -c \
  "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB:-erp_nexus}')) as size;"
echo ""

# 4. Top 10 queries más lentas (si pg_stat_statements está instalado)
echo "🐌 Top 10 slow queries (pg_stat_statements):"
docker compose exec -T db psql -U "${POSTGRES_USER:-erp}" -d "${POSTGRES_DB:-erp_nexus}" -c \
  "SELECT query, calls, total_time, rows, mean_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;" \
  2>/dev/null || echo "   (pg_stat_statements no disponible)"
echo ""

# 5. Cache hit ratio
echo "🎯 Cache hit ratio:"
docker compose exec -T db psql -U "${POSTGRES_USER:-erp}" -d "${POSTGRES_DB:-erp_nexus}" -c \
  "SELECT round(100.0 * sum(blks_hit) / nullif(sum(blks_hit + blks_read), 0), 2) as cache_hit_ratio FROM pg_stat_database WHERE datname = '${POSTGRES_DB:-erp_nexus}';"
echo ""

echo "========================================="
echo "✅ Maintenance completado"
echo "========================================="
