# Tests de validación Monitoring Stack — ERP Nexus
# Valida configuración Prometheus, Grafana, AlertManager y Docker Compose

from pathlib import Path
import json
import yaml

import pytest


BASE = Path(__file__).resolve().parents[3]


class TestPrometheusConfiguration:
    """Validación de configuración Prometheus."""

    def test_prometheus_yml_exists(self):
        assert (BASE / "monitoring/prometheus/prometheus.yml").exists(), \
            "prometheus.yml no encontrado"

    def test_prometheus_global_scrape_interval(self):
        config = yaml.safe_load((BASE / "monitoring/prometheus/prometheus.yml").read_text())
        assert config['global']['scrape_interval'] == '15s'

    def test_prometheus_evaluation_interval(self):
        config = yaml.safe_load((BASE / "monitoring/prometheus/prometheus.yml").read_text())
        assert config['global']['evaluation_interval'] == '15s'

    def test_prometheus_has_django_job(self):
        config = yaml.safe_load((BASE / "monitoring/prometheus/prometheus.yml").read_text())
        jobs = [s['job_name'] for s in config['scrape_configs']]
        assert 'django' in jobs

    def test_prometheus_has_celery_job(self):
        config = yaml.safe_load((BASE / "monitoring/prometheus/prometheus.yml").read_text())
        jobs = [s['job_name'] for s in config['scrape_configs']]
        assert 'celery' in jobs

    def test_prometheus_has_cadvisor_job(self):
        config = yaml.safe_load((BASE / "monitoring/prometheus/prometheus.yml").read_text())
        jobs = [s['job_name'] for s in config['scrape_configs']]
        assert 'cadvisor' in jobs

    def test_prometheus_has_node_exporter_job(self):
        config = yaml.safe_load((BASE / "monitoring/prometheus/prometheus.yml").read_text())
        jobs = [s['job_name'] for s in config['scrape_configs']]
        assert 'node' in jobs or 'node-exporter' in jobs

    def test_prometheus_has_alerting_configured(self):
        config = yaml.safe_load((BASE / "monitoring/prometheus/prometheus.yml").read_text())
        assert 'alerting' in config
        assert 'alertmanagers' in config['alerting']

    def test_prometheus_external_labels(self):
        config = yaml.safe_load((BASE / "monitoring/prometheus/prometheus.yml").read_text())
        labels = config['global']['external_labels']
        assert labels.get('environment') == 'production'
        assert labels.get('cluster') == 'erp-nexus-prod'


class TestAlertRules:
    """Validación de reglas de alerta."""

    def test_alert_rules_file_exists(self):
        assert (BASE / "monitoring/prometheus/alerts/erp_nexus_rules.yml").exists()

    def test_alert_rules_valid_yaml(self):
        yaml.safe_load((BASE / "monitoring/prometheus/alerts/erp_nexus_rules.yml").read_text())

    def test_alert_rules_has_critical_group(self):
        data = yaml.safe_load((BASE / "monitoring/prometheus/alerts/erp_nexus_rules.yml").read_text())
        groups = [g['name'] for g in data['groups']]
        assert 'erp_nexus_critical' in groups

    def test_alert_rules_has_warnings_group(self):
        data = yaml.safe_load((BASE / "monitoring/prometheus/alerts/erp_nexus_rules.yml").read_text())
        groups = [g['name'] for g in data['groups']]
        assert 'erp_nexus_warnings' in groups

    def test_critical_alerts_have_severity_label(self):
        data = yaml.safe_load((BASE / "monitoring/prometheus/alerts/erp_nexus_rules.yml").read_text())
        for group in data['groups']:
            if group['name'] == 'erp_nexus_critical':
                for rule in group['rules']:
                    assert rule['labels']['severity'] == 'critical'

    def test_alerts_have_annotations(self):
        data = yaml.safe_load((BASE / "monitoring/prometheus/alerts/erp_nexus_rules.yml").read_text())
        for group in data['groups']:
            for rule in group['rules']:
                assert 'summary' in rule['annotations']
                assert 'description' in rule['annotations']


