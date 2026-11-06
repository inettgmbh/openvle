"""Integration tests for /system/ endpoints (misc routes without version prefix)."""


class TestGetApiVersion:
    """GET /system/api/version -- get API version."""

    def test_returns_version(self, client, auth_headers, mock_permission_allow):
        resp = client.get("/system/api/version", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "api_version" in data

    def test_version_matches_settings(
        self, client, auth_headers, mock_permission_allow
    ):
        resp = client.get("/system/api/version", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        from core.config import Settings

        settings = Settings()
        assert data["api_version"] == settings.project_version

    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/system/api/version")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, system_read is denied."""
        resp = client.get("/system/api/version", headers=auth_headers)
        assert resp.status_code == 403


class TestHealthAuthenticated:
    """GET /system/health/authenticated -- health with auth."""

    def test_returns_health_status(
        self, client, auth_headers, mock_permission_allow
    ):
        resp = client.get("/system/health/authenticated", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Services may be ERROR but endpoint returns 200
        assert "MariaDB" in data
        assert "Redis" in data

    def test_response_contains_all_services(
        self, client, auth_headers, mock_permission_allow
    ):
        resp = client.get("/system/health/authenticated", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        expected_services = [
            "MariaDB",
            "MongoDB",
            "Redis",
            "Proxmox",
            "Guacamole",
            "LDAP",
        ]
        for service in expected_services:
            assert service in data
            assert "status" in data[service]

    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/system/health/authenticated")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, system_read is denied."""
        resp = client.get("/system/health/authenticated", headers=auth_headers)
        assert resp.status_code == 403


class TestHealthToken:
    """GET /system/health/token -- health with API token."""

    def test_valid_token_returns_200(self, client):
        """The test environment sets api_health_token to 'test-health-token'."""
        resp = client.get(
            "/system/health/token",
            headers={"token": "test-health-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "MariaDB" in data
        assert "Redis" in data

    def test_wrong_token_returns_403(self, client):
        resp = client.get(
            "/system/health/token", headers={"token": "wrong-token"}
        )
        assert resp.status_code == 403

    def test_no_token_returns_403(self, client):
        resp = client.get("/system/health/token")
        assert resp.status_code == 403
