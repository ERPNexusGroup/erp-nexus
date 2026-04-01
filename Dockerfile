# ════════════════════════════════════════════════════════════════════════
# ERP Nexus — Dockerfile multi-stage
# ════════════════════════════════════════════════════════════════════════

# ─── Stage 1: Builder ─────────────────────────────────────────────────
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

# Instalar uv
RUN pip install --no-cache-dir uv

# Copiar dependencias e instalar
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copiar código fuente
COPY . .

# Instalar el proyecto
RUN uv sync --frozen --no-dev

# Collect static
RUN uv run python manage.py collectstatic --noinput || true

# ─── Stage 2: Runtime ─────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=erp_nexus.settings.production

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN groupadd -r erp && useradd -r -g erp erp

# Copiar desde builder
COPY --from=builder /build/.venv /app/.venv
COPY --from=builder /build /app

# Ajustar PATH
ENV PATH="/app/.venv/bin:$PATH"

# Crear directorios necesarios
RUN mkdir -p /app/modules /app/staticfiles /app/media /app/logs && \
    chown -R erp:erp /app

USER erp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

EXPOSE 8000

# Default: gunicorn con uvicorn workers
CMD ["gunicorn", "erp_nexus.asgi:application", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
