# Tests para scripts de mantenimiento de base de datos (backup, restore, maintenance)

import os
import stat
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parents[3]  # repo root: erp-nexus/


class TestBackupScript:
    """Validaciones del script backup-db.sh."""

    def test_backup_script_exists(self):
        path = BASE_DIR / "scripts" / "backup-db.sh"
        assert path.exists(), "backup-db.sh no encontrado"

    def test_backup_script_is_executable(self):
        path = BASE_DIR / "scripts" / "backup-db.sh"
        st = os.stat(path)
        assert bool(st.st_mode & stat.S_IXUSR), "backup-db.sh no es ejecutable"

    def test_backup_script_has_shebang(self):
        path = BASE_DIR / "scripts" / "backup-db.sh"
        first_line = path.read_text().splitlines()[0]
        assert first_line.startswith("#!/bin/bash"), "Shebang incorrecto"

    def test_backup_script_uses_docker_compose(self):
        path = BASE_DIR / "scripts" / "backup-db.sh"
        content = path.read_text()
        assert "docker compose" in content or "docker-compose" in content, \
            "Script debe usar docker compose para pg_dump"

    def test_backup_script_compresses_output(self):
        path = BASE_DIR / "scripts" / "backup-db.sh"
        content = path.read_text()
        assert "gzip" in content, "Backup debe comprimirse con gzip"


class TestRestoreScript:
    """Validaciones del script restore-db.sh."""

    def test_restore_script_exists(self):
        path = BASE_DIR / "scripts" / "restore-db.sh"
        assert path.exists(), "restore-db.sh no encontrado"

    def test_restore_script_is_executable(self):
        path = BASE_DIR / "scripts" / "restore-db.sh"
        st = os.stat(path)
        assert bool(st.st_mode & stat.S_IXUSR), "restore-db.sh no es ejecutable"

    def test_restore_script_accepts_argument(self):
        path = BASE_DIR / "scripts" / "restore-db.sh"
        content = path.read_text()
        assert '$1' in content or "${1}" in content, \
            "Script debe aceptar archivo de backup como argumento"

    def test_restore_script_stops_web_before_restore(self):
        path = BASE_DIR / "scripts" / "restore-db.sh"
        content = path.read_text()
        assert "docker compose stop web" in content or "docker-compose stop web" in content, \
            "Restore debe detener contenedor web antes de restaurar"


class TestMaintenanceDBScript:
    """Validaciones del script maintenance-db.sh."""

    def test_maintenance_db_exists(self):
        path = BASE_DIR / "scripts" / "maintenance-db.sh"
        assert path.exists(), "maintenance-db.sh no encontrado"

    def test_maintenance_db_executable(self):
        path = BASE_DIR / "scripts" / "maintenance-db.sh"
        st = os.stat(path)
        assert bool(st.st_mode & stat.S_IXUSR), "maintenance-db.sh no es ejecutable"

    def test_maintenance_db_runs_vacuum(self):
        path = BASE_DIR / "scripts" / "maintenance-db.sh"
        content = path.read_text()
        assert "VACUUM" in content or "vacuumdb" in content, \
            "Script debe ejecutar VACUUM ANALYZE"

    def test_maintenance_db_shows_statistics(self):
        path = BASE_DIR / "scripts" / "maintenance-db.sh"
        content = path.read_text()
        assert "pg_stat" in content, "Script debe mostrar estadísticas"


class TestMaintenanceRedisScript:
    """Validaciones del script maintenance-redis.sh."""

    def test_maintenance_redis_exists(self):
        path = BASE_DIR / "scripts" / "maintenance-redis.sh"
        assert path.exists(), "maintenance-redis.sh no encontrado"

    def test_maintenance_redis_executable(self):
        path = BASE_DIR / "scripts" / "maintenance-redis.sh"
        st = os.stat(path)
        assert bool(st.st_mode & stat.S_IXUSR), "maintenance-redis.sh no es ejecutable"

    def test_maintenance_redis_uses_redis_cli(self):
        path = BASE_DIR / "scripts" / "maintenance-redis.sh"
        content = path.read_text()
        assert "redis-cli" in content, "Script debe usar redis-cli"


class TestInitDBSQL:
    """Validaciones del script SQL de inicialización."""

    def test_init_db_sql_exists(self):
        path = BASE_DIR / "scripts" / "init-db.sql"
        assert path.exists(), "init-db.sql no encontrado"

    def test_init_db_sql_creates_extensions(self):
        path = BASE_DIR / "scripts" / "init-db.sql"
        content = path.read_text()
        assert "pg_stat_statements" in content, \
            "init-db.sql debe crear extensión pg_stat_statements"


class TestDockerComposeProductionHasBackupVolume:
    """Verifica que docker-compose.prod.yml incluya volumen de backup."""

    def test_backup_volume_defined(self):
        compose_path = BASE_DIR / "docker-compose.prod.yml"
        content = compose_path.read_text()
        # Buscar definición del volumen 'backup' en sección volumes:
        assert "backup:" in content, \
            "docker-compose.prod.yml debe definir volumen 'backup' en sección volumes"
        # Buscar montaje en servicio web:
        web_section = content.split("web:")[1].split("volumes:")[1]
        assert ":/backup" in web_section, \
            "Volumen backup debe estar montado en contenedor web como backup:/backup"


class TestDockerComposeProductionPostgresTuning:
    """Verifica que PostgreSQL tenga parámetros de tuning aplicados."""

    def test_postgres_has_command_tuning(self):
        compose_path = BASE_DIR / "docker-compose.prod.yml"
        content = compose_path.read_text()
        required_params = [
            "shared_buffers",
            "effective_cache_size",
            "max_connections",
            "wal_buffers",
            "checkpoint_completion_target",
            "random_page_cost",
        ]
        for param in required_params:
            assert param in content, f"Falta parámetro PostgreSQL: {param}"

    def test_postgres_logs_slow_queries(self):
        compose_path = BASE_DIR / "docker-compose.prod.yml"
        content = compose_path.read_text()
        assert "log_min_duration_statement" in content, \
            "PostgreSQL debe loguear queries lentos (log_min_duration_statement)"


class TestDockerComposeProductionRedisConfig:
    """Verifica configuración de Redis para producción."""

    def test_redis_has_password(self):
        compose_path = BASE_DIR / "docker-compose.prod.yml"
        content = compose_path.read_text()
        assert "requirepass" in content, "Redis debe tener contraseña (requirepass)"

    def test_redis_has_maxmemory(self):
        compose_path = BASE_DIR / "docker-compose.prod.yml"
        content = compose_path.read_text()
        assert "maxmemory" in content, "Redis debe limitar memoria (maxmemory)"

    def test_redis_has_appendonly(self):
        compose_path = BASE_DIR / "docker-compose.prod.yml"
        content = compose_path.read_text()
        assert "appendonly" in content, "Redis debe tener AOF persistencia (appendonly)"

    def test_redis_rename_dangerous_commands(self):
        compose_path = BASE_DIR / "docker-compose.prod.yml"
        content = compose_path.read_text()
        # FLUSHDB y FLUSHALL deben estar renombrados o deshabilitados
        assert "FLUSHDB" in content and "FLUSHALL" in content, \
            "Redis debe renombrar comandos peligrosos (FLUSHDB/FLUSHALL) para seguridad"
