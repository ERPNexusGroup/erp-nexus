# Tests de configuración Celery — ERP Nexus
# Verifica que Celery esté correctamente configurado para producción

import os
from pathlib import Path

import pytest


BASE_DIR = Path(__file__).resolve().parents[3]


class TestCeleryConfiguration:
    """Validaciones de configuración Celery en settings."""

    def test_celery_py_exists(self):
        """erp_nexus/celery.py debe existir."""
        path = BASE_DIR / "erp_nexus" / "celery.py"
        assert path.exists(), "celery.py no encontrado en erp_nexus/"

    def test_celery_app_defined(self):
        """celery.py debe definir app = Celery('erp_nexus')."""
        content = (BASE_DIR / "erp_nexus" / "celery.py").read_text()
        assert "Celery(" in content, "Celery app no definida en celery.py"
        assert "app = Celery" in content or "celery_app = Celery" in content, \
            "Variable 'app' de Celery no declarada"

    def test_celery_autodiscover_tasks(self):
        """Celery debe autodescubrir tareas de todas las apps."""
        content = (BASE_DIR / "erp_nexus" / "celery.py").read_text()
        assert "autodiscover_tasks" in content, "autodiscover_tasks() no llamado"

    def test_settings_base_has_celery_queues(self):
        """base.py debe definir CELERY_TASK_QUEUES con colas esperadas."""
        from erp_nexus.settings.base import CELERY_TASK_QUEUES
        expected_queues = {'default', 'sri', 'notifications', 'reports', 'webhooks'}
        actual = set(CELERY_TASK_QUEUES.keys())
        assert expected_queues.issubset(actual), \
            f"Faltan colas. Esperadas: {expected_queues}, Actuales: {actual}"

    def test_settings_base_celery_eager_in_dev(self):
        """En development, CELERY_TASK_ALWAYS_EAGER debe ser True."""
        from erp_nexus.settings.development import CELERY_TASK_ALWAYS_EAGER
        assert CELERY_TASK_ALWAYS_EAGER is True, \
            "Development debe usar eager mode (sin broker)"

    def test_settings_prod_celery_not_eager(self):
        """En producción CELERY_TASK_ALWAYS_EAGER debe ser False.
        Verificamos leyendo el archivo production.py (no importando, para evitar
        requerir env vars en tests).
        """
        prod_path = BASE_DIR / "erp_nexus" / "settings" / "production.py"
        content = prod_path.read_text()
        assert "CELERY_TASK_ALWAYS_EAGER = False" in content, \
            "Producción debe tener CELERY_TASK_ALWAYS_EAGER = False"

    def test_settings_prod_has_broker_url(self):
        """Producción debe definir CELERY_BROKER_URL (desde REDIS_URL)."""
        prod_path = BASE_DIR / "erp_nexus" / "settings" / "production.py"
        content = prod_path.read_text()
        assert "CELERY_BROKER_URL" in content, \
            "CELERY_BROKER_URL no configurado en production.py"

    def test_tasks_module_exists(self):
        """Debe existir al menos un módulo tasks.py en alguna app."""
        # Buscar apps con tasks.py
        apps_dir = BASE_DIR / "apps"
        tasks_files = list(apps_dir.rglob("tasks.py"))
        assert len(tasks_files) > 0, "Ninguna app define tasks.py (necesario para Celery)"

    def test_celery_task_decorator_used(self):
        """Las tareas deben usar @shared_task o @app.task."""
        apps_dir = BASE_DIR / "apps"
        task_files = list(apps_dir.rglob("tasks.py"))
        found = False
        for tf in task_files:
            content = tf.read_text()
            if "@shared_task" in content or "@app.task" in content:
                found = True
                break
        assert found, "Ningún tasks.py usa @shared_task o @app.task"


class TestDockerComposeCeleryServices:
    """Validación de servicios Celery en docker-compose.prod.yml."""

    def test_worker_service_defined(self):
        compose = (BASE_DIR / "docker-compose.prod.yml").read_text()
        assert "worker:" in compose, "Servicio 'worker' no definido en docker-compose"

    def test_beat_service_defined(self):
        compose = (BASE_DIR / "docker-compose.prod.yml").read_text()
        assert "beat:" in compose, "Servicio 'beat' no definido en docker-compose"

    def test_worker_has_celery_command(self):
        compose = (BASE_DIR / "docker-compose.prod.yml").read_text()
        worker_section = compose.split("worker:")[1].split("beat:")[0]  # entre worker y beat
        assert "celery -A erp_nexus worker" in worker_section, \
            "Comando celery worker no encontrado en servicio worker"

    def test_worker_queues_match_settings(self):
        """Las colas en worker command deben coincidir con settings."""
        compose = (BASE_DIR / "docker-compose.prod.yml").read_text()
        worker_section = compose.split("worker:")[1].split("beat:")[0]
        queues_arg = [q.strip() for q in worker_section.split("--queues=")[1].split()[0].split(",")]

        from erp_nexus.settings.base import CELERY_TASK_QUEUES
        expected = list(CELERY_TASK_QUEUES.keys())
        assert set(queues_arg) == set(expected), \
            f"Colas en worker ({queues_arg}) no coinciden con settings ({expected})"

    def test_beat_has_scheduler(self):
        compose = (BASE_DIR / "docker-compose.prod.yml").read_text()
        beat_section = compose.split("beat:")[1]
        assert "celery -A erp_nexus beat" in beat_section, \
            "Comando celery beat no encontrado"

    def test_worker_depends_on_redis(self):
        compose = (BASE_DIR / "docker-compose.prod.yml").read_text()
        worker_section = compose.split("worker:")[1].split("beat:")[0]
        assert "redis:" in worker_section and "depends_on:" in worker_section, \
            "Worker debe depender de redis"


class TestCeleryTasksExist:
    """Verifica que existan tareas base para colas críticas."""

    def test_sri_task_exists(self):
        """Debe existir tarea send_invoice_to_sri_task."""
        from apps.notifications.tasks import send_invoice_to_sri_task
        assert callable(send_invoice_to_sri_task), "send_invoice_to_sri_task no es callable"

    def test_email_task_exists(self):
        """Debe existir tarea send_email_task."""
        from apps.notifications.tasks import send_email_task
        assert callable(send_email_task)

    def test_report_task_exists(self):
        """Debe existir al menos una tarea de reportes."""
        from apps.notifications.tasks import generate_invoice_pdf_task
        assert callable(generate_invoice_pdf_task)

    def test_webhook_task_exists(self):
        """Debe existir tarea send_webhook_task."""
        from apps.notifications.tasks import send_webhook_task
        assert callable(send_webhook_task)
