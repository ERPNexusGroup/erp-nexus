-- ERP Nexus — PostgreSQL Initial Extensions
-- Se ejecuta una sola vez al crear la base de datos por primera vez
-- (montado en /docker-entrypoint-initdb.d/ por docker-compose)

-- Extensiones de monitoreo y estadísticas
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_stat_kcache;
CREATE EXTENSION IF NOT EXISTS pg_qualstats;
CREATE EXTENSION IF NOT EXISTS pg_wait_sampling;

-- Índices útiles para queries comunes (ajustar según carga real)
-- Nota: Los índices reales se migran vía Django migrations

-- Comment extensiones
COMMENT ON EXTENSION pg_stat_statements IS 'Track execution statistics of all SQL statements';
COMMENT ON EXTENSION pg_stat_kcache IS 'Track CPU and I/O statistics of queries';
