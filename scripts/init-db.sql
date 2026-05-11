-- Inicialización PostgreSQL para ERP Nexus
-- Ejecutado automáticamente al crear el contenedor

-- Crear extensiones útiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Configuraciones de conexión
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';

-- Mostrar info
SELECT 'PostgreSQL inicializado para ERP Nexus' as status,
       version() as pg_version;
