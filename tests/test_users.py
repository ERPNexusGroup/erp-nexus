"""Tests para usuarios API — profile, password, password reset."""
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache


class TestUserProfile(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="profileuser", email="profile@test.com", password="testpass123"
        )
        client = Client()
        r = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "profileuser", "password": "testpass123"}),
            content_type="application/json",
        )
        self.token = r.json()["access_token"]

    def test_get_profile(self):
        client = Client()
        r = client.get(
            "/api/v1/users/me",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "profileuser"
        assert data["email"] == "profile@test.com"

    def test_update_profile(self):
        client = Client()
        r = client.patch(
            "/api/v1/users/me",
            data=json.dumps({"display_name": "Updated Name"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert r.status_code == 200
        assert r.json()["display_name"] == "Updated Name"

    def test_change_password(self):
        client = Client()
        r = client.post(
            "/api/v1/users/change-password",
            data=json.dumps({
                "current_password": "testpass123",
                "new_password": "newpass45678",
            }),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert r.status_code == 200

        # Verify can login with new password
        r = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "profileuser", "password": "newpass45678"}),
            content_type="application/json",
        )
        assert r.status_code == 200

    def test_change_password_wrong_current(self):
        client = Client()
        r = client.post(
            "/api/v1/users/change-password",
            data=json.dumps({
                "current_password": "wrongpass",
                "new_password": "newpass45678",
            }),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert r.status_code == 400


class TestPasswordReset(TestCase):
    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.user = User.objects.create_user(
            username="resetuser", email="reset@test.com", password="oldpass123"
        )

    def test_request_reset(self):
        client = Client()
        r = client.post(
            "/api/v1/auth/password-reset/request",
            data=json.dumps({"email": "reset@test.com"}),
            content_type="application/json",
        )
        assert r.status_code == 200

    def test_request_reset_unknown_email(self):
        """Debe retornar éxito incluso si el email no existe."""
        client = Client()
        r = client.post(
            "/api/v1/auth/password-reset/request",
            data=json.dumps({"email": "unknown@test.com"}),
            content_type="application/json",
        )
        assert r.status_code == 200

    def test_confirm_reset(self):
        client = Client()

        # Request reset
        r = client.post(
            "/api/v1/auth/password-reset/request",
            data=json.dumps({"email": "reset@test.com"}),
            content_type="application/json",
        )

        # Get token from cache
        from django.core.cache import cache
        # Find the token in cache
        import secrets
        token = None
        for key in ["password_reset:*"]:
            pass

        # Use cache directly - the token was stored
        # For testing, we'll store and retrieve it
        test_token = secrets.token_urlsafe(32)
        cache.set(f"password_reset:{test_token}", self.user.id, 3600)

        r = client.post(
            "/api/v1/auth/password-reset/confirm",
            data=json.dumps({
                "token": test_token,
                "new_password": "newresetpass123",
            }),
            content_type="application/json",
        )
        assert r.status_code == 200

        # Verify login with new password
        r = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "resetuser", "password": "newresetpass123"}),
            content_type="application/json",
        )
        assert r.status_code == 200

    def test_confirm_reset_invalid_token(self):
        client = Client()
        r = client.post(
            "/api/v1/auth/password-reset/confirm",
            data=json.dumps({
                "token": "invalid-token",
                "new_password": "newpass123",
            }),
            content_type="application/json",
        )
        assert r.status_code == 400

    def test_confirm_reset_short_password(self):
        client = Client()
        test_token = "shortpwtoken"
        cache.set(f"password_reset:{test_token}", self.user.id, 3600)

        r = client.post(
            "/api/v1/auth/password-reset/confirm",
            data=json.dumps({
                "token": test_token,
                "new_password": "short",
            }),
            content_type="application/json",
        )
        assert r.status_code == 400
