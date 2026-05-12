#!/bin/bash
# ERP Nexus — Redis Maintenance & Diagnostics

set -e

echo "========================================="
echo "🔧 ERP Nexus — Redis Maintenance"
echo "========================================="
echo ""

# 1. Info básica
echo "📊 Redis Info:"
docker compose exec -T redis redis-cli -a "${REDIS_PASSWORD:-}" info stats | head -20
echo ""

# 2. Memory usage
echo "💾 Memory usage:"
docker compose exec -T redis redis-cli -a "${REDIS_PASSWORD:-}" info memory | grep -E "used_memory_human|maxmemory|maxmemory_policy"
echo ""

# 3. Keyspace
echo "🔑 Keyspace (DB count):"
docker compose exec -T redis redis-cli -a "${REDIS_PASSWORD:-}" info keyspace
echo ""

# 4. Slow log (últimas 10 operaciones lentas)
echo "🐌 Slow log (top 10):"
docker compose exec -T redis redis-cli -a "${REDIS_PASSWORD:-}" slowlog get 10
echo ""

# 5. Check persistence
echo "💿 Persistence:"
docker compose exec -T redis redis-cli -a "${REDIS_PASSWORD:-}" info persistence | grep -E "aof_enabled|aof_rewrite_in_progress|aof_last_bgrewrite_status"
echo ""

echo "========================================="
echo "✅ Redis maintenance completado"
echo "========================================="
