"""Integration tests for /v{x}/me/ endpoints (self-service)."""

from tests.integration.conftest import API


class TestGetMe:
    """GET /me -- get own user object."""

    def test_returns_user(self, client, auth_headers):
        resp = client.get(f"{API}/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "username" in data
        assert "email" in data

    def test_returns_correct_user_data(self, client, auth_headers):
        resp = client.get(f"{API}/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testuser"
        assert data["email"] == "testuser@example.com"

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/me")
        assert resp.status_code in (401, 403)


class TestGetMePermissions:
    """GET /me/permissions -- get own effective permissions."""

    def test_returns_permissions(self, client, auth_headers):
        resp = client.get(f"{API}/me/permissions", headers=auth_headers)
        assert resp.status_code == 200

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/me/permissions")
        assert resp.status_code in (401, 403)


class TestUpdateMePassword:
    """PUT /me/password -- update own password."""

    def test_unauthenticated_returns_401(self, client):
        payload = {
            "password_old": "old",
            "password_new": "new",
            "password_new_repeat": "new",
        }
        resp = client.put(f"{API}/me/password", json=payload)
        assert resp.status_code in (401, 403)

    def test_authenticated_with_invalid_old_password(self, client, auth_headers):
        """With a dummy hashed_password, old password verification fails."""
        payload = {
            "password_old": "wrongoldpassword",
            "password_new": "newpassword123",
            "password_new_repeat": "newpassword123",
        }
        resp = client.put(f"{API}/me/password", json=payload, headers=auth_headers)
        # bcrypt verification will fail on the dummy hash
        assert resp.status_code in (400, 401, 422, 500)
