"""Tests for controllers/virtual_machines.py - CRUDVirtualMachine operations."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from controllers.virtual_machines import CRUDVirtualMachine
from core.exceptions import (
    BadRequestError,
    BulkActionRequirementMissing,
    BulkObjectNotFound,
    OperationDependencyMissing,
    ProtectedObjectError,
)
from models import (
    Application,
    Changelog,
    ObjectPermission,
    SubTask,
    Task,
    Template,
    VirtualMachine,
    Vendor,
)
from schemas.virtual_machines import (
    VirtualMachineCreate,
    VirtualMachineIdList,
    VirtualMachineUpdate,
)
from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def sample_vendor_vm(db_session, system_user):
    now = datetime.now(timezone.utc)
    vendor = Vendor(
        id=uuid.uuid4(),
        name="VM Vendor",
        description="Vendor for VM tests",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


@pytest.fixture()
def sample_app_vm(db_session, system_user, sample_vendor_vm):
    now = datetime.now(timezone.utc)
    app = Application(
        id=uuid.uuid4(),
        key="vm-app",
        name="VM App",
        vendor=sample_vendor_vm.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(app)
    db_session.flush()
    return app


@pytest.fixture()
def source_template(db_session, system_user):
    """A template to clone VMs from."""
    now = datetime.now(timezone.utc)
    tpl = Template(
        id=uuid.uuid4(),
        name="source-tpl",
        status="available",
        proxmoxId=100,
        proxmoxNode="pve-node-1",
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
    return tpl


@pytest.fixture()
def sample_vm(db_session, system_user, source_template):
    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name="vm-test-01",
        status="running",
        proxmoxId=200,
        proxmoxNode="pve-node-1",
        cpu=2,
        ram=4096,
        disk=32,
        template=source_template.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vm)
    db_session.flush()
    return vm


@pytest.fixture()
def stopped_vm(db_session, system_user, source_template):
    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name="vm-stopped-01",
        status="stopped",
        proxmoxId=201,
        proxmoxNode="pve-node-1",
        cpu=2,
        ram=4096,
        disk=32,
        template=source_template.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vm)
    db_session.flush()
    return vm


@pytest.fixture()
def protected_vm(db_session, system_user, source_template):
    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name="vm-protected",
        status="running",
        proxmoxId=202,
        proxmoxNode="pve-node-1",
        cpu=2,
        ram=4096,
        disk=32,
        template=source_template.id,
        prevent_delete=True,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vm)
    db_session.flush()
    return vm


class TestCRUDVirtualMachineGetByName:
    def test_found(self, db_session, sample_vm):
        crud = CRUDVirtualMachine()
        result = crud.get_by_name(db_session, name="vm-test-01")
        assert result is not None
        assert result.id == sample_vm.id

    def test_not_found(self, db_session, system_user):
        crud = CRUDVirtualMachine()
        result = crud.get_by_name(db_session, name="nonexistent")
        assert result is None


class TestCRUDVirtualMachineUpdate:
    def test_update_cpu(self, db_session, active_user, mock_redis_queues, sample_vm):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        obj_in = VirtualMachineUpdate(cpu=4)
        result = crud.update(sample_vm.id, db_session, request, obj_in=obj_in)
        assert result.cpu == 4

    def test_update_creates_task(
        self, db_session, active_user, mock_redis_queues, sample_vm
    ):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        obj_in = VirtualMachineUpdate(ram=8192)
        crud.update(sample_vm.id, db_session, request, obj_in=obj_in)

        tasks = db_session.query(Task).all()
        assert any("Update VirtualMachine" in t.name for t in tasks)

    def test_update_restart_on_cpu_change(
        self, db_session, active_user, mock_redis_queues, sample_vm
    ):
        """When CPU changes and restart_vm is True, status becomes Rebooting."""
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        obj_in = VirtualMachineUpdate(cpu=8, restart_vm=True)
        result = crud.update(sample_vm.id, db_session, request, obj_in=obj_in)
        assert result.status == "Rebooting"

    def test_update_no_restart_without_cpu_ram_change(
        self, db_session, active_user, mock_redis_queues, sample_vm
    ):
        """restart_vm=True is ignored if CPU/RAM didn't change."""
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        obj_in = VirtualMachineUpdate(
            description="Updated description", restart_vm=True
        )
        result = crud.update(sample_vm.id, db_session, request, obj_in=obj_in)
        assert result.status != "Rebooting"


class TestCRUDVirtualMachineUpdateApps:
    def test_update_apps(self, db_session, active_user, sample_vm, sample_app_vm):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        result = crud.update_apps(
            sample_vm.id,
            db_session,
            request,
            obj_in={"apps": [{"key": "vm-app"}]},
        )
        assert len(result.apps) == 1
        assert result.apps[0].key == "vm-app"

    def test_update_apps_invalid_key_raises(self, db_session, active_user, sample_vm):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        from core.exceptions import ObjectNotFound

        with pytest.raises(ObjectNotFound):
            crud.update_apps(
                sample_vm.id,
                db_session,
                request,
                obj_in={"apps": [{"key": "nonexistent-app"}]},
            )


