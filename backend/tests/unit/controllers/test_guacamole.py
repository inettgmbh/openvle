"""Tests for controllers/guacamole.py - CRUDGuacamole operations."""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from controllers.guacamole import CRUDGuacamole
from core.exceptions import (
    BadRequestError,
    InvalidOperationForObject,
    ObjectNotFound,
    OperationDependencyMissing,
)
from models import (
    Guacamole,
    GuacamoleConnectionProfile,
    SubTask,
    Task,
    Template,
    Vendor,
    VirtualMachine,
)
from schemas.guacamole import GuacamoleCreate, GuacamoleUpdate

from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def sample_vendor_guac(db_session, system_user):
    now = datetime.now(timezone.utc)
    vendor = Vendor(
        id=uuid.uuid4(),
        name="Guac Vendor",
        description="Vendor for guac tests",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


@pytest.fixture()
def sample_vm(db_session, system_user):
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
        ipv4="10.0.0.100",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vm)
    db_session.flush()
    return vm


@pytest.fixture()
def sample_vm_no_ip(db_session, system_user):
    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name="vm-no-ip",
        status="running",
        proxmoxId=201,
        proxmoxNode="pve-node-1",
        cpu=2,
        ram=4096,
        disk=32,
        ipv4=None,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vm)
    db_session.flush()
    return vm


