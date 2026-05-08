"""Tests for pve/pve_node_info.py - PVE node info periodic tasks."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from models import SubTask, Template, VirtualMachine


class TestCreatePveNodeInfo:
    def test_create_pve_node_info(self, monkeypatch):
        """Inserts a new PVE resource list document into MongoDB."""
        mock_collection = MagicMock()
        monkeypatch.setattr("pve.pve_node_info.mongodb", mock_collection)

        from pve.pve_node_info import create_pve_node_info

        vm_list = [{"vmid": 100, "node": "node1"}]
        template_list = [{"vmid": 200, "node": "node1"}]
        node_list = [{"node": "node1", "maxcpu": 16}]

        create_pve_node_info(vm_list, template_list, node_list)

        mock_collection.insert_one.assert_called_once()
        inserted = mock_collection.insert_one.call_args[0][0]
        assert inserted["name"] == "PVE resource list"
        assert inserted["qemu_vm_list"] == vm_list
        assert inserted["qemu_template_list"] == template_list
        assert inserted["node_list"] == node_list
        assert "updated_at" in inserted


class TestUpdatePveNodeInfo:
    def test_update_pve_node_info(self, monkeypatch):
        """Updates the existing MongoDB document with new resource data."""
        mock_collection = MagicMock()
        monkeypatch.setattr("pve.pve_node_info.mongodb", mock_collection)

        from pve.pve_node_info import update_pve_node_info

        vm_list = [{"vmid": 101, "node": "node2"}]
        template_list = []
        node_list = [{"node": "node2"}]

        update_pve_node_info("PVE resource list", vm_list, template_list, node_list)

        mock_collection.update_one.assert_called_once()
        args = mock_collection.update_one.call_args
        assert args[0][0] == {"name": "PVE resource list"}
        new_values = args[0][1]["$set"]
        assert new_values["qemu_vm_list"] == vm_list
        assert new_values["qemu_template_list"] == template_list
        assert new_values["node_list"] == node_list


class TestGetPveNodeInfo:
    def test_get_pve_node_info_found(self, monkeypatch):
        """Returns cached data when document exists in MongoDB."""
        expected = {
            "name": "PVE resource list",
            "qemu_vm_list": [{"vmid": 100}],
            "qemu_template_list": [],
            "node_list": [{"node": "node1"}],
        }
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = expected
        monkeypatch.setattr("pve.pve_node_info.mongodb", mock_collection)

        from pve.pve_node_info import get_pve_node_info

        result = get_pve_node_info("PVE resource list")
        assert result == expected
        mock_collection.find_one.assert_called_once_with({"name": "PVE resource list"})

    def test_get_pve_node_info_not_found(self, monkeypatch):
        """Returns empty dict when document does not exist."""
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = None
        monkeypatch.setattr("pve.pve_node_info.mongodb", mock_collection)

        from pve.pve_node_info import get_pve_node_info

        result = get_pve_node_info("nonexistent")
        assert result == {}


class TestProxmoxNodeInfoPeriodic:
    def _setup_periodic(
        self, monkeypatch, db_session, system_user, resource_list, mongo_data=None
    ):
        """Helper to set up mocks for proxmox_node_info_periodic."""
        now = datetime.now(timezone.utc)

        # Create a Task for the SubTask
        from models import Task

        task = Task(
            id=uuid.uuid4(),
            name="pve_periodic",
            status="queued",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(task)
        db_session.flush()

        # Create the sub_task that proxmox_node_info_periodic looks for
        sub_task = SubTask(
            id=uuid.uuid4(),
            job_id="proxmox_node_info_periodic",
            name="PVE Periodic",
            status="queued",
            object_type="System",
            object_id=str(uuid.uuid4()),
            action="pve_periodic",
            attempt="0",
            parent_task=task.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(sub_task)
        db_session.flush()

        # Mock SessionLocal to return our test session (patch in all modules that call it)
        monkeypatch.setattr("pve.pve_node_info.SessionLocal", lambda: db_session)
        import controllers.sub_tasks as sub_tasks_mod
        import core.mariadb as mariadb_mod

        monkeypatch.setattr(sub_tasks_mod, "SessionLocal", lambda: db_session)
        monkeypatch.setattr(mariadb_mod, "SessionLocal", lambda: db_session)

        # Also patch mail_automated which is called from worker_process_success
        import core.mail_automated as mail_auto_mod

        monkeypatch.setattr(mail_auto_mod, "SessionLocal", lambda: db_session)

        # Mock ProxmoxCluster
        mock_proxmox = MagicMock()
        mock_proxmox.cluster.resources.get.return_value = resource_list
        mock_cluster = MagicMock()
        mock_cluster.return_value.proxmox = mock_proxmox
        monkeypatch.setattr("pve.pve_node_info.ProxmoxCluster", mock_cluster)

        # Mock MongoDB collection
        mock_mongo_collection = MagicMock()
        mock_mongo_collection.find_one.return_value = mongo_data
        monkeypatch.setattr("pve.pve_node_info.mongodb", mock_mongo_collection)

        # Mock CRUDChangelog._create_for_changes to avoid side effects
        monkeypatch.setattr(
            "pve.pve_node_info.CRUDChangelog",
            lambda model: MagicMock(),
        )

        # Mock get_system_user
        monkeypatch.setattr(
            "pve.pve_node_info.get_system_user",
            lambda: system_user,
        )

        # Mock db_save to avoid commit issues
        monkeypatch.setattr("pve.pve_node_info.db_save", lambda db, obj: obj)

        return sub_task

    @pytest.mark.anyio
    async def test_proxmox_node_info_periodic_updates_vms(
        self, monkeypatch, db_session, system_user
    ):
        """Updates VM status and node in DB when PVE reports changes."""
        now = datetime.now(timezone.utc)

        # Create a VM in the DB
        vm = VirtualMachine(
            id=uuid.uuid4(),
            name="test-vm",
            proxmoxId=100,
            status="running",
            proxmoxNode="node1",
            cpu=2,
            ram=4096,
            disk=32,
            ipv4="10.0.0.1",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(vm)
        db_session.flush()

        # PVE reports the VM moved to node2 with same status
        resource_list = [
            {"vmid": 100, "node": "node2", "status": "running", "type": "qemu"},
        ]
        mongo_data = {
            "name": "PVE resource list",
            "qemu_vm_list": [{"vmid": 100, "node": "node1", "status": "running"}],
            "qemu_template_list": [],
            "node_list": [],
        }

        self._setup_periodic(
            monkeypatch, db_session, system_user, resource_list, mongo_data
        )

        from pve.pve_node_info import proxmox_node_info_periodic

        await proxmox_node_info_periodic()

        # Refresh VM to see updates
        db_session.expire_all()
        updated_vm = db_session.get(VirtualMachine, vm.id)
        assert updated_vm.proxmoxNode == "node2"

    @pytest.mark.anyio
    async def test_proxmox_node_info_periodic_updates_templates(
        self, monkeypatch, db_session, system_user
    ):
        """Updates Template node when PVE reports a node change."""
        now = datetime.now(timezone.utc)

        tpl = Template(
            id=uuid.uuid4(),
            name="test-template",
            proxmoxId=500,
            status="cloning",
            proxmoxNode="node1",
            cpu=2,
            ram=4096,
            disk=32,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(tpl)
        db_session.flush()

        resource_list = [
            {
                "vmid": 500,
                "node": "node3",
                "status": "stopped",
                "type": "qemu",
                "template": 1,
            },
        ]
        mongo_data = {
            "name": "PVE resource list",
            "qemu_vm_list": [],
            "qemu_template_list": [{"vmid": 500, "node": "node1"}],
            "node_list": [],
        }

        self._setup_periodic(
            monkeypatch, db_session, system_user, resource_list, mongo_data
        )

        from pve.pve_node_info import proxmox_node_info_periodic

        await proxmox_node_info_periodic()

        db_session.expire_all()
        updated_tpl = db_session.get(Template, tpl.id)
        # Template was in "cloning" state, should now be "available"
        assert updated_tpl.status == "available"
        assert updated_tpl.proxmoxNode == "node3"

    @pytest.mark.anyio
    async def test_proxmox_node_info_periodic_handles_no_resources(
        self, monkeypatch, db_session, system_user
    ):
        """Empty resource list from PVE does not cause errors."""
        resource_list = []
        mongo_data = {
            "name": "PVE resource list",
            "qemu_vm_list": [],
            "qemu_template_list": [],
            "node_list": [],
        }

        self._setup_periodic(
            monkeypatch, db_session, system_user, resource_list, mongo_data
        )

        from pve.pve_node_info import proxmox_node_info_periodic

        # Should complete without raising
        await proxmox_node_info_periodic()
