"""Integration tests for /v{x}/statistics/ endpoints."""

from tests.integration.conftest import API


class TestGetStatisticsDashboard:
    """GET /statistics/dashboard -- get statistics dashboard."""

    def test_returns_basic_dashboard(self, client, auth_headers):
        """Without admin permissions, returns basic dashboard (no PVE needed)."""
        resp = client.get(f"{API}/statistics/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "vms" in data
        assert "courses" in data
        assert "events" in data
        assert "connections" in data

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/statistics/dashboard")
        assert resp.status_code in (401, 403)

    def test_admin_dashboard_fails_without_pve(
        self, client, auth_headers, mock_permission_allow
    ):
        """With admin permissions, tries to connect to PVE which fails -> 500."""
        resp = client.get(f"{API}/statistics/dashboard", headers=auth_headers)
        assert resp.status_code == 500

    def test_basic_dashboard_has_own_counts(self, client, auth_headers):
        """Basic dashboard contains own_total fields for VMs, courses, events."""
        resp = client.get(f"{API}/statistics/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "own_total" in data["vms"]
        assert "own_running" in data["vms"]
        assert "own_total" in data["courses"]
        assert "own_total" in data["events"]
        assert "own_running" in data["events"]
        assert "own_total" in data["connections"]
