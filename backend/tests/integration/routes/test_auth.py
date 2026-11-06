"""Integration tests for /v{x}/auth/ endpoints."""

from tests.integration.conftest import API


class TestLogin:
    """POST /auth/login -- user login."""

    def test_login_wrong_credentials_returns_401(self, client):
        resp = client.post(
            f"{API}/auth/login",
            data={"username": "nonexistent", "password": "wrongpass"},
        )
        assert resp.status_code == 401

    def test_login_missing_fields_returns_422(self, client):
        resp = client.post(f"{API}/auth/login", data={})
        assert resp.status_code == 422

    def test_login_system_user_blocked_in_non_dev(self, client):
        """The system user cannot log in when app_env != 'dev'."""
        resp = client.post(
            f"{API}/auth/login",
            data={"username": "system", "password": "anything"},
        )
        # SystemUserLoginException maps to 403
        assert resp.status_code in (401, 403)


class TestReauthenticate:
    """POST /auth/reauthenticate -- reauthenticate."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.post(f"{API}/auth/reauthenticate")
        assert resp.status_code in (401, 403)

    def test_expired_token_returns_401(self, client, expired_auth_headers):
        """An expired JWT should be rejected."""
        resp = client.post(
            f"{API}/auth/reauthenticate", headers=expired_auth_headers
        )
        assert resp.status_code in (401, 403)

    def test_bearer_token_rejected(self, client, auth_headers):
        """Regular bearer tokens must be rejected (only policy_required allowed)."""
        resp = client.post(f"{API}/auth/reauthenticate", headers=auth_headers)
        assert resp.status_code == 401

    def test_policy_required_token_accepted(self, client, active_user):
        """A valid policy_required token should be accepted."""
        from tests.helpers.auth_helpers import create_test_token

        token = create_test_token(active_user, token_type="policy_required")
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(f"{API}/auth/reauthenticate", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