class TestCRUDVirtualMachineDelete:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_delete_sets_status_deleting(
        self, mock_cluster, db_session, active_user, mock_redis_queues, sample_vm
    ):
        mock_cluster.return_value.pve_get_node.return_value = "pve-node-1"
        mock_cluster.return_value.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "protection": 0
        }
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        crud.delete(db_session, request, id=sample_vm.id)

        db_session.refresh(sample_vm)
        assert sample_vm.status == "deleting"

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_delete_creates_task_chain(
        self, mock_cluster, db_session, active_user, mock_redis_queues, sample_vm
    ):
        mock_cluster.return_value.pve_get_node.return_value = "pve-node-1"
        mock_cluster.return_value.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "protection": 0
        }
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        crud.delete(db_session, request, id=sample_vm.id)

        tasks = db_session.query(Task).all()
        assert any("Delete VirtualMachine" in t.name for t in tasks)

        subtasks = db_session.query(SubTask).all()
        actions = [st.action for st in subtasks]
        assert "ha_remove" in actions
        assert "vm_stop" in actions
        assert "vm_delete" in actions

    def test_delete_protected_raises(
        self, db_session, active_user, mock_redis_queues, protected_vm
    ):
        crud = CRUDVirtualMachine(db=db_session, id=protected_vm.id)
        request = create_mock_request(active_user)
        with pytest.raises(ProtectedObjectError):
            crud.delete(db_session, request, id=protected_vm.id)

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_delete_proceeds_when_pve_config_raises_resource_exception(
        self, mock_cluster, db_session, active_user, mock_redis_queues, sample_vm
    ):
        """VM not found on PVE during protection check — deletion still proceeds."""
        from proxmoxer.core import ResourceException

        mock_cluster.return_value.pve_get_node.return_value = "pve-node-1"
        mock_cluster.return_value.proxmox.nodes.return_value.qemu.return_value.config.get.side_effect = ResourceException(
            501, "Not Implemented", ""
        )
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        crud.delete(db_session, request, id=sample_vm.id)

        db_session.refresh(sample_vm)
        assert sample_vm.status == "deleting"

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_delete_no_proxmox_id_proceeds(
        self, mock_cluster, db_session, active_user, mock_redis_queues, system_user
    ):
        """VM with no proxmoxId skips PVE protection check and proceeds."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        from models import VirtualMachine

        vm = VirtualMachine(
            id=uuid.uuid4(),
            name="broken-vm",
            proxmoxId=None,
            cpu=2,
            ram=4096,
            disk=32,
            status="stopped",
            prevent_delete=False,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(vm)
        db_session.flush()

        crud = CRUDVirtualMachine(db=db_session, id=vm.id)
        request = create_mock_request(active_user)
        crud.delete(db_session, request, id=vm.id)

        db_session.refresh(vm)
        assert vm.status == "deleting"
        mock_cluster.return_value.proxmox.nodes.return_value.qemu.return_value.config.get.assert_not_called()


class TestCRUDVirtualMachineActionsStart:
    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_start_sets_status_starting(
        self, mock_periodic, db_session, active_user, mock_redis_queues, stopped_vm
    ):
        crud = CRUDVirtualMachine(db=db_session, id=stopped_vm.id)
        request = create_mock_request(active_user)
        result = crud.actions_start(db_session, request, id=stopped_vm.id)
        assert result.status == "starting"

    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_start_creates_changelog(
        self, mock_periodic, db_session, active_user, mock_redis_queues, stopped_vm
    ):
        crud = CRUDVirtualMachine(db=db_session, id=stopped_vm.id)
        request = create_mock_request(active_user)
        crud.actions_start(db_session, request, id=stopped_vm.id)

        changelogs = (
            db_session.query(Changelog)
            .filter(Changelog.objectId == stopped_vm.id)
            .all()
        )
        assert len(changelogs) >= 1

    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_start_already_running_raises(
        self, mock_periodic, db_session, active_user, mock_redis_queues, sample_vm
    ):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        with pytest.raises(BadRequestError):
            crud.actions_start(db_session, request, id=sample_vm.id)


class TestCRUDVirtualMachineActionsStop:
    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_stop_sets_status_stopping(
        self, mock_periodic, db_session, active_user, mock_redis_queues, sample_vm
    ):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        result = crud.actions_stop(db_session, request, id=sample_vm.id)
        assert result.status == "stopping"

    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_stop_already_stopped_raises(
        self, mock_periodic, db_session, active_user, mock_redis_queues, stopped_vm
    ):
        crud = CRUDVirtualMachine(db=db_session, id=stopped_vm.id)
        request = create_mock_request(active_user)
        with pytest.raises(BadRequestError):
            crud.actions_stop(db_session, request, id=stopped_vm.id)


class TestCRUDVirtualMachineBulkStart:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_start(
        self, mock_pve, db_session, active_user, mock_redis_queues, stopped_vm
    ):
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(stopped_vm.id)])
        result = crud.bulk_start(db_session, request, obj_in)
        assert result["enqueued"] == 1
        assert len(result["skipped"]) == 0

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_start_skips_running(
        self, mock_pve, db_session, active_user, mock_redis_queues, sample_vm
    ):
        """Running VMs are skipped and all-running raises."""
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(sample_vm.id)])
        with pytest.raises(BulkActionRequirementMissing):
            crud.bulk_start(db_session, request, obj_in)

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_start_nonexistent_raises(
        self, mock_pve, db_session, active_user, mock_redis_queues
    ):
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        fake_id = str(uuid.uuid4())
        obj_in = VirtualMachineIdList(vms=[fake_id])
        with pytest.raises(BulkObjectNotFound):
            crud.bulk_start(db_session, request, obj_in)


class TestCRUDVirtualMachineBulkStop:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_stop(
        self, mock_pve, db_session, active_user, mock_redis_queues, sample_vm
    ):
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(sample_vm.id)])
        result = crud.bulk_stop(db_session, request, obj_in)
        assert result["enqueued"] == 1

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_stop_skips_stopped(
        self, mock_pve, db_session, active_user, mock_redis_queues, stopped_vm
    ):
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(stopped_vm.id)])
        with pytest.raises(BulkActionRequirementMissing):
            crud.bulk_stop(db_session, request, obj_in)


class TestCRUDVirtualMachineCreateFromTemplate:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_create_from_template(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        mock_redis_queues,
        source_template,
    ):
        mock_pve = MagicMock()
        mock_pve.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "ostype": "l26",
            "tags": "",
        }
        mock_pve.pve_get_node.return_value = "pve-node-1"
        mock_pve_cls.return_value = mock_pve

        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineCreate(
            name="new-vm",
            cpu=2,
            ram=2048,
            template=str(source_template.id),
        )
        result = crud.create_from_template(db_session, request, obj_in=obj_in)
        assert result.status == "queued"
        assert result.template == source_template.id

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_create_creates_object_permission(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        mock_redis_queues,
        source_template,
    ):
        mock_pve = MagicMock()
        mock_pve.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "ostype": "l26",
            "tags": "",
        }
        mock_pve.pve_get_node.return_value = "pve-node-1"
        mock_pve_cls.return_value = mock_pve

        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineCreate(
            name="new-vm-perm",
            cpu=2,
            ram=2048,
            template=str(source_template.id),
        )
        result = crud.create_from_template(db_session, request, obj_in=obj_in)

        perms = (
            db_session.query(ObjectPermission)
            .filter(
                ObjectPermission.object_id == result.id,
                ObjectPermission.object_type == "VirtualMachine",
            )
            .all()
        )
        assert len(perms) >= 1
        assert any(p.permission_key == "object_full" for p in perms)


# ---------------------------------------------------------------------------
# Fixtures for additional tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def paused_vm(db_session, system_user, source_template):
    """A VM in paused state."""
    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name="vm-paused-01",
        status="paused",
        proxmoxId=203,
        proxmoxNode="pve-node-1",
        cpu=2,
        ram=4096,
        disk=32,
        template=source_template.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vm)
    db_session.flush()
    return vm


@pytest.fixture()
def sample_event(db_session, system_user, event_statuses, sample_course):
    """Create a sample event for create_from_template_event tests."""
    from models import Event

    now = datetime.now(timezone.utc)
    event = Event(
        id=uuid.uuid4(),
        name="Test Event",
        slug="tst-evt",
        description="An event for VM tests",
        dateStart=now.date(),
        guacamole=False,
        status=event_statuses["Geplant"].id,
        course=sample_course.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(event)
    db_session.flush()
    return event


# ---------------------------------------------------------------------------
# create_from_template_event
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineCreateFromTemplateEvent:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_create_from_template_event_returns_vm(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        mock_redis_queues,
        source_template,
        sample_event,
        role_teacher,
    ):
        from schemas.virtual_machines import VirtualMachineEventCreate

        mock_pve = MagicMock()
        mock_pve.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "ostype": "l26",
            "tags": "",
        }
        mock_pve.pve_get_node.return_value = "pve-node-1"
        mock_pve_cls.return_value = mock_pve

        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineEventCreate(
            name="event-vm",
            cpu=2,
            ram=2048,
            template=str(source_template.id),
            event=str(sample_event.id),
            user=str(active_user.id),
        )
        result = crud.create_from_template_event(db_session, request, obj_in=obj_in)
        assert "VirtualMachine" in result
        vm = result["VirtualMachine"]
        assert vm.status == "queued"
        assert vm.event == sample_event.id

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_create_from_template_event_creates_task(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        mock_redis_queues,
        source_template,
        sample_event,
        role_teacher,
    ):
        from schemas.virtual_machines import VirtualMachineEventCreate

        mock_pve = MagicMock()
        mock_pve.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "ostype": "l26",
            "tags": "",
        }
        mock_pve.pve_get_node.return_value = "pve-node-1"
        mock_pve_cls.return_value = mock_pve

        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineEventCreate(
            name="event-vm-task",
            cpu=2,
            ram=2048,
            template=str(source_template.id),
            event=str(sample_event.id),
            user=str(active_user.id),
        )
        crud.create_from_template_event(db_session, request, obj_in=obj_in)

        tasks = db_session.query(Task).all()
        assert any("Create VirtualMachine" in t.name for t in tasks)

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_create_from_template_event_creates_object_permission(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        mock_redis_queues,
        source_template,
        sample_event,
        role_teacher,
    ):
        from schemas.virtual_machines import VirtualMachineEventCreate

        mock_pve = MagicMock()
        mock_pve.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "ostype": "l26",
            "tags": "",
        }
        mock_pve.pve_get_node.return_value = "pve-node-1"
        mock_pve_cls.return_value = mock_pve

        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineEventCreate(
            name="event-vm-perm",
            cpu=2,
            ram=2048,
            template=str(source_template.id),
            event=str(sample_event.id),
            user=str(active_user.id),
        )
        result = crud.create_from_template_event(db_session, request, obj_in=obj_in)
        vm = result["VirtualMachine"]

        perms = (
            db_session.query(ObjectPermission)
            .filter(
                ObjectPermission.object_id == vm.id,
                ObjectPermission.object_type == "VirtualMachine",
            )
            .all()
        )
        assert len(perms) >= 1


# ---------------------------------------------------------------------------
# actions_clone
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineActionsClone:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_clone_sets_status_queued(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        mock_redis_queues,
        stopped_vm,
    ):
        from schemas.virtual_machines import VirtualMachineClone

        mock_pve = MagicMock()
        mock_pve.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "ostype": "l26",
            "tags": "",
        }
        mock_pve.pve_get_node.return_value = "pve-node-1"
        mock_pve_cls.return_value = mock_pve

        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineClone(
            name="cloned-vm",
            description="Cloned VM",
            cpu=2,
            ram=2048,
        )
        result = crud.actions_clone(stopped_vm.id, db_session, request, obj_in=obj_in)
        assert result.status == "queued"

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_clone_creates_task_and_subtasks(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        mock_redis_queues,
        stopped_vm,
    ):
        from schemas.virtual_machines import VirtualMachineClone

        mock_pve = MagicMock()
        mock_pve.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "ostype": "l26",
            "tags": "",
        }
        mock_pve.pve_get_node.return_value = "pve-node-1"
        mock_pve_cls.return_value = mock_pve

        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineClone(
            name="cloned-vm-task",
            description="Cloned VM",
            cpu=2,
            ram=2048,
        )
        crud.actions_clone(stopped_vm.id, db_session, request, obj_in=obj_in)

        tasks = db_session.query(Task).all()
        assert any("Create VirtualMachine" in t.name for t in tasks)

        subtasks = db_session.query(SubTask).all()
        actions = [st.action for st in subtasks]
        assert "vm_clone" in actions

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_clone_running_vm_raises(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        """Only stopped VMs may be cloned."""
        from schemas.virtual_machines import VirtualMachineClone

        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineClone(
            name="should-fail-clone",
            description="Fail",
            cpu=2,
            ram=2048,
        )
        with pytest.raises(OperationDependencyMissing):
            crud.actions_clone(sample_vm.id, db_session, request, obj_in=obj_in)

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_clone_vm_no_proxmox_id_raises(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        system_user,
        mock_redis_queues,
        source_template,
    ):
        """VMs without a proxmoxId cannot be cloned."""
        from schemas.virtual_machines import VirtualMachineClone

        now = datetime.now(timezone.utc)
        vm_no_pve = VirtualMachine(
            id=uuid.uuid4(),
            name="vm-no-pve",
            status="stopped",
            proxmoxId=None,
            proxmoxNode="pve-node-1",
            cpu=2,
            ram=4096,
            disk=32,
            template=source_template.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(vm_no_pve)
        db_session.flush()

        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineClone(
            name="clone-no-pve",
            description="Fail",
            cpu=2,
            ram=2048,
        )
        with pytest.raises(OperationDependencyMissing):
            crud.actions_clone(vm_no_pve.id, db_session, request, obj_in=obj_in)


# ---------------------------------------------------------------------------
# actions_migrate
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineActionsMigrate:
    @patch(
        "controllers.virtual_machines.get_pve_node_info",
        return_value={"node_list": [{"node": "pve-node-2"}]},
    )
    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_migrate_sets_status_migrating(
        self,
        mock_periodic,
        mock_node_info,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        from schemas.virtual_machines import VirtualMachineMigrate

        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        obj_in = VirtualMachineMigrate(targetNode="pve-node-2")
        result = crud.actions_migrate(sample_vm.id, db_session, request, obj_in=obj_in)
        assert result.status == "migrating"

    @patch(
        "controllers.virtual_machines.get_pve_node_info",
        return_value={"node_list": [{"node": "pve-node-2"}]},
    )
    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_migrate_creates_changelog(
        self,
        mock_periodic,
        mock_node_info,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        from schemas.virtual_machines import VirtualMachineMigrate

        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        obj_in = VirtualMachineMigrate(targetNode="pve-node-2")
        crud.actions_migrate(sample_vm.id, db_session, request, obj_in=obj_in)

        changelogs = (
            db_session.query(Changelog).filter(Changelog.objectId == sample_vm.id).all()
        )
        assert len(changelogs) >= 1

    @patch(
        "controllers.virtual_machines.get_pve_node_info",
        return_value={"node_list": [{"node": "pve-node-1"}, {"node": "pve-node-2"}]},
    )
    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_migrate_same_node_raises(
        self,
        mock_periodic,
        mock_node_info,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        """Migrating to the same node should raise BadRequestError."""
        from schemas.virtual_machines import VirtualMachineMigrate

        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        # sample_vm is on pve-node-1
        obj_in = VirtualMachineMigrate(targetNode="pve-node-1")
        with pytest.raises(BadRequestError):
            crud.actions_migrate(sample_vm.id, db_session, request, obj_in=obj_in)

    @patch(
        "controllers.virtual_machines.get_pve_node_info",
        return_value={"node_list": [{"node": "pve-node-2"}]},
    )
    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_migrate_invalid_node_raises(
        self,
        mock_periodic,
        mock_node_info,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        """Migrating to a non-existent node should raise ProxmoxResourceNotFound."""
        from core.exceptions import ProxmoxResourceNotFound
        from schemas.virtual_machines import VirtualMachineMigrate

        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        obj_in = VirtualMachineMigrate(targetNode="nonexistent-node")
        with pytest.raises(ProxmoxResourceNotFound):
            crud.actions_migrate(sample_vm.id, db_session, request, obj_in=obj_in)


# ---------------------------------------------------------------------------
# actions_ha_get
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineActionsHaGet:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_ha_get_returns_state(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        sample_vm,
    ):
        mock_pve = MagicMock()
        mock_pve.proxmox.cluster.ha.resources.return_value.get.return_value = {
            "type": "vm",
            "state": "started",
            "max_relocate": 5,
            "max_restart": 5,
            "digest": "abc123",
        }
        mock_pve_cls.return_value = mock_pve

        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        result = crud.actions_ha_get(sample_vm.id, db_session, request)
        assert result["state"] == "started"
        assert result["type"] == "vm"

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_ha_get_resource_exception_returns_ignored(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        sample_vm,
    ):
        """When HA resource not found, return ignored state."""
        from proxmoxer.core import ResourceException

        mock_pve = MagicMock()
        mock_pve.proxmox.cluster.ha.resources.return_value.get.side_effect = (
            ResourceException(status_code=404, status_message="Not Found", content="")
        )
        mock_pve_cls.return_value = mock_pve

        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        result = crud.actions_ha_get(sample_vm.id, db_session, request)
        assert result["state"] == "ignored"
        assert result["max_relocate"] == 0
        assert result["max_restart"] == 0


# ---------------------------------------------------------------------------
# actions_ha_add
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineActionsHaAdd:
    def test_ha_add_creates_task(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        from schemas.virtual_machines import VirtualMachineHaAdd

        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        obj_in = VirtualMachineHaAdd(
            ha_state="started", ha_max_restart=5, ha_max_relocate=5
        )
        result = crud.actions_ha_add(sample_vm.id, db_session, request, obj_in=obj_in)
        assert result is not None

        tasks = db_session.query(Task).all()
        assert any("Add VirtualMachine to HA" in t.name for t in tasks)

    def test_ha_add_creates_subtask(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        from schemas.virtual_machines import VirtualMachineHaAdd

        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        obj_in = VirtualMachineHaAdd(
            ha_state="started", ha_max_restart=3, ha_max_relocate=3
        )
        crud.actions_ha_add(sample_vm.id, db_session, request, obj_in=obj_in)

        subtasks = db_session.query(SubTask).all()
        actions = [st.action for st in subtasks]
        assert "vm_ha_add" in actions


# ---------------------------------------------------------------------------
# actions_ha_remove
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineActionsHaRemove:
    def test_ha_remove_creates_task(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        result = crud.actions_ha_remove(db_session, request, id=sample_vm.id)
        assert result is not None

        tasks = db_session.query(Task).all()
        assert any("Remove VirtualMachine from cluster HA" in t.name for t in tasks)

    def test_ha_remove_creates_subtask(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        crud.actions_ha_remove(db_session, request, id=sample_vm.id)

        subtasks = db_session.query(SubTask).all()
        actions = [st.action for st in subtasks]
        assert "ha_remove" in actions


# ---------------------------------------------------------------------------
# actions_pause
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineActionsPause:
    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_pause_sets_status_pausing(
        self,
        mock_periodic,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        result = crud.actions_pause(db_session, request, id=sample_vm.id)
        assert result.status == "pausing"

    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_pause_creates_changelog(
        self,
        mock_periodic,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        crud.actions_pause(db_session, request, id=sample_vm.id)

        changelogs = (
            db_session.query(Changelog).filter(Changelog.objectId == sample_vm.id).all()
        )
        assert len(changelogs) >= 1

    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_pause_already_paused_raises(
        self,
        mock_periodic,
        db_session,
        active_user,
        mock_redis_queues,
        paused_vm,
    ):
        crud = CRUDVirtualMachine(db=db_session, id=paused_vm.id)
        request = create_mock_request(active_user)
        with pytest.raises(BadRequestError):
            crud.actions_pause(db_session, request, id=paused_vm.id)


# ---------------------------------------------------------------------------
# actions_reset
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineActionsReset:
    def test_reset_sets_status_resetting(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        result = crud.actions_reset(db_session, request, id=sample_vm.id)
        assert result.status == "resetting"

    def test_reset_creates_changelog(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        crud.actions_reset(db_session, request, id=sample_vm.id)

        changelogs = (
            db_session.query(Changelog).filter(Changelog.objectId == sample_vm.id).all()
        )
        assert len(changelogs) >= 1

    def test_reset_stopped_vm_raises(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        stopped_vm,
    ):
        """Only running VMs can be reset."""
        crud = CRUDVirtualMachine(db=db_session, id=stopped_vm.id)
        request = create_mock_request(active_user)
        with pytest.raises(BadRequestError):
            crud.actions_reset(db_session, request, id=stopped_vm.id)


# ---------------------------------------------------------------------------
# actions_reboot
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineActionsReboot:
    def test_reboot_sets_status_rebooting(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        result = crud.actions_reboot(db_session, request, id=sample_vm.id)
        assert result.status == "rebooting"

    def test_reboot_creates_changelog(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        crud.actions_reboot(db_session, request, id=sample_vm.id)

        changelogs = (
            db_session.query(Changelog).filter(Changelog.objectId == sample_vm.id).all()
        )
        assert len(changelogs) >= 1

    def test_reboot_stopped_vm_raises(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        stopped_vm,
    ):
        """Only running VMs can be rebooted."""
        crud = CRUDVirtualMachine(db=db_session, id=stopped_vm.id)
        request = create_mock_request(active_user)
        with pytest.raises(BadRequestError):
            crud.actions_reboot(db_session, request, id=stopped_vm.id)


# ---------------------------------------------------------------------------
# actions_shutdown
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineActionsShutdown:
    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_shutdown_sets_status_shutting_down(
        self,
        mock_periodic,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        result = crud.actions_shutdown(db_session, request, id=sample_vm.id)
        assert result.status == "shutting down"

    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_shutdown_creates_changelog(
        self,
        mock_periodic,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        crud.actions_shutdown(db_session, request, id=sample_vm.id)

        changelogs = (
            db_session.query(Changelog).filter(Changelog.objectId == sample_vm.id).all()
        )
        assert len(changelogs) >= 1

    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_shutdown_already_stopped_raises(
        self,
        mock_periodic,
        db_session,
        active_user,
        mock_redis_queues,
        stopped_vm,
    ):
        crud = CRUDVirtualMachine(db=db_session, id=stopped_vm.id)
        request = create_mock_request(active_user)
        with pytest.raises(BadRequestError):
            crud.actions_shutdown(db_session, request, id=stopped_vm.id)


# ---------------------------------------------------------------------------
# actions_resume
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineActionsResume:
    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_resume_sets_status_resuming(
        self,
        mock_periodic,
        db_session,
        active_user,
        mock_redis_queues,
        paused_vm,
    ):
        crud = CRUDVirtualMachine(db=db_session, id=paused_vm.id)
        request = create_mock_request(active_user)
        result = crud.actions_resume(db_session, request, id=paused_vm.id)
        assert result.status == "Resuming"

    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_resume_creates_changelog(
        self,
        mock_periodic,
        db_session,
        active_user,
        mock_redis_queues,
        paused_vm,
    ):
        crud = CRUDVirtualMachine(db=db_session, id=paused_vm.id)
        request = create_mock_request(active_user)
        crud.actions_resume(db_session, request, id=paused_vm.id)

        changelogs = (
            db_session.query(Changelog).filter(Changelog.objectId == paused_vm.id).all()
        )
        assert len(changelogs) >= 1

    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_resume_already_running_raises(
        self,
        mock_periodic,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        """Running VMs cannot be resumed."""
        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        with pytest.raises(BadRequestError):
            crud.actions_resume(db_session, request, id=sample_vm.id)


# ---------------------------------------------------------------------------
# actions_hibernate
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineActionsHibernate:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_hibernate_enqueues_job(
        self,
        mock_periodic,
        mock_pve_cls,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        """Hibernate a running VM (not locked)."""
        mock_pve = MagicMock()
        # VM is running, no lock key present
        mock_pve.proxmox.nodes.return_value.qemu.return_value.status.current.get.return_value = {
            "status": "running",
        }
        mock_pve.pve_get_node.return_value = "pve-node-1"
        mock_pve_cls.return_value = mock_pve

        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        result = crud.actions_hibernate(db_session, request, id=sample_vm.id)
        assert result is not None

        tasks = db_session.query(Task).all()
        assert any("Hibernate VirtualMachine" in t.name for t in tasks)

    @patch("controllers.virtual_machines.ProxmoxCluster")
    @patch(
        "controllers.virtual_machines.proxmox_node_info_periodic",
        new_callable=MagicMock,
    )
    def test_hibernate_already_hibernated_raises(
        self,
        mock_periodic,
        mock_pve_cls,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        """A VM that is already hibernated (stopped + suspended lock) raises."""
        mock_pve = MagicMock()
        mock_pve.proxmox.nodes.return_value.qemu.return_value.status.current.get.return_value = {
            "status": "stopped",
            "lock": "suspended",
        }
        mock_pve.pve_get_node.return_value = "pve-node-1"
        mock_pve_cls.return_value = mock_pve

        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        request = create_mock_request(active_user)
        with pytest.raises(BadRequestError):
            crud.actions_hibernate(db_session, request, id=sample_vm.id)


# ---------------------------------------------------------------------------
# bulk_pause
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineBulkPause:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_pause(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(sample_vm.id)])
        result = crud.bulk_pause(db_session, request, obj_in)
        assert result["enqueued"] == 1

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_pause_skips_paused(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
        paused_vm,
    ):
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(paused_vm.id)])
        with pytest.raises(BulkActionRequirementMissing):
            crud.bulk_pause(db_session, request, obj_in)

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_pause_nonexistent_raises(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
    ):
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        fake_id = str(uuid.uuid4())
        obj_in = VirtualMachineIdList(vms=[fake_id])
        with pytest.raises(BulkObjectNotFound):
            crud.bulk_pause(db_session, request, obj_in)


# ---------------------------------------------------------------------------
# bulk_reset
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineBulkReset:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_reset(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(sample_vm.id)])
        result = crud.bulk_reset(db_session, request, obj_in)
        assert result["enqueued"] == 1

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_reset_skips_stopped(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
        stopped_vm,
    ):
        """Only running VMs can be reset."""
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(stopped_vm.id)])
        with pytest.raises(BulkActionRequirementMissing):
            crud.bulk_reset(db_session, request, obj_in)


# ---------------------------------------------------------------------------
# bulk_reboot
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineBulkReboot:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_reboot(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(sample_vm.id)])
        result = crud.bulk_reboot(db_session, request, obj_in)
        assert result["enqueued"] == 1

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_reboot_skips_stopped(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
        stopped_vm,
    ):
        """Only running VMs can be rebooted."""
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(stopped_vm.id)])
        with pytest.raises(BulkActionRequirementMissing):
            crud.bulk_reboot(db_session, request, obj_in)


# ---------------------------------------------------------------------------
# bulk_shutdown
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineBulkShutdown:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_shutdown(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(sample_vm.id)])
        result = crud.bulk_shutdown(db_session, request, obj_in)
        assert result["enqueued"] == 1

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_shutdown_skips_stopped(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
        stopped_vm,
    ):
        """Stopped VMs cannot be shut down."""
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(stopped_vm.id)])
        with pytest.raises(BulkActionRequirementMissing):
            crud.bulk_shutdown(db_session, request, obj_in)


# ---------------------------------------------------------------------------
# bulk_resume
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineBulkResume:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_resume(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
        paused_vm,
    ):
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(paused_vm.id)])
        result = crud.bulk_resume(db_session, request, obj_in)
        assert result["enqueued"] == 1

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_resume_skips_running(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        """Running VMs are skipped for resume."""
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(sample_vm.id)])
        with pytest.raises(BulkActionRequirementMissing):
            crud.bulk_resume(db_session, request, obj_in)


# ---------------------------------------------------------------------------
# bulk_hibernate
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineBulkHibernate:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_hibernate(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        mock_pve = MagicMock()
        # VM is running with "lock" key present - eligible for hibernate
        mock_pve.proxmox.nodes.return_value.qemu.return_value.status.current.get.return_value = {
            "status": "running",
            "lock": "",
        }
        mock_pve.pve_get_node.return_value = "pve-node-1"
        mock_pve_cls.return_value = mock_pve

        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(sample_vm.id)])
        result = crud.bulk_hibernate(db_session, request, obj_in)
        assert result["enqueued"] == 1


# ---------------------------------------------------------------------------
# bulk_ha_add
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineBulkHaAdd:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_ha_add(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        from schemas.virtual_machines import VirtualMachineBulkHaAdd

        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineBulkHaAdd(
            vms=[str(sample_vm.id)],
            ha_state="started",
            ha_max_restart=5,
            ha_max_relocate=5,
        )
        result = crud.bulk_ha_add(db_session, request, obj_in)
        assert result["enqueued"] == 1

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_ha_add_nonexistent_raises(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
    ):
        from schemas.virtual_machines import VirtualMachineBulkHaAdd

        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        fake_id = str(uuid.uuid4())
        obj_in = VirtualMachineBulkHaAdd(
            vms=[fake_id],
            ha_state="started",
            ha_max_restart=5,
            ha_max_relocate=5,
        )
        with pytest.raises(BulkObjectNotFound):
            crud.bulk_ha_add(db_session, request, obj_in)


# ---------------------------------------------------------------------------
# bulk_ha_remove
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineBulkHaRemove:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_ha_remove(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(sample_vm.id)])
        result = crud.bulk_ha_remove(db_session, request, obj_in)
        assert result["enqueued"] == 1

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_ha_remove_nonexistent_raises(
        self,
        mock_pve,
        db_session,
        active_user,
        mock_redis_queues,
    ):
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        fake_id = str(uuid.uuid4())
        obj_in = VirtualMachineIdList(vms=[fake_id])
        with pytest.raises(BulkObjectNotFound):
            crud.bulk_ha_remove(db_session, request, obj_in)


# ---------------------------------------------------------------------------
# bulk_migrate
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineBulkMigrate:
    @patch(
        "controllers.virtual_machines.get_pve_node_info",
        return_value={"node_list": [{"node": "pve-node-2"}]},
    )
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_migrate(
        self,
        mock_pve,
        mock_node_info,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(sample_vm.id)])
        result = crud.bulk_migrate(
            db_session, request, obj_in, target_node="pve-node-2"
        )
        assert result["enqueued"] == 1

    @patch(
        "controllers.virtual_machines.get_pve_node_info",
        return_value={"node_list": [{"node": "pve-node-1"}, {"node": "pve-node-2"}]},
    )
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_migrate_skips_same_node(
        self,
        mock_pve,
        mock_node_info,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        """VMs already on the target node are skipped."""
        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        # sample_vm is on pve-node-1
        obj_in = VirtualMachineIdList(vms=[str(sample_vm.id)])
        with pytest.raises(BulkActionRequirementMissing):
            crud.bulk_migrate(db_session, request, obj_in, target_node="pve-node-1")

    @patch(
        "controllers.virtual_machines.get_pve_node_info",
        return_value={"node_list": [{"node": "pve-node-2"}]},
    )
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_bulk_migrate_invalid_node_raises(
        self,
        mock_pve,
        mock_node_info,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
    ):
        """Migrating to a non-existent node raises ProxmoxResourceNotFound."""
        from core.exceptions import ProxmoxResourceNotFound

        crud = CRUDVirtualMachine()
        request = create_mock_request(active_user)
        obj_in = VirtualMachineIdList(vms=[str(sample_vm.id)])
        with pytest.raises(ProxmoxResourceNotFound):
            crud.bulk_migrate(
                db_session, request, obj_in, target_node="nonexistent-node"
            )


# ---------------------------------------------------------------------------
# get_ipv4
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineGetIpv4:
    @patch(
        "controllers.virtual_machines.vm_ip_in_subnet",
        return_value="10.0.0.42",
    )
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_get_ipv4_returns_ip(
        self,
        mock_pve_cls,
        mock_subnet,
        db_session,
        active_user,
        sample_vm,
    ):
        mock_pve = MagicMock()
        mock_pve_cls.return_value = mock_pve
        mock_pve.pve_get_node.return_value = "pve-node-1"
        # Mock the proxmox() call for get_ipv4 which uses proxmox(f"/nodes/...")
        mock_pve.proxmox.return_value.get.return_value = {
            "result": [
                {
                    "name": "eth0",
                    "ip-addresses": [
                        {"ip-address": "10.0.0.42", "ip-address-type": "ipv4"}
                    ],
                }
            ]
        }

        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        result = crud.get_ipv4(sample_vm.id, db_session)
        assert result == "10.0.0.42"

    @patch(
        "controllers.virtual_machines.vm_ip_in_subnet",
        return_value=None,
    )
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_get_ipv4_not_in_subnet_returns_message(
        self,
        mock_pve_cls,
        mock_subnet,
        db_session,
        active_user,
        sample_vm,
    ):
        mock_pve = MagicMock()
        mock_pve_cls.return_value = mock_pve
        mock_pve.pve_get_node.return_value = "pve-node-1"
        mock_pve.proxmox.return_value.get.return_value = {
            "result": [
                {
                    "name": "eth0",
                    "ip-addresses": [
                        {"ip-address": "192.168.1.1", "ip-address-type": "ipv4"}
                    ],
                }
            ]
        }

        crud = CRUDVirtualMachine(db=db_session, id=sample_vm.id)
        result = crud.get_ipv4(sample_vm.id, db_session)
        # Should return a string message about the VM not being on the subnet
        assert isinstance(result, str)
        assert "Subnet" in result or "subnet" in result.lower()

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_get_ipv4_vm_not_running_raises(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        stopped_vm,
    ):
        """Getting IPv4 on a non-running VM raises BadRequestError via ResourceException."""
        from proxmoxer.core import ResourceException

        mock_pve = MagicMock()
        mock_pve_cls.return_value = mock_pve
        mock_pve.pve_get_node.return_value = "pve-node-1"
        mock_pve.proxmox.return_value.get.side_effect = ResourceException(
            status_code=500, status_message="QEMU agent not running", content=""
        )

        crud = CRUDVirtualMachine(db=db_session, id=stopped_vm.id)
        with pytest.raises(BadRequestError):
            crud.get_ipv4(stopped_vm.id, db_session)


# ---------------------------------------------------------------------------
# get_rrddata
# ---------------------------------------------------------------------------


class TestCRUDVirtualMachineGetRrddata:
    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_get_rrddata_returns_data(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        sample_vm,
    ):
        from schemas.proxmox import ProxmoxRRDConsolidation, ProxmoxRRDTimeframe

        mock_pve = MagicMock()
        mock_pve_cls.return_value = mock_pve
        rrd_data = [{"time": 1000, "cpu": 0.5, "mem": 2048}]
        mock_pve.proxmox.nodes.return_value.qemu.return_value.rrddata.get.return_value = rrd_data

        crud = CRUDVirtualMachine()
        result = crud.get_rrddata(
            db_session,
            id=sample_vm.id,
            timeframe=ProxmoxRRDTimeframe.HOUR,
            cf=ProxmoxRRDConsolidation.AVERAGE,
        )
        assert result == rrd_data

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_get_rrddata_invalid_vm_raises(
        self,
        mock_pve_cls,
        db_session,
        active_user,
    ):
        from core.exceptions import ObjectNotFound
        from schemas.proxmox import ProxmoxRRDConsolidation, ProxmoxRRDTimeframe

        crud = CRUDVirtualMachine()
        fake_id = uuid.uuid4()
        with pytest.raises(ObjectNotFound):
            crud.get_rrddata(
                db_session,
                id=fake_id,
                timeframe=ProxmoxRRDTimeframe.HOUR,
                cf=ProxmoxRRDConsolidation.AVERAGE,
            )

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_get_rrddata_proxmox_error_raises(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        sample_vm,
    ):
        """Invalid timeframe or cf raises BadRequestError via ResourceException."""
        from proxmoxer.core import ResourceException
        from schemas.proxmox import ProxmoxRRDConsolidation, ProxmoxRRDTimeframe

        mock_pve = MagicMock()
        mock_pve_cls.return_value = mock_pve
        mock_pve.proxmox.nodes.return_value.qemu.return_value.rrddata.get.side_effect = ResourceException(
            status_code=400, status_message="Bad Request", content=""
        )

        crud = CRUDVirtualMachine()
        with pytest.raises(BadRequestError):
            crud.get_rrddata(
                db_session,
                id=sample_vm.id,
                timeframe=ProxmoxRRDTimeframe.HOUR,
                cf=ProxmoxRRDConsolidation.AVERAGE,
            )

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_get_rrddata_string_id(
        self,
        mock_pve_cls,
        db_session,
        active_user,
        sample_vm,
    ):
        """get_rrddata accepts string UUIDs and converts them."""
        from schemas.proxmox import ProxmoxRRDConsolidation, ProxmoxRRDTimeframe

        mock_pve = MagicMock()
        mock_pve_cls.return_value = mock_pve
        rrd_data = [{"time": 1000, "cpu": 0.3}]
        mock_pve.proxmox.nodes.return_value.qemu.return_value.rrddata.get.return_value = rrd_data

        crud = CRUDVirtualMachine()
        result = crud.get_rrddata(
            db_session,
            id=str(sample_vm.id),
            timeframe=ProxmoxRRDTimeframe.HOUR,
            cf=ProxmoxRRDConsolidation.AVERAGE,
        )
        assert result == rrd_data

    @patch("controllers.virtual_machines.ProxmoxCluster")
    def test_get_rrddata_invalid_string_id_raises(
        self,
        mock_pve_cls,
        db_session,
        active_user,
    ):
        """An invalid string ID raises InvalidFieldValue."""
        from core.exceptions import InvalidFieldValue
        from schemas.proxmox import ProxmoxRRDConsolidation, ProxmoxRRDTimeframe

        crud = CRUDVirtualMachine()
        with pytest.raises(InvalidFieldValue):
            crud.get_rrddata(
                db_session,
                id="not-a-uuid",
                timeframe=ProxmoxRRDTimeframe.HOUR,
                cf=ProxmoxRRDConsolidation.AVERAGE,
            )