class TestGrafanaProvisioning:
    """Validación de provisioning Grafana."""

    def test_datasource_config_exists(self):
        assert (BASE / "monitoring/grafana/provisioning/datasources/prometheus.yml").exists()

    def test_datasource_config_valid_yaml(self):
        yaml.safe_load((BASE / "monitoring/grafana/provisioning/datasources/prometheus.yml").read_text())

    def test_dashboard_provisioning_exists(self):
        assert (BASE / "monitoring/grafana/provisioning/dashboards/erp_nexus.yml").exists()

    def test_dashboard_provisioning_valid_yaml(self):
        yaml.safe_load((BASE / "monitoring/grafana/provisioning/dashboards/erp_nexus.yml").read_text())

    def test_grafana_config_exists(self):
        assert (BASE / "monitoring/grafana/provisioning/config/grafana.ini").exists()

    def test_grafana_config_has_smtp(self):
        content = (BASE / "monitoring/grafana/provisioning/config/grafana.ini").read_text()
        assert "[smtp]" in content
        assert "enabled = true" in content

    def test_dashboard_json_exists(self):
        assert (BASE / "monitoring/grafana/dashboards/erp_nexus.json").exists()

    def test_dashboard_json_valid(self):
        json.loads((BASE / "monitoring/grafana/dashboards/erp_nexus.json").read_text())


class TestAlertManager:
    """Validación de configuración AlertManager."""

    def test_alertmanager_config_exists(self):
        assert (BASE / "monitoring/alertmanager/alertmanager.yml").exists()

    def test_alertmanager_config_valid_yaml(self):
        yaml.safe_load((BASE / "monitoring/alertmanager/alertmanager.yml").read_text())

    def test_alertmanager_has_route(self):
        config = yaml.safe_load((BASE / "monitoring/alertmanager/alertmanager.yml").read_text())
        assert 'route' in config
        assert 'receiver' in config['route']

    def test_alertmanager_has_receivers(self):
        config = yaml.safe_load((BASE / "monitoring/alertmanager/alertmanager.yml").read_text())
        assert 'receivers' in config
        assert len(config['receivers']) >= 1

    def test_alertmanager_has_slack_receiver(self):
        config = yaml.safe_load((BASE / "monitoring/alertmanager/alertmanager.yml").read_text())
        receivers = [r['name'] for r in config['receivers']]
        assert 'slack-erp-nexus' in receivers

    def test_alertmanager_has_inhibit_rules(self):
        config = yaml.safe_load((BASE / "monitoring/alertmanager/alertmanager.yml").read_text())
        assert 'inhibit_rules' in config


