"""Tests para autenticación API — login, register, JWT."""
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model


class TestAuthLogin(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )

    def test_login_success(self):
        client = Client()
        r = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "testuser", "password": "testpass123"}),
            content_type="application/json",
        )
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self):
        client = Client()
        r = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "testuser", "password": "wrongpass"}),
            content_type="application/json",
        )
        # 401 = credenciales inválidas, 429 = rate limit (si hay muchos tests)
        assert r.status_code in [401, 429]

    def test_login_missing_fields(self):
        client = Client()
        r = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "testuser"}),
            content_type="application/json",
        )
        assert r.status_code == 422


class TestAuthRegister(TestCase):
    def test_register_success(self):
        client = Client()
        r = client.post(
            "/api/v1/auth/register",
            data=json.dumps({
                "username": "newuser",
                "email": "new@test.com",
                "password": "securepass123",
                "display_name": "New User",
            }),
            content_type="application/json",
        )
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@test.com"

    def test_register_duplicate_username(self):
        User = get_user_model()
        User.objects.create_user(username="existing", email="ex@test.com", password="pass")

        client = Client()
        r = client.post(
            "/api/v1/auth/register",
            data=json.dumps({
                "username": "existing",
                "email": "new@test.com",
                "password": "securepass123",
            }),
            content_type="application/json",
        )
        assert r.status_code == 409


class TestAuthMe(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="meuser", email="me@test.com", password="testpass123"
        )

    def test_me_with_token(self):
        client = Client()

        # Login
        r = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "meuser", "password": "testpass123"}),
            content_type="application/json",
        )
        token = r.json()["access_token"]

        # Get /me
        r = client.get(
            "/api/v1/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        assert r.status_code == 200
        assert r.json()["username"] == "meuser"

    def test_me_without_token(self):
        client = Client()
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401


class TestAuthRefresh(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="refuser", email="ref@test.com", password="testpass123"
        )

    def test_refresh_success(self):
        client = Client()

        # Login
        r = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "refuser", "password": "testpass123"}),
            content_type="application/json",
        )
        refresh_token = r.json()["refresh_token"]

        # Refresh
        r = client.post(
            "/api/v1/auth/refresh",
            data=json.dumps({"refresh_token": refresh_token}),
            content_type="application/json",
        )
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data

    def test_refresh_with_access_token_fails(self):
        """Usar un access token como refresh token debe fallar."""
        client = Client()

        r = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "refuser", "password": "testpass123"}),
            content_type="application/json",
        )
        access_token = r.json()["access_token"]

        r = client.post(
            "/api/v1/auth/refresh",
            data=json.dumps({"refresh_token": access_token}),
            content_type="application/json",
        )
        assert r.status_code == 401


class TestProtectedEndpoints(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="protuser", email="prot@test.com", password="testpass123"
        )
        client = Client()
        r = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "protuser", "password": "testpass123"}),
            content_type="application/json",
        )
        self.token = r.json()["access_token"]

    def test_modules_requires_auth(self):
        client = Client()
        r = client.get("/api/v1/modules/")
        assert r.status_code == 401

    def test_modules_with_token(self):
        client = Client()
        r = client.get(
            "/api/v1/modules/",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert r.status_code == 200

    def test_events_requires_auth(self):
        client = Client()
        r = client.get("/api/v1/events/")
        assert r.status_code == 401

    def test_health_is_public(self):
        """Health check debe ser público."""
        client = Client()
        r = client.get("/api/v1/health")
        assert r.status_code == 200
