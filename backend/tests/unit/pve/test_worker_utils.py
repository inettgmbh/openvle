"""Tests for pve/worker_utils.py - Worker utility functions."""

from unittest.mock import MagicMock


class TestFormatPveExceptionForUser:
    def test_format_pve_exception_resource_exception(self):
        """ResourceException with status_code and message is formatted correctly."""
        from proxmoxer.core import ResourceException

        exc = ResourceException(500, "Internal Server Error", "node unreachable")
        from pve.worker_utils import format_pve_exception_for_user

        status, msg = format_pve_exception_for_user(exc, prefix="Clone failed")

        assert status == 500
        assert "Clone failed" in msg
        assert "500" in msg

    def test_format_pve_exception_generic(self):
        """Generic Exception returns 500 and message."""
        from pve.worker_utils import format_pve_exception_for_user

        exc = Exception("something broke")
        status, msg = format_pve_exception_for_user(exc, prefix="VM operation")

        assert status == 500
        assert "VM operation" in msg
        assert "something broke" in msg

    def test_format_pve_exception_with_response(self):
        """ResourceException with response attribute includes PVE Details."""
        from proxmoxer.core import ResourceException

        exc = ResourceException(503, "Service Unavailable", "try again later")
        exc.response = "Cluster not quorate"

        from pve.worker_utils import format_pve_exception_for_user

        status, msg = format_pve_exception_for_user(exc)

        assert status == 503
        assert "PVE Details:" in msg
        assert "Cluster not quorate" in msg

    def test_format_pve_exception_default_prefix(self):
        """Without custom prefix, uses default 'PVE operation failed'."""
        from pve.worker_utils import format_pve_exception_for_user

        exc = Exception("timeout")
        status, msg = format_pve_exception_for_user(exc)

        assert status == 500
        assert "PVE operation failed" in msg


class TestPveTaskGet:
    def test_pve_task_get_returns_dict(self, monkeypatch):
        """Returns task status dict once PVE reports completion."""
        expected_status = {
            "status": "stopped",
            "exitstatus": "OK",
            "type": "qmclone",
        }

        mock_cluster_instance = MagicMock()
        mock_cluster_instance.proxmox.nodes.return_value.tasks.return_value.status.get.return_value = expected_status
        mock_cluster_cls = MagicMock(return_value=mock_cluster_instance)
        monkeypatch.setattr("pve.worker_utils.ProxmoxCluster", mock_cluster_cls)
        monkeypatch.setattr("pve.worker_utils.time.sleep", lambda x: None)

        from pve.worker_utils import pve_task_get

        upid = "UPID:node1:00123456:0ABCDEF0:6789ABCD:qmclone:100:user@pve:"
        result = pve_task_get(upid)

        assert result == expected_status
        mock_cluster_instance.proxmox.nodes.assert_called_with("node1")

    def test_pve_task_get_extracts_node_from_upid(self, monkeypatch):
        """Verifies node name is correctly extracted from UPID string."""
        expected_status = {"status": "stopped", "exitstatus": "OK"}

        mock_cluster_instance = MagicMock()
        mock_cluster_instance.proxmox.nodes.return_value.tasks.return_value.status.get.return_value = expected_status
        mock_cluster_cls = MagicMock(return_value=mock_cluster_instance)
        monkeypatch.setattr("pve.worker_utils.ProxmoxCluster", mock_cluster_cls)
        monkeypatch.setattr("pve.worker_utils.time.sleep", lambda x: None)

        from pve.worker_utils import pve_task_get

        upid = "UPID:my-node-02:00123456:0ABCDEF0:6789ABCD:qmclone:200:user@pve:"
        pve_task_get(upid)

        # Verify the correct node name was extracted
        mock_cluster_instance.proxmox.nodes.assert_called_with("my-node-02")
