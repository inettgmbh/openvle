"""Integration tests for /v{x}/proxmox/ endpoints.

All Proxmox endpoints contact a real PVE cluster, so happy-path tests
are skipped.  We only verify authentication (401) and permission (403)
guards here.
"""

from tests.integration.conftest import API

FAKE_NODE = "fake-node"
FAKE_PROXMOX_ID = 9999


# -- Cluster endpoints ------------------------------------------------


class TestClusterLogs:
    """GET /proxmox/cluster/logs -- PVE cluster logs."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/proxmox/cluster/logs")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        resp = client.get(f"{API}/proxmox/cluster/logs", headers=auth_headers)
        assert resp.status_code == 403


class TestClusterResources:
    """GET /proxmox/cluster/resources -- PVE cluster resources."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/proxmox/cluster/resources")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        resp = client.get(f"{API}/proxmox/cluster/resources", headers=auth_headers)
        assert resp.status_code == 403


class TestClusterStatus:
    """GET /proxmox/cluster/status -- PVE cluster status."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/proxmox/cluster/status")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        resp = client.get(f"{API}/proxmox/cluster/status", headers=auth_headers)
        assert resp.status_code == 403


class TestClusterTasks:
    """GET /proxmox/cluster/tasks -- PVE cluster tasks."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/proxmox/cluster/tasks")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        resp = client.get(f"{API}/proxmox/cluster/tasks", headers=auth_headers)
        assert resp.status_code == 403


class TestClusterCounts:
    """GET /proxmox/cluster/counts -- PVE cluster VM counts."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/proxmox/cluster/counts")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        resp = client.get(f"{API}/proxmox/cluster/counts", headers=auth_headers)
        assert resp.status_code == 403


# -- Node endpoints ----------------------------------------------------


class TestGetNodes:
    """GET /proxmox/nodes -- list all PVE nodes."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/proxmox/nodes")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        resp = client.get(f"{API}/proxmox/nodes", headers=auth_headers)
        assert resp.status_code == 403


class TestGetNodeRrd:
    """GET /proxmox/nodes/{node}/rrd -- node RRD graphic (PNG)."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/proxmox/nodes/{FAKE_NODE}/rrd")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        resp = client.get(
            f"{API}/proxmox/nodes/{FAKE_NODE}/rrd",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestGetNodeRrdData:
    """GET /proxmox/nodes/{node}/rrddata -- node RRD statistic data."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/proxmox/nodes/{FAKE_NODE}/rrddata")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        resp = client.get(
            f"{API}/proxmox/nodes/{FAKE_NODE}/rrddata",
            headers=auth_headers,
        )
        assert resp.status_code == 403


# -- Template load endpoints -------------------------------------------


class TestGetTemplateLoad:
    """GET /proxmox/templates/load -- get PVE template config."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(
            f"{API}/proxmox/templates/load",
            params={"proxmox_id": FAKE_PROXMOX_ID},
        )
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        resp = client.get(
            f"{API}/proxmox/templates/load",
            params={"proxmox_id": FAKE_PROXMOX_ID},
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestPostTemplateLoad:
    """POST /proxmox/templates/load -- create template from PVE."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.post(
            f"{API}/proxmox/templates/load",
            params={"proxmox_id": FAKE_PROXMOX_ID},
        )
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        resp = client.post(
            f"{API}/proxmox/templates/load",
            params={"proxmox_id": FAKE_PROXMOX_ID},
            headers=auth_headers,
        )
        assert resp.status_code == 403