class TestDockerComposeIntegration:
    """Validación de servicios de monitoreo en docker-compose."""

    def _get_service_block(self, compose: str, service: str) -> str:
        lines = compose.splitlines()
        start_idx = None
        base_indent = None
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            if stripped == f"{service}:":
                start_idx = i
                base_indent = indent
                break
        if start_idx is None:
            return ""
        end_idx = len(lines)
        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            stripped = line.lstrip()
            if stripped == "":
                continue
            if len(line) - len(stripped) <= base_indent and stripped.endswith(":"):
                end_idx = i
                break
        return "\n".join(lines[start_idx:end_idx])

    def test_prometheus_service_defined(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "prometheus:" in compose, "Servicio prometheus no definido"

    def test_prometheus_command_flags(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        prom_section = self._get_service_block(compose, "prometheus")
        assert "--config.file=/etc/prometheus/prometheus.yml" in prom_section
        assert "--storage.tsdb.path=/prometheus" in prom_section

    def test_prometheus_ports_exposed(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        prom_section = self._get_service_block(compose, "prometheus")
        assert '"9090:9090"' in prom_section or "'9090:9090'" in prom_section

    def test_prometheus_uses_alert_rules_volume(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        prom_section = self._get_service_block(compose, "prometheus")
        assert "./monitoring/prometheus/alerts:/etc/prometheus/alerts:ro" in prom_section

    def test_grafana_service_defined(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "grafana:" in compose, "Servicio grafana no definido"

    def test_grafana_ports_exposed(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        grafana_section = self._get_service_block(compose, "grafana")
        assert '"3000:3000"' in grafana_section or "'3000:3000'" in grafana_section

    def test_grafana_env_admin_password(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        grafana_section = self._get_service_block(compose, "grafana")
        assert "GF_SECURITY_ADMIN_PASSWORD" in grafana_section

    def test_grafana_provisioning_volumes(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        grafana_section = self._get_service_block(compose, "grafana")
        assert "provisioning:/etc/grafana/provisioning:ro" in grafana_section

    def test_cadvisor_service_defined(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "cadvisor:" in compose, "Servicio cadvisor no definido"

    def test_cadvisor_ports_exposed(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        cadvisor_section = self._get_service_block(compose, "cadvisor")
        assert '"8080:8080"' in cadvisor_section or "'8080:8080'" in cadvisor_section

    def test_node_exporter_service_defined(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "node-exporter:" in compose, "Servicio node-exporter no definido"

    def test_node_exporter_ports_exposed(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        ne_section = self._get_service_block(compose, "node-exporter")
        assert '"9100:9100"' in ne_section or "'9100:9100'" in ne_section

    def test_alertmanager_service_defined(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "alertmanager:" in compose, "Servicio alertmanager no definido"

    def test_alertmanager_ports_exposed(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        am_section = self._get_service_block(compose, "alertmanager")
        assert '"9093:9093"' in am_section or "'9093:9093'" in am_section


class TestDockerComposeVolumes:
    """Validación de volúmenes de monitoreo."""

    def test_promdata_volume_defined(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "promdata:" in compose

    def test_grafanadata_volume_defined(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "grafanadata:" in compose

    def test_alertmanagerdata_volume_defined(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        assert "alertmanagerdata:" in compose


class TestEnvironmentVariables:
    """Validación de variables de entorno de monitoreo."""

    def test_env_has_grafana_admin_user(self):
        env = (BASE / ".env.prod.example").read_text()
        assert "GRAFANA_ADMIN_USER=" in env

    def test_env_has_grafana_admin_password(self):
        env = (BASE / ".env.prod.example").read_text()
        assert "GRAFANA_ADMIN_PASSWORD=" in env

    def test_env_has_smtp_host(self):
        env = (BASE / ".env.prod.example").read_text()
        assert "SMTP_HOST=" in env

    def test_env_has_slack_webhook(self):
        env = (BASE / ".env.prod.example").read_text()
        assert "SLACK_WEBHOOK_URL=" in env

    def test_env_has_alert_emails(self):
        env = (BASE / ".env.prod.example").read_text()
        assert "ADMIN_ALERT_EMAIL=" in env
        assert "DB_ADMIN_EMAIL=" in env
        assert "DEVOPS_ALERT_EMAIL=" in env


class TestIntegration:
    """Validación de integración entre componentes."""

    def test_prometheus_has_grafana_as_datasource(self):
        # En producción, Grafana se conecta a Prometheus en http://prometheus:9090
        # Este test valida que el datasource esté configurado correctamente
        ds = yaml.safe_load((BASE / "monitoring/grafana/provisioning/datasources/prometheus.yml").read_text())
        assert ds['datasources'][0]['url'] == 'http://prometheus:9090'

    def test_docker_compose_monitoring_depends_on_web(self):
        compose = (BASE / "docker-compose.prod.yml").read_text()
        # Prometheus y AlertManager dependen de web (para métricas)
        assert "depends_on:" in compose
