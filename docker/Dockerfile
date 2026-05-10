# Dockerfile — ERP Nexus
# Multi-stage build para producción

# ============================================
# Stage 1: Builder (instalar uv + deps)
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /bin/uv /bin/uv

# Dependencias
COPY pyproject.toml uv.lock* ./

# Instalar dependencias en directorio aislado
RUN uv sync --no-dev --frozen --no-install-project

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Crear usuario no-root
RUN useradd --create-home appuser

# Instalar system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar uv desde builder
COPY --from=builder /bin/uv /bin/uv

# Copiar venv del builder
COPY --from=builder /app/.venv /app/.venv

# Establecer PATH para venv
ENV PATH="/app/.venv/bin:$PATH"

# Copiar código
COPY --chown=appuser:appuser . .

# Crear directorios necesarios
RUN mkdir -p /app/media /app/static /app/logs \
    && chown -R appuser:appuser /app/media /app/static /app/logs

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=erp_nexus.settings.production

# Switch a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Comando por defecto
CMD ["gunicorn", "erp_nexus.asgi:application", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
