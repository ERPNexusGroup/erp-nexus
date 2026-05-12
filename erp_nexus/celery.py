"""
Celery Configuration — ERP Nexus
================================
Configuración centralizada de Celery para tareas asíncronas.
Redis es broker y result backend (asegurar REDIS_URL en .env.prod).
"""

import os
from celery import Celery

# Set default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_nexus.settings')

app = Celery('erp_nexus')

# Load configuration from Django settings, using CELERY_ namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed Django apps
app.autodiscover_tasks()


# ─── Signal handlers (opcional - logging) ─────────────────────────────────────
@app.task(bind=True)
def debug_task(self):
    """Task de debugging — imprime solicitud."""
    print(f'Request: {self.request!r}')
