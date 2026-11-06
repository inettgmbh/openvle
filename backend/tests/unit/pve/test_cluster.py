"""Tests for pve/cluster.py - ProxmoxCluster operations."""

import uuid
from unittest.mock import MagicMock

import pytest
from core.exceptions import ProxmoxConnectionError


class TestProxmoxClusterInit:
    def test_init_with_ssl_verify(self, monkeypatch):
        """When pve_verify_ssl=True, ProxmoxAPI is called with verify_ssl=True."""
        from core.config import Settings

        mock_settings = Settings()
        mock_settings.pve_verify_ssl = True
        mock_settings.pve_hostname = "test-pve.local"
        mock_settings.pve_user = "test@pve"
        mock_settings.pve_token_name = "tok"
        mock_settings.pve_token_value = "val"

        mock_pve_api = MagicMock()
        monkeypatch.setattr("pve.cluster.ProxmoxAPI", mock_pve_api)
        monkeypatch.setattr("pve.cluster.settings", mock_settings)

        from pve.cluster import ProxmoxCluster

        ProxmoxCluster()

        mock_pve_api.assert_called_once_with(
            "test-pve.local",
            user="test@pve",
            token_name="tok",
            token_value="val",
            verify_ssl=True,
        )

    def test_init_without_ssl_verify(self, monkeypatch):
        """When pve_verify_ssl=False, urllib3 warnings are disabled and verify_ssl=False."""
        from core.config import Settings

        mock_settings = Settings()
        mock_settings.pve_verify_ssl = False
        mock_settings.pve_hostname = "test-pve.local"
        mock_settings.pve_user = "test@pve"
        mock_settings.pve_token_name = "tok"
        mock_settings.pve_token_value = "val"

        mock_pve_api = MagicMock()
        mock_disable_warnings = MagicMock()
        monkeypatch.setattr("pve.cluster.ProxmoxAPI", mock_pve_api)
        monkeypatch.setattr("pve.cluster.settings", mock_settings)
        monkeypatch.setattr(
            "pve.cluster.urllib3.disable_warnings", mock_disable_warnings
        )

        from pve.cluster import ProxmoxCluster

        ProxmoxCluster()

        mock_disable_warnings.assert_called_once()
        mock_pve_api.assert_called_once_with(
            "test-pve.local",
            user="test@pve",
            token_name="tok",
            token_value="val",
            verify_ssl=False,
        )

    def test_init_connection_error(self, monkeypatch):
        """ConnectionError during init raises ProxmoxConnectionError."""
        import requests
        from core.config import Settings

        mock_settings = Settings()
        mock_settings.pve_verify_ssl = True

        monkeypatch.setattr("pve.cluster.settings", mock_settings)
        monkeypatch.setattr(
            "pve.cluster.ProxmoxAPI",
            MagicMock(
                side_effect=requests.exceptions.ConnectionError("refused")
            ),
        )

        from pve.cluster import ProxmoxCluster

        with pytest.raises(ProxmoxConnectionError):
            ProxmoxCluster()


class TestPveGetNode:
    def _make_cluster(self, monkeypatch, resource_list):
        """Helper to create a ProxmoxCluster with mocked resource_list."""
        mock_pve_api = MagicMock()
        mock_pve_api.return_value.cluster.resources.get.return_value = (
            resource_list
        )
        monkeypatch.setattr("pve.cluster.ProxmoxAPI", mock_pve_api)

        from core.config import Settings

        mock_settings = Settings()
        mock_settings.pve_verify_ssl = True
        monkeypatch.setattr("pve.cluster.settings", mock_settings)

        from pve.cluster import ProxmoxCluster

        cluster = ProxmoxCluster()
        # Override the proxmox attribute to use our controlled mock
        cluster.proxmox = mock_pve_api.return_value
        return cluster

    def test_pve_get_node_found(self, monkeypatch):
        """Returns correct node name when vmid matches."""
        resources = [
            {"vmid": 100, "node": "node1", "type": "qemu"},
            {"vmid": 200, "node": "node2", "type": "qemu"},
        ]
        cluster = self._make_cluster(monkeypatch, resources)

        result = cluster.pve_get_node(200)
        assert result == "node2"

    def test_pve_get_node_not_found(self, monkeypatch):
        """Returns None when vmid is not in resources."""
        resources = [
            {"vmid": 100, "node": "node1", "type": "qemu"},
        ]
        cluster = self._make_cluster(monkeypatch, resources)

        result = cluster.pve_get_node(999)
        assert result is None

    def test_pve_get_node_skips_items_without_vmid(self, monkeypatch):
        """Items without 'vmid' key are skipped without error."""
        resources = [
            {"type": "node", "node": "node1"},  # no vmid
            {"vmid": 100, "node": "node2", "type": "qemu"},
        ]
        cluster = self._make_cluster(monkeypatch, resources)

        result = cluster.pve_get_node(100)
        assert result == "node2"


