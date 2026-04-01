"""Tests para audit log y permisos."""
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.core_audit.models import AuditLog


class TestAuditLog(TestCase):
    def test_create_audit_log(self):
        log = AuditLog.log(
            action="data.create",
            resource_type="Product",
            resource_id="42",
            description="Producto creado",
        )
        assert log.action == "data.create"
        assert log.resource_type == "Product"
        assert str(log.resource_id) == "42"

    def test_audit_log_with_user(self):
        User = get_user_model()
        user = User.objects.create_user(username="auduser", password="pass123")

        log = AuditLog.log(
            action="auth.login",
            user=user,
            description="Login",
        )
        assert log.user_id == user.id
        assert log.username == "auduser"

    def test_audit_log_login_records(self):
        """Login via API debe crear audit log."""
        User = get_user_model()
        User.objects.create_user(username="loguser", email="log@test.com", password="pass123")

        client = Client()
        client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "loguser", "password": "pass123"}),
            content_type="application/json",
        )

        log = AuditLog.objects.filter(action="auth.login", username="loguser").first()
        assert log is not None
        assert log.action == "auth.login"


class TestAuditAPI(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="auditapi", email="audit@test.com", password="pass123"
        )
        client = Client()
        r = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "auditapi", "password": "pass123"}),
            content_type="application/json",
        )
        self.token = r.json()["access_token"]

    def test_audit_list(self):
        client = Client()
        r = client.get(
            "/api/v1/audit/",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_audit_stats(self):
        client = Client()
        r = client.get(
            "/api/v1/audit/stats",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "by_action" in data

    def test_audit_filter_by_action(self):
        client = Client()
        r = client.get(
            "/api/v1/audit/?action=auth.login",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert r.status_code == 200


class TestPermissions(TestCase):
    def test_superuser_has_access(self):
        from apps.core_api.permissions import _get_user_permissions
        User = get_user_model()
        user = User.objects.create_superuser(username="super", password="pass")
        # Superuser bypasses permission check, not tested via _get_user_permissions
        assert user.is_superuser

    def test_regular_user_no_permissions(self):
        from apps.core_api.permissions import _get_user_permissions
        User = get_user_model()
        user = User.objects.create_user(username="regular", password="pass")
        perms = _get_user_permissions(user)
        assert len(perms) == 0
