# Docker Infrastructure Tests
# Verifican que los archivos Docker y compose sean válidos

import os
import subprocess
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parents[3]  # repo root: .../erp-nexus/


class TestDockerFilesExist:
    """Verifica existencia de archivos Docker obligatorios."""

    def test_dockerfile_prod_exists(self):
        path = BASE_DIR / "Dockerfile.prod"
        assert path.exists(), "Dockerfile.prod missing"

    def test_docker_compose_prod_exists(self):
        path = BASE_DIR / "docker-compose.prod.yml"
        assert path.exists(), "docker-compose.prod.yml missing"

    def test_entrypoint_sh_exists(self):
        path = BASE_DIR / "entrypoint.sh"
        assert path.exists(), "entrypoint.sh missing"

    def test_entrypoint_is_executable(self):
        path = BASE_DIR / "entrypoint.sh"
        assert os.access(path, os.X_OK), "entrypoint.sh not executable"

    def test_dockerignore_exists(self):
        path = BASE_DIR / ".dockerignore"
        assert path.exists(), ".dockerignore missing"

    def test_env_prod_example_exists(self):
        path = BASE_DIR / ".env.prod.example"
        assert path.exists(), ".env.prod.example missing"

    def test_deployment_doc_exists(self):
        path = BASE_DIR / "docs" / "DEPLOYMENT.md"
        assert path.exists(), "docs/DEPLOYMENT.md missing"


class TestDockerfileSyntax:
    """Validación básica de sintaxis Dockerfile."""

    def test_dockerfile_has_from(self):
        path = BASE_DIR / "Dockerfile.prod"
        content = path.read_text()
        assert "FROM" in content, "Dockerfile debe tener al menos una sentencia FROM"

    def test_dockerfile_multi_stage(self):
        path = BASE_DIR / "Dockerfile.prod"
        content = path.read_text()
        # Contar ocurrencias de FROM — debe haber ≥2 (builder + runtime)
        count = content.count("FROM")
        assert count >= 2, f"Dockerfile debe ser multi-stage (2+ FROM), detectado: {count}"

    def test_dockerfile_has_healthcheck(self):
        path = BASE_DIR / "Dockerfile.prod"
        content = path.read_text()
        assert "HEALTHCHECK" in content, "Dockerfile debe incluir HEALTHCHECK"

    def test_dockerfile_exposes_port(self):
        path = BASE_DIR / "Dockerfile.prod"
        content = path.read_text()
        assert "EXPOSE" in content, "Dockerfile debe EXPOSE puerto 8000"


class TestDockerComposeSyntax:
    """Validación básica de docker-compose.yml."""

    def test_compose_has_services(self):
        path = BASE_DIR / "docker-compose.prod.yml"
        content = path.read_text()
        assert "services:" in content, "docker-compose debe definir services:"

    def test_compose_has_web_service(self):
        path = BASE_DIR / "docker-compose.prod.yml"
        content = path.read_text()
        assert "web:" in content, "docker-compose debe tener servicio 'web'"

    def test_compose_has_db_service(self):
        path = BASE_DIR / "docker-compose.prod.yml"
        content = path.read_text()
        assert "db:" in content, "docker-compose debe tener servicio 'db'"

    def test_compose_has_redis_service(self):
        path = BASE_DIR / "docker-compose.prod.yml"
        content = path.read_text()
        assert "redis:" in content, "docker-compose debe tener servicio 'redis'"

    def test_compose_web_depends_on_db(self):
        path = BASE_DIR / "docker-compose.prod.yml"
        content = path.read_text()
        assert "depends_on:" in content and "db:" in content, "web debe depender de db"


class TestEntrypointScript:
    """Validación del entrypoint.sh."""

    def test_shebang_present(self):
        path = BASE_DIR / "entrypoint.sh"
        content = path.read_text()
        assert content.startswith("#!/bin/bash"), "entrypoint.sh debe empezar con #!/bin/bash"

    def test_migrate_command_present(self):
        path = BASE_DIR / "entrypoint.sh"
        content = path.read_text()
        assert "migrate" in content, "entrypoint debe ejecutar 'python manage.py migrate'"

    def test_collectstatic_command_present(self):
        path = BASE_DIR / "entrypoint.sh"
        content = path.read_text()
        assert "collectstatic" in content, "entrypoint debe ejecutar 'python manage.py collectstatic'"

    def test_gunicorn_command_present(self):
        path = BASE_DIR / "entrypoint.sh"
        content = path.read_text()
        assert "gunicorn" in content, "entrypoint debe arrancar gunicorn"


class TestHealthEndpoint:
    """Verifica que /health/ esté configurado en urls.py."""

    def test_health_pattern_in_urls(self):
        """Lee urls.py y verifica que contenga 'health/'."""
        urls_path = BASE_DIR / "erp_nexus" / "urls.py"
        content = urls_path.read_text()
        has_health = 'path("health/"' in content or "path('health/'" in content
        assert has_health, "URLconf debe incluir path('health/', ...) en erp_nexus/urls.py"