class TestNextVmId:
    def _make_cluster(self, monkeypatch, nextid_values, validate_ok=True):
        """Helper to create a ProxmoxCluster with mocked nextid."""
        mock_proxmox = MagicMock()
        # nextid.get() returns first value, then subsequent values
        mock_proxmox.cluster.nextid.get = MagicMock(side_effect=nextid_values)
        mock_pve_api = MagicMock(return_value=mock_proxmox)
        monkeypatch.setattr("pve.cluster.ProxmoxAPI", mock_pve_api)

        from core.config import Settings

        mock_settings = Settings()
        mock_settings.pve_verify_ssl = True
        monkeypatch.setattr("pve.cluster.settings", mock_settings)

        from pve.cluster import ProxmoxCluster

        cluster = ProxmoxCluster()
        cluster.proxmox = mock_proxmox
        return cluster

    def test_next_vm_id_success(self, monkeypatch, db_session, system_user):
        """Returns next available VM ID when no conflicts exist."""
        # First call: get candidate; second call: validate candidate
        cluster = self._make_cluster(monkeypatch, ["100", "100"])

        result = cluster.next_vm_id(db_session)
        assert result == 100

    def test_next_vm_id_skips_reserved(
        self, monkeypatch, db_session, system_user
    ):
        """Skips IDs already used in the DB."""
        from datetime import datetime, timezone

        from models import VirtualMachine

        now = datetime.now(timezone.utc)
        vm = VirtualMachine(
            id=uuid.uuid4(),
            name="test-vm",
            proxmoxId=100,
            cpu=2,
            ram=4096,
            disk=32,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(vm)
        db_session.flush()

        # First call returns "100" (reserved), validation of 101 succeeds
        cluster = self._make_cluster(monkeypatch, ["100", "101"])

        result = cluster.next_vm_id(db_session)
        # Should skip 100 (in DB) and return 101
        assert result == 101


class TestGetFreeNode:
    def _make_cluster(self, monkeypatch, resource_list):
        """Helper to create a ProxmoxCluster with mocked resources."""
        mock_proxmox = MagicMock()
        mock_proxmox.cluster.resources.get.return_value = resource_list
        mock_pve_api = MagicMock(return_value=mock_proxmox)
        monkeypatch.setattr("pve.cluster.ProxmoxAPI", mock_pve_api)

        from core.config import Settings

        mock_settings = Settings()
        mock_settings.pve_verify_ssl = True
        monkeypatch.setattr("pve.cluster.settings", mock_settings)

        from pve.cluster import ProxmoxCluster

        cluster = ProxmoxCluster()
        cluster.proxmox = mock_proxmox
        return cluster

    def test_get_free_node_returns_best(self, monkeypatch):
        """Returns node with most free CPU."""
        resources = [
            {"node": "node1", "cgroup-mode": 2, "maxcpu": 16, "cpu": 10},
            {"node": "node2", "cgroup-mode": 2, "maxcpu": 32, "cpu": 5},
            {"node": "node3", "cgroup-mode": 2, "maxcpu": 8, "cpu": 1},
        ]
        cluster = self._make_cluster(monkeypatch, resources)

        result = cluster.get_free_node()
        # node2 has 27 free CPUs (32-5), node1 has 6, node3 has 7
        assert result == "node2"

    def test_get_free_node_single_node(self, monkeypatch):
        """Works correctly with a single node."""
        resources = [
            {"node": "solo-node", "cgroup-mode": 2, "maxcpu": 16, "cpu": 4},
        ]
        cluster = self._make_cluster(monkeypatch, resources)

        result = cluster.get_free_node()
        assert result == "solo-node"
