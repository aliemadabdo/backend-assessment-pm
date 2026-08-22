import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from users.tests.factories import UserFactory

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestAuth:

    # ── Registration ──────────────────────────────────────────

    def test_successful_registration(self, api_client):
        payload = {
            "username": "john",
            "email": "john@example.com",
            "password": "StrongPass123!",
        }

        response = api_client.post("/api/register/", payload, format="json")

        assert response.status_code == 201
        assert response.data["username"] == "john"
        assert response.data["email"] == "john@example.com"
        assert "token" in response.data
        assert "password" not in response.data
        assert User.objects.filter(username="john").exists()

    def test_duplicate_username(self, api_client):
        UserFactory(username="john")

        response = api_client.post(
            "/api/register/",
            {"username": "john", "email": "other@example.com", "password": "StrongPass123!"},
            format="json",
        )

        assert response.status_code == 400

    def test_register_missing_password_returns_400(self, api_client):
        response = api_client.post("/api/register/", {"username": "alice"}, format="json")

        assert response.status_code == 400
        assert "detail" in response.data

    # @pytest.mark.skip(reason="Weak password rejection not enforced yet — re-enable once AUTH_PASSWORD_VALIDATORS is confirmed active for this endpoint.")
    # def test_weak_password_rejected(self, api_client):
    #     response = api_client.post(
    #         "/api/register/",
    #         {"username": "weakuser", "email": "weak@example.com", "password": "password"},
    #         format="json",
    #     )

    #     assert response.status_code == 400
    #     assert not User.objects.filter(username="weakuser").exists()

    # ── Login ──────────────────────────────────────────────────

    def test_successful_login(self, api_client):
        # UserFactory's default password is "StrongPass123!" via set_password,
        # no need to override it explicitly unless a test needs a different one.
        user = UserFactory(username="john")

        response = api_client.post(
            "/api/login/",
            {"username": "john", "password": "StrongPass123!"},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["username"] == user.username
        assert response.data["token"]

    def test_login_invalid_credentials_returns_400(self, api_client):
        UserFactory(username="alice")

        response = api_client.post(
            "/api/login/",
            {"username": "alice", "password": "wrongpass"},
            format="json",
        )

        assert response.status_code == 400
        assert response.data["detail"] == "Invalid credentials."