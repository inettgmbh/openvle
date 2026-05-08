"""Tests for controllers/templates.py - CRUDTemplate operations."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from controllers.templates import CRUDTemplate
from core.exceptions import (
    BadRequestError,
    ObjectNotFound,
    OperationDependencyMissing,
    ProtectedObjectError,
    ProxmoxConnectionError,
    ProxmoxResourceNotFound,
)
from models import (
    Application,
    ObjectPermission,
    SubTask,
    Task,
    Template,
    VirtualMachine,
    Vendor,
)
from schemas.templates import TemplateCreate, TemplateUpdate
from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def sample_vendor_tpl(db_session, system_user):
    now = datetime.now(timezone.utc)
    vendor = Vendor(
        id=uuid.uuid4(),
        name="Tpl Vendor",
        description="Vendor for tpl tests",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


@pytest.fixture()
def sample_app_tpl(db_session, system_user, sample_vendor_tpl):
    now = datetime.now(timezone.utc)
    app = Application(
        id=uuid.uuid4(),
        key="tpl-app",
        name="Tpl App",
        vendor=sample_vendor_tpl.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(app)
    db_session.flush()
    return app


@pytest.fixture()
def source_vm_stopped(db_session, system_user):
    """A stopped VM with proxmoxId, used as source for template creation."""
    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name="source-vm",
        status="stopped",
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
    db_session.add(vm)
    db_session.flush()
    return vm


@pytest.fixture()
def source_vm_running(db_session, system_user):
    """A running VM (cannot be used for template creation)."""
    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name="source-vm-running",
        status="running",
        proxmoxId=101,
        proxmoxNode="pve-node-1",
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
    return vm


@pytest.fixture()
def source_vm_no_proxmox(db_session, system_user):
    """A VM without proxmoxId."""
    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name="source-vm-no-pve",
        status="stopped",
        proxmoxId=None,
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
    return vm


@pytest.fixture()
def sample_template(db_session, system_user):
    now = datetime.now(timezone.utc)
    tpl = Template(
        id=uuid.uuid4(),
        name="tpl-test-01",
        status="available",
        proxmoxId=200,
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
def protected_template(db_session, system_user):
    now = datetime.now(timezone.utc)
    tpl = Template(
        id=uuid.uuid4(),
        name="tpl-protected",
        status="available",
        proxmoxId=201,
        proxmoxNode="pve-node-1",
        cpu=2,
        ram=4096,
        disk=32,
        prevent_delete=True,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(tpl)
    db_session.flush()
    return tpl


class TestCRUDTemplateGetByName:
    def test_found(self, db_session, sample_template):
        crud = CRUDTemplate()
        result = crud.get_by_name(db_session, name="tpl-test-01")
        assert result is not None
        assert result.id == sample_template.id

    def test_not_found(self, db_session, system_user):
        crud = CRUDTemplate()
        result = crud.get_by_name(db_session, name="nonexistent")
        assert result is None


class TestCRUDTemplateCreate:
    def test_create_template(
        self, db_session, active_user, mock_redis_queues, source_vm_stopped
    ):
        crud = CRUDTemplate()
        request = create_mock_request(active_user)
        obj_in = TemplateCreate(
            source_vm=str(source_vm_stopped.id),
            name="new-template",
            cpu=2,
            ram=2048,
            disk=32,
        )
        result = crud.create(db_session, request, obj_in=obj_in)
        assert result.name == "new-template"
        assert result.status == "queued"
        assert result.os == source_vm_stopped.os

    def test_create_creates_task_and_subtasks(
        self, db_session, active_user, mock_redis_queues, source_vm_stopped
    ):
        crud = CRUDTemplate()
        request = create_mock_request(active_user)
        obj_in = TemplateCreate(
            source_vm=str(source_vm_stopped.id),
            name="tpl-task-test",
            cpu=2,
            ram=2048,
            disk=32,
        )
        crud.create(db_session, request, obj_in=obj_in)

        tasks = db_session.query(Task).all()
        assert any("Create Template" in t.name for t in tasks)

        subtasks = db_session.query(SubTask).all()
        actions = [st.action for st in subtasks]
        assert "vm_clone" in actions
        assert "vm_convert" in actions
        assert "template_update" in actions

    def test_create_no_proxmox_id_raises(
        self, db_session, active_user, mock_redis_queues, source_vm_no_proxmox
    ):
        crud = CRUDTemplate()
        request = create_mock_request(active_user)
        obj_in = TemplateCreate(
            source_vm=str(source_vm_no_proxmox.id),
            name="tpl-no-pve",
            cpu=2,
            ram=2048,
            disk=32,
        )
        with pytest.raises(OperationDependencyMissing):
            crud.create(db_session, request, obj_in=obj_in)

    def test_create_running_vm_raises(
        self, db_session, active_user, mock_redis_queues, source_vm_running
    ):
        crud = CRUDTemplate()
        request = create_mock_request(active_user)
        obj_in = TemplateCreate(
            source_vm=str(source_vm_running.id),
            name="tpl-running",
            cpu=2,
            ram=2048,
            disk=32,
        )
        with pytest.raises(OperationDependencyMissing):
            crud.create(db_session, request, obj_in=obj_in)

    def test_create_creates_object_permission(
        self, db_session, active_user, mock_redis_queues, source_vm_stopped
    ):
        crud = CRUDTemplate()
        request = create_mock_request(active_user)
        obj_in = TemplateCreate(
            source_vm=str(source_vm_stopped.id),
            name="tpl-perm",
            cpu=2,
            ram=2048,
            disk=32,
        )
        result = crud.create(db_session, request, obj_in=obj_in)

        perms = (
            db_session.query(ObjectPermission)
            .filter(
                ObjectPermission.object_id == result.id,
                ObjectPermission.object_type == "Template",
            )
            .all()
        )
        assert len(perms) >= 1
        assert any(p.permission_key == "object_full" for p in perms)


class TestCRUDTemplateUpdate:
    def test_update_fields(
        self, db_session, active_user, mock_redis_queues, sample_template
    ):
        crud = CRUDTemplate(db=db_session, id=sample_template.id)
        request = create_mock_request(active_user)
        obj_in = TemplateUpdate(cpu=4)
        result = crud.update(sample_template.id, db_session, request, obj_in=obj_in)
        assert result.cpu == 4

    def test_update_creates_task(
        self, db_session, active_user, mock_redis_queues, sample_template
    ):
        crud = CRUDTemplate(db=db_session, id=sample_template.id)
        request = create_mock_request(active_user)
        obj_in = TemplateUpdate(ram=8192)
        crud.update(sample_template.id, db_session, request, obj_in=obj_in)

        tasks = db_session.query(Task).all()
        assert any("Update Template" in t.name for t in tasks)


class TestCRUDTemplateUpdateApps:
    def test_update_apps(
        self, db_session, active_user, sample_template, sample_app_tpl
    ):
        crud = CRUDTemplate(db=db_session, id=sample_template.id)
        request = create_mock_request(active_user)
        # Pass dict directly to avoid schema issues with ApplicationNested
        result = crud.update_apps(
            sample_template.id,
            db_session,
            request,
            obj_in={"apps": [{"key": "tpl-app"}]},
        )
        assert len(result.apps) == 1
        assert result.apps[0].key == "tpl-app"

    def test_update_apps_invalid_key_raises(
        self, db_session, active_user, sample_template
    ):
        crud = CRUDTemplate(db=db_session, id=sample_template.id)
        request = create_mock_request(active_user)
        with pytest.raises(ObjectNotFound):
            crud.update_apps(
                sample_template.id,
                db_session,
                request,
                obj_in={"apps": [{"key": "nonexistent-app"}]},
            )


class TestCRUDTemplateDelete:
    @patch("controllers.templates.ProxmoxCluster")
    def test_delete_template(
        self, mock_cluster, db_session, active_user, mock_redis_queues, sample_template
    ):
        mock_cluster.return_value.pve_get_node.return_value = "pve-node-1"
        mock_cluster.return_value.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "protection": 0
        }
        crud = CRUDTemplate(db=db_session, id=sample_template.id)
        request = create_mock_request(active_user)
        crud.delete(db_session, request, id=sample_template.id)

        db_session.refresh(sample_template)
        assert sample_template.status == "Deleting"

    def test_delete_protected_raises(
        self, db_session, active_user, mock_redis_queues, protected_template
    ):
        crud = CRUDTemplate(db=db_session, id=protected_template.id)
        request = create_mock_request(active_user)
        with pytest.raises(ProtectedObjectError):
            crud.delete(db_session, request, id=protected_template.id)

    @patch("controllers.templates.ProxmoxCluster")
    def test_delete_proceeds_when_pve_config_raises_resource_exception(
        self, mock_cluster, db_session, active_user, mock_redis_queues, sample_template
    ):
        """Template not found on PVE during protection check — deletion still proceeds."""
        from proxmoxer.core import ResourceException

        mock_cluster.return_value.pve_get_node.return_value = "pve-node-1"
        mock_cluster.return_value.proxmox.nodes.return_value.qemu.return_value.config.get.side_effect = ResourceException(
            501, "Not Implemented", ""
        )
        crud = CRUDTemplate(db=db_session, id=sample_template.id)
        request = create_mock_request(active_user)
        crud.delete(db_session, request, id=sample_template.id)

        db_session.refresh(sample_template)
        assert sample_template.status == "Deleting"

    @patch("controllers.templates.ProxmoxCluster")
    def test_delete_no_proxmox_id_proceeds(
        self, mock_cluster, db_session, active_user, mock_redis_queues, system_user
    ):
        """Template with no proxmoxId skips PVE protection check and proceeds."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        from models.templates import Template

        tpl = Template(
            id=uuid.uuid4(),
            name="broken-template",
            proxmoxId=None,
            cpu=2,
            ram=4096,
            disk=32,
            status="available",
            prevent_delete=False,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(tpl)
        db_session.flush()

        crud = CRUDTemplate(db=db_session, id=tpl.id)
        request = create_mock_request(active_user)
        crud.delete(db_session, request, id=tpl.id)

        db_session.refresh(tpl)
        assert tpl.status == "Deleting"
        mock_cluster.return_value.proxmox.nodes.return_value.qemu.return_value.config.get.assert_not_called()

    @patch("controllers.templates.ProxmoxCluster")
    def test_delete_in_use_by_vm_raises(
        self,
        mock_cluster,
        db_session,
        active_user,
        mock_redis_queues,
        sample_template,
        system_user,
    ):
        mock_cluster.return_value.pve_get_node.return_value = "pve-node-1"
        mock_cluster.return_value.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "protection": 0
        }
        now = datetime.now(timezone.utc)
        vm = VirtualMachine(
            id=uuid.uuid4(),
            name="vm-using-tpl",
            status="running",
            proxmoxId=300,
            cpu=2,
            ram=4096,
            disk=32,
            template=sample_template.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(vm)
        db_session.flush()

        crud = CRUDTemplate(db=db_session, id=sample_template.id)
        request = create_mock_request(active_user)
        with pytest.raises(BadRequestError):
            crud.delete(db_session, request, id=sample_template.id)


class TestCRUDTemplateLoadFromPve:
    @patch("controllers.templates.CRUDTemplate.get_pve_template")
    def test_load_from_pve(self, mock_get_pve, db_session, active_user):
        mock_get_pve.return_value = {
            "name": "pve-template-01",
            "node": "pve-node-1",
            "cores": 4,
            "memory": 8192,
            "description": "A PVE template",
            "scsi0": "local-lvm:base-200-disk-0,size=64G",
            "tags": "",
            "template": 1,
        }
        crud = CRUDTemplate()
        request = create_mock_request(active_user)
        result = crud.load_from_pve(db_session, request, proxmox_id=200)
        assert result.name == "pve-template-01"
        assert result.cpu == 4
        assert result.ram == 8192
        assert result.disk == 64
        assert result.status == "available"

    @patch("controllers.templates.CRUDTemplate.get_pve_template")
    def test_load_from_pve_no_disk_match(self, mock_get_pve, db_session, active_user):
        """When no disk key matches, disk defaults to 0."""
        mock_get_pve.return_value = {
            "name": "pve-template-02",
            "node": "pve-node-1",
            "cores": 2,
            "memory": 4096,
            "description": "",
            "tags": "",
            "template": 1,
        }
        crud = CRUDTemplate()
        request = create_mock_request(active_user)
        result = crud.load_from_pve(db_session, request, proxmox_id=201)
        assert result.disk == 0


class TestCRUDTemplateGetPveTemplate:
    def test_existing_proxmox_id_raises(self, db_session, sample_template):
        """If a template with the given proxmoxId already exists, raise BadRequestError."""
        crud = CRUDTemplate()
        with pytest.raises(BadRequestError):
            crud.get_pve_template(db_session, proxmox_id=sample_template.proxmoxId)

    @patch("controllers.templates.ProxmoxCluster")
    def test_proxmox_connection_failure_raises(
        self, mock_cluster_cls, db_session, system_user
    ):
        """If ProxmoxCluster() constructor raises, ProxmoxConnectionError is raised."""
        mock_cluster_cls.side_effect = Exception("Connection refused")
        crud = CRUDTemplate()
        with pytest.raises(ProxmoxConnectionError):
            crud.get_pve_template(db_session, proxmox_id=999)

    @patch("controllers.templates.ProxmoxCluster")
    def test_pve_config_retrieval_failure_raises(
        self, mock_cluster_cls, db_session, system_user
    ):
        """If PVE config retrieval fails, BadRequestError is raised."""
        mock_cluster = MagicMock()
        mock_cluster_cls.return_value = mock_cluster
        mock_cluster.pve_get_node.side_effect = Exception("Node not found")
        crud = CRUDTemplate()
        with pytest.raises(BadRequestError):
            crud.get_pve_template(db_session, proxmox_id=999)

    @patch("controllers.templates.ProxmoxCluster")
    def test_empty_config_raises(self, mock_cluster_cls, db_session, system_user):
        """If PVE returns empty config, ProxmoxResourceNotFound is raised."""
        mock_cluster = MagicMock()
        mock_cluster_cls.return_value = mock_cluster
        mock_cluster.pve_get_node.return_value = "pve-node-1"
        mock_cluster.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = None
        crud = CRUDTemplate()
        with pytest.raises(ProxmoxResourceNotFound):
            crud.get_pve_template(db_session, proxmox_id=999)

    @patch("controllers.templates.ProxmoxCluster")
    def test_non_template_vm_raises(self, mock_cluster_cls, db_session, system_user):
        """If the PVE resource is a VM (not a template), BadRequestError is raised."""
        mock_cluster = MagicMock()
        mock_cluster_cls.return_value = mock_cluster
        mock_cluster.pve_get_node.return_value = "pve-node-1"
        mock_cluster.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "name": "some-vm",
            "cores": 2,
            "memory": 4096,
            "template": 0,
        }
        crud = CRUDTemplate()
        with pytest.raises(BadRequestError):
            crud.get_pve_template(db_session, proxmox_id=999)

    @patch("controllers.templates.ProxmoxCluster")
    def test_successful_retrieval(self, mock_cluster_cls, db_session, system_user):
        """A valid PVE template config is returned successfully."""
        mock_cluster = MagicMock()
        mock_cluster_cls.return_value = mock_cluster
        mock_cluster.pve_get_node.return_value = "pve-node-1"
        expected_conf = {
            "name": "pve-tpl-valid",
            "cores": 4,
            "memory": 8192,
            "description": "A valid template",
            "scsi0": "local-lvm:base-999-disk-0,size=64G",
            "tags": "test,dev",
            "template": 1,
        }
        mock_cluster.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = expected_conf
        crud = CRUDTemplate()
        result = crud.get_pve_template(db_session, proxmox_id=999)
        assert result["name"] == "pve-tpl-valid"
        assert result["cores"] == 4
        assert result["memory"] == 8192
        assert result["node"] == "pve-node-1"
        assert result["template"] == 1
