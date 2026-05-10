# Makefile — ERP Nexus
# Uso: make <target>
# Ejemplo: make dev (setup dev), make test, make lint

.PHONY: help dev install test lint format clean docker-up docker-down migrate shell

# ─── Default target ───────────────────────────────────────────────────────────
help:
	@echo "ERP Nexus — Comandos disponibles:"
	@echo ""
	@echo "  make dev          Setup entorno desarrollo (primera vez)"
	@echo "  make install      Instalar dependencias (uv sync)"
	@echo "  make migrate      Aplicar migraciones Django"
	@echo "  make superuser    Crear superusuario interactivo"
	@echo "  make test         Ejecutar tests (pytest)"
	@echo "  make test-cov     Tests con cobertura HTML"
	@echo "  make lint         Linter (ruff check)"
	@echo "  make format       Formatear código (black + isort)"
	@echo "  make typecheck    Type checking (mypy)"
	@echo "  make shell        Django shell interactivo"
	@echo "  make runserver    Levantar servidor desarrollo"
	@echo "  make docker-up    Docker Compose (all services)"
	@echo "  make docker-down  Detener Docker Compose"
	@echo "  make clean        Limpiar archivos temporales"
	@echo ""

# ─── Setup desarrollo ─────────────────────────────────────────────────────────
dev: install migrate
	@echo ""
	@echo "✅ Setup completado. Ejecuta 'make runserver' para iniciar."

install:
	@echo "📦 Instalando dependencias con uv..."
	uv sync
	@echo "✅ Dependencias instaladas en .venv/"

migrate:
	@echo "🗄️  Aplicando migraciones..."
	uv run python manage.py migrate --noinput
	@echo "✅ Migraciones aplicadas"

superuser:
	uv run python manage.py bootstrap_superadmin

# ─── Development server ───────────────────────────────────────────────────────
runserver:
	uv run python manage.py runserver

runserver-plus:
	uv run python manage.py runserver_plus  # Requiere django-extensions

# ─── Testing ──────────────────────────────────────────────────────────────────
test:
	uv run pytest -xvs

test-quiet:
	uv run pytest -q

test-cov:
	uv run pytest --cov=. --cov-report=html
	@echo "📊 Reporte de cobertura: htmlcov/index.html"

test-module:
	uv run pytest modules/facturacion_ec/tests/ -v

# ─── Linting & Formatting ─────────────────────────────────────────────────────
lint:
	@echo "🔍 Running linter (ruff)..."
	uv run ruff check .
	@echo "✅ No issues found"

format:
	@echo "🎨 Formatting code (black + isort)..."
	uv run black .
	uv run isort .
	@echo "✅ Code formatted"

typecheck:
	@echo "🔎 Type checking (mypy)..."
	uv run mypy . --config-file=pyproject.toml

# ─── Docker ────────────────────────────────────────────────────────────────────
docker-up:
	docker-compose up -d
	@echo "🐳 Servicios Docker iniciados"
	@echo "   ERP Nexus: http://localhost:8000"
	@echo "   PostgreSQL: localhost:5432"
	@echo "   Redis: localhost:6379"

docker-down:
	docker-compose down
	@echo "🐳 Servicios detenidos"

docker-logs:
	docker-compose logs -f web

docker-shell:
	docker-compose exec web uv run python manage.py shell

# ─── Database ──────────────────────────────────────────────────────────────────
db-backup:
	@echo "💾 Backup de base de datos..."
	uv run python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > backup.json
	@echo "✅ Backup guardado en backup.json"

db-restore:
	@echo "⚠️  Esto borrará todos los datos! ¿Continuar? [y/N]"
	read answer; if [ "$$answer" = "y" ]; then \
		uv run python manage.py flush --noinput; \
		uv run python manage.py loaddata backup.json; \
		echo "✅ Restore completado"; \
	else \
		echo "❌ Cancelado"; \
	fi

flush:
	uv run python manage.py flush --noinput

# ─── Maintenance ───────────────────────────────────────────────────────────────
clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -f {} + 2>/dev/null || true
	rm -rf .venv/ .uv/ dist/ build/ *.egg-info/ 2>/dev/null || true
	rm -f db.sqlite3 2>/dev/null || true
	@echo "✅ Limpieza completada"

# ─── Security ──────────────────────────────────────────────────────────────────
check-secrets:
	@echo "🔐 Buscando posibles secrets en el código..."
	@grep -r "password\s*=" . --include="*.py" --include="*.env" | grep -v "example" || echo "✅ No se encontraron passwords en código"
	@grep -r "API_KEY\s*=" . --include="*.py" --include="*.env" | grep -v "example" || echo "✅ No se encontraron API keys en código"

# ─── Helpful aliases ───────────────────────────────────────────────────────────
shell:
	uv run python manage.py shell

shell-plus:  # Requiere django-extensions
	uv run python manage.py shell_plus

admin:
	uv run python manage.py createsuperuser

makemigrations:
	uv run python manage.py makemigrations

show-migrations:
	uv run python manage.py showmigrations

# ─── Module management ─────────────────────────────────────────────────────────
module-list:
	uv run python manage.py module list

module-install:  # Uso: make module-install path=./mi_modulo
	uv run python manage.py install_module $(path)

module-validate:
	uv run python manage.py module validate facturacion_ec