@pytest.fixture()
def sample_gcp_vm(db_session, system_user, sample_vm):
    now = datetime.now(timezone.utc)
    gcp = GuacamoleConnectionProfile(
        id=uuid.uuid4(),
        port=3389,
        protocol="rdp",
        username="admin",
        password="pass",
        objectId=sample_vm.id,
        objectType="VirtualMachine",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(gcp)
    db_session.flush()
    return gcp


@pytest.fixture()
def sample_gcp_template(db_session, system_user):
    """GCP attached to a Template (not VM)."""
    now = datetime.now(timezone.utc)
    tpl = Template(
        id=uuid.uuid4(),
        name="tpl-guac",
        proxmoxId=100,
        status="stopped",
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

    gcp = GuacamoleConnectionProfile(
        id=uuid.uuid4(),
        port=3389,
        protocol="rdp",
        objectId=tpl.id,
        objectType="Template",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(gcp)
    db_session.flush()
    return gcp


class TestCRUDGuacamoleCreate:
    def test_create_guacamole(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
        sample_gcp_vm,
    ):
        crud = CRUDGuacamole(db=db_session)
        request = create_mock_request(active_user)
        obj_in = GuacamoleCreate(
            name="guac-conn-01",
            connection_profile=str(sample_gcp_vm.id),
            userId=str(active_user.id),
        )
        result = crud.create(db_session, request, obj_in=obj_in)
        assert result.name == "guac-conn-01"
        assert result.userId == active_user.id
        assert result.connection_profile == sample_gcp_vm.id

    def test_create_creates_task_and_subtask(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        sample_vm,
        sample_gcp_vm,
    ):
        crud = CRUDGuacamole(db=db_session)
        request = create_mock_request(active_user)
        obj_in = GuacamoleCreate(
            name="guac-task",
            connection_profile=str(sample_gcp_vm.id),
            userId=str(active_user.id),
        )
        crud.create(db_session, request, obj_in=obj_in)

        tasks = db_session.query(Task).all()
        assert any("Provision Guacamole" in t.name for t in tasks)

        subtasks = db_session.query(SubTask).all()
        assert any(st.action == "guacamole_provision" for st in subtasks)

    def test_create_no_ipv4_raises(
        self, db_session, active_user, mock_redis_queues, sample_vm_no_ip
    ):
        """VM without IPv4 cannot have Guacamole connection."""
        now = datetime.now(timezone.utc)
        gcp = GuacamoleConnectionProfile(
            id=uuid.uuid4(),
            port=3389,
            protocol="rdp",
            objectId=sample_vm_no_ip.id,
            objectType="VirtualMachine",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(gcp)
        db_session.flush()

        crud = CRUDGuacamole(db=db_session)
        request = create_mock_request(active_user)
        obj_in = GuacamoleCreate(
            name="guac-no-ip",
            connection_profile=str(gcp.id),
            userId=str(active_user.id),
        )
        with pytest.raises(OperationDependencyMissing):
            crud.create(db_session, request, obj_in=obj_in)

    def test_create_template_gcp_raises(
        self, db_session, active_user, mock_redis_queues, sample_gcp_template
    ):
        """GCP linked to Template (not VM) cannot be used for Guacamole create."""
        crud = CRUDGuacamole(db=db_session)
        request = create_mock_request(active_user)
        obj_in = GuacamoleCreate(
            name="guac-template",
            connection_profile=str(sample_gcp_template.id),
            userId=str(active_user.id),
        )
        with pytest.raises(InvalidOperationForObject):
            crud.create(db_session, request, obj_in=obj_in)


class TestCRUDGuacamoleProvision:
    @patch("controllers.guacamole.provision_guacamole", return_value=42)
    def test_provision_stores_identifier(
        self,
        mock_provision,
        db_session,
        system_user,
        active_user,
        sample_vm,
        sample_gcp_vm,
    ):
        now = datetime.now(timezone.utc)
        guac = Guacamole(
            id=uuid.uuid4(),
            name="guac-provision-01",
            connection_profile=sample_gcp_vm.id,
            userId=active_user.id,
            identifier=None,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(guac)
        db_session.flush()

        crud = CRUDGuacamole(db=db_session, id=guac.id)
        with patch(
            "controllers.base.get_system_user", return_value=system_user
        ):
            result = crud.provision(db_session, id=guac.id)
        assert result.identifier == 42

    def test_provision_already_provisioned_raises(
        self, db_session, active_user, sample_vm, sample_gcp_vm
    ):
        now = datetime.now(timezone.utc)
        guac = Guacamole(
            id=uuid.uuid4(),
            name="guac-already",
            connection_profile=sample_gcp_vm.id,
            userId=active_user.id,
            identifier=99,  # Already provisioned
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(guac)
        db_session.flush()

        crud = CRUDGuacamole(db=db_session, id=guac.id)
        with pytest.raises(BadRequestError):
            crud.provision(db_session, id=guac.id)


class TestCRUDGuacamoleDelete:
    @patch("controllers.guacamole.guacamole_delete", return_value=True)
    def test_delete_guacamole(
        self,
        mock_guac_delete,
        db_session,
        active_user,
        sample_vm,
        sample_gcp_vm,
    ):
        now = datetime.now(timezone.utc)
        guac = Guacamole(
            id=uuid.uuid4(),
            name="guac-delete-me",
            connection_profile=sample_gcp_vm.id,
            userId=active_user.id,
            identifier=55,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(guac)
        db_session.flush()

        crud = CRUDGuacamole(db=db_session, id=guac.id)
        result = crud.delete(db_session, id=guac.id)
        assert "deleted" in result["detail"]
        mock_guac_delete.assert_called_once()


class TestCRUDGuacamoleUpdateHostname:
    @patch("controllers.guacamole.guacamole_hostname_update", return_value=None)
    def test_update_hostname(
        self,
        mock_hostname_update,
        db_session,
        active_user,
        sample_vm,
        sample_gcp_vm,
    ):
        now = datetime.now(timezone.utc)
        guac = Guacamole(
            id=uuid.uuid4(),
            name="guac-hostname",
            connection_profile=sample_gcp_vm.id,
            userId=active_user.id,
            identifier=77,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(guac)
        db_session.flush()

        crud = CRUDGuacamole(db=db_session, id=guac.id)
        result = crud.update_hostname(
            db_session, id=guac.id, hostname="10.0.0.200"
        )
        assert result.connection_hostname == "10.0.0.200"

    def test_update_hostname_not_provisioned_raises(
        self, db_session, active_user, sample_vm, sample_gcp_vm
    ):
        now = datetime.now(timezone.utc)
        guac = Guacamole(
            id=uuid.uuid4(),
            name="guac-no-ident",
            connection_profile=sample_gcp_vm.id,
            userId=active_user.id,
            identifier=None,  # Not provisioned
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(guac)
        db_session.flush()

        crud = CRUDGuacamole(db=db_session, id=guac.id)
        with pytest.raises(BadRequestError):
            crud.update_hostname(db_session, id=guac.id, hostname="10.0.0.200")


class TestCRUDGuacamoleGetByName:
    def test_get_by_name_found(
        self, db_session, active_user, sample_vm, sample_gcp_vm
    ):
        now = datetime.now(timezone.utc)
        guac = Guacamole(
            id=uuid.uuid4(),
            name="guac-find-me",
            connection_profile=sample_gcp_vm.id,
            userId=active_user.id,
            identifier=None,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(guac)
        db_session.flush()

        crud = CRUDGuacamole(db=db_session)
        result = crud.get_by_name(db_session, name="guac-find-me")
        assert result is not None
        assert result.id == guac.id
        assert result.name == "guac-find-me"

    def test_get_by_name_not_found(self, db_session, system_user):
        crud = CRUDGuacamole(db=db_session)
        result = crud.get_by_name(db_session, name="nonexistent-guac")
        assert result is None


class TestCRUDGuacamoleUpdate:
    def test_update_name(
        self, db_session, active_user, sample_vm, sample_gcp_vm
    ):
        now = datetime.now(timezone.utc)
        guac = Guacamole(
            id=uuid.uuid4(),
            name="guac-original-name",
            connection_profile=sample_gcp_vm.id,
            userId=active_user.id,
            identifier=10,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(guac)
        db_session.flush()

        crud = CRUDGuacamole(db=db_session)
        request = create_mock_request(active_user)
        obj_in = GuacamoleUpdate(name="guac-updated-name")
        result = crud.update(guac.id, db_session, request, obj_in=obj_in)
        assert result.name == "guac-updated-name"

    def test_update_guacd_port(
        self, db_session, active_user, sample_vm, sample_gcp_vm
    ):
        now = datetime.now(timezone.utc)
        guac = Guacamole(
            id=uuid.uuid4(),
            name="guac-port-test",
            connection_profile=sample_gcp_vm.id,
            userId=active_user.id,
            identifier=11,
            guacd_port=4822,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(guac)
        db_session.flush()

        crud = CRUDGuacamole(db=db_session)
        request = create_mock_request(active_user)
        obj_in = GuacamoleUpdate(guacd_port=5000)
        result = crud.update(guac.id, db_session, request, obj_in=obj_in)
        assert result.guacd_port == 5000

    def test_update_nonexistent_raises(self, db_session, active_user):
        crud = CRUDGuacamole(db=db_session)
        request = create_mock_request(active_user)
        obj_in = GuacamoleUpdate(name="no-such-guac")
        with pytest.raises(ObjectNotFound):
            crud.update(uuid.uuid4(), db_session, request, obj_in=obj_in)
