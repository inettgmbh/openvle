"""Tests for schemas/virtual_machines.py - VirtualMachine schema validation."""

import uuid

import pytest

from core.exceptions import InvalidFieldValue
from schemas.virtual_machines import (
    VirtualMachineBulkHaAdd,
    VirtualMachineBulkMigrate,
    VirtualMachineClone,
    VirtualMachineCreate,
    VirtualMachineEventCreate,
    VirtualMachineHaAdd,
    VirtualMachineIdList,
    VirtualMachineMigrate,
    VirtualMachineUpdate,
    VirtualMachineUpdateApps,
)


def _make_vm(**kwargs):
    defaults = {
        "name": "test-vm",
        "description": "A test VM",
        "cpu": 2,
        "ram": 2048,
        "template": uuid.uuid4(),
    }
    defaults.update(kwargs)
    return VirtualMachineCreate(**defaults)


class TestVirtualMachineCreate:
    def test_valid_create(self):
        vm = _make_vm()
        assert vm.name == "test-vm"
        assert vm.cpu == 2
        assert vm.ram == 2048
        assert vm.prevent_delete is False
        assert vm.create_guacamole is False

    def test_required_fields(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            VirtualMachineCreate(name="test", cpu=1, ram=1024)

    def test_name_sanitized(self):
        vm = _make_vm(name="My VM Name")
        assert vm.name == "My-VM-Name"

    def test_description_truncated(self):
        vm = _make_vm(description="x" * 1500)
        assert len(vm.description) == 999

    def test_cpu_valid_range(self):
        assert _make_vm(cpu=1).cpu == 1
        assert _make_vm(cpu=24).cpu == 24

    def test_cpu_invalid_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_vm(cpu=0)
        with pytest.raises(InvalidFieldValue):
            _make_vm(cpu=25)

    def test_ram_valid_range(self):
        assert _make_vm(ram=1024).ram == 1024
        assert _make_vm(ram=268270).ram == 268270

    def test_ram_invalid_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_vm(ram=512)
        with pytest.raises(InvalidFieldValue):
            _make_vm(ram=300000)


class TestVirtualMachineClone:
    def _make_clone(self, **kwargs):
        defaults = {
            "name": "clone-vm",
            "description": "A cloned VM",
            "cpu": 4,
            "ram": 4096,
        }
        defaults.update(kwargs)
        return VirtualMachineClone(**defaults)

    def test_valid_clone(self):
        c = self._make_clone()
        assert c.name == "clone-vm"
        assert c.cpu == 4

    def test_clone_name_sanitized(self):
        c = self._make_clone(name="clone vm")
        assert c.name == "clone-vm"

    def test_clone_cpu_invalid_raises(self):
        with pytest.raises(InvalidFieldValue):
            self._make_clone(cpu=0)

    def test_clone_ram_invalid_raises(self):
        with pytest.raises(InvalidFieldValue):
            self._make_clone(ram=512)

    def test_clone_description_truncated(self):
        c = self._make_clone(description="d" * 1500)
        assert len(c.description) == 999


class TestVirtualMachineUpdate:
    def test_valid_update(self):
        u = VirtualMachineUpdate(cpu=8, ram=4096)
        assert u.cpu == 8
        assert u.ram == 4096

    def test_update_name_sanitized(self):
        u = VirtualMachineUpdate(name="new name")
        assert u.name == "new-name"

    def test_update_cpu_invalid_raises(self):
        with pytest.raises(InvalidFieldValue):
            VirtualMachineUpdate(cpu=0)

    def test_update_ram_invalid_raises(self):
        with pytest.raises(InvalidFieldValue):
            VirtualMachineUpdate(ram=512)

    def test_update_defaults(self):
        u = VirtualMachineUpdate()
        assert u.prevent_delete is False
        assert u.restart_vm is False


class TestVirtualMachineHaAdd:
    def test_defaults(self):
        ha = VirtualMachineHaAdd()
        assert ha.ha_state == "started"
        assert ha.ha_max_restart == 5
        assert ha.ha_max_relocate == 5

    def test_custom_values(self):
        ha = VirtualMachineHaAdd(
            ha_state="stopped", ha_max_restart=3, ha_max_relocate=2
        )
        assert ha.ha_state == "stopped"
        assert ha.ha_max_restart == 3


class TestVirtualMachineMigrate:
    def test_target_node_required(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            VirtualMachineMigrate()

    def test_valid_migrate(self):
        m = VirtualMachineMigrate(targetNode="pve-node-01")
        assert m.targetNode == "pve-node-01"


class TestVirtualMachineBulkHaAdd:
    def test_defaults(self):
        bulk = VirtualMachineBulkHaAdd()
        assert bulk.ha_state == "started"
        assert bulk.ha_max_restart == 5
        assert bulk.vms is None

    def test_with_vms(self):
        vm_ids = [uuid.uuid4(), uuid.uuid4()]
        bulk = VirtualMachineBulkHaAdd(vms=vm_ids)
        assert len(bulk.vms) == 2


class TestVirtualMachineBulkMigrate:
    def test_target_node_required(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            VirtualMachineBulkMigrate()

    def test_valid_bulk_migrate(self):
        m = VirtualMachineBulkMigrate(targetNode="pve-node-02", vms=[uuid.uuid4()])
        assert m.targetNode == "pve-node-02"


class TestVirtualMachineEventCreate:
    def test_valid_event_create(self):
        vm = VirtualMachineEventCreate(
            name="event-vm",
            cpu=2,
            ram=2048,
            template=uuid.uuid4(),
            event=uuid.uuid4(),
            user=uuid.uuid4(),
        )
        assert vm.name == "event-vm"
        assert vm.event is not None
        assert vm.user is not None

    def test_missing_event_raises(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            VirtualMachineEventCreate(
                name="test",
                cpu=2,
                ram=2048,
                template=uuid.uuid4(),
                user=uuid.uuid4(),
            )

    def test_missing_user_raises(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            VirtualMachineEventCreate(
                name="test",
                cpu=2,
                ram=2048,
                template=uuid.uuid4(),
                event=uuid.uuid4(),
            )

    def test_inherits_validators(self):
        """CPU/RAM validators from VirtualMachineCreate still apply."""
        with pytest.raises(InvalidFieldValue):
            VirtualMachineEventCreate(
                name="test",
                cpu=0,
                ram=2048,
                template=uuid.uuid4(),
                event=uuid.uuid4(),
                user=uuid.uuid4(),
            )


class TestVirtualMachineUpdateApps:
    def test_valid_update(self):
        u = VirtualMachineUpdateApps(apps=[{"key": "chrome"}])
        assert len(u.apps) == 1
        assert u.apps[0].key == "chrome"

    def test_none_apps(self):
        u = VirtualMachineUpdateApps(apps=None)
        assert u.apps is None

    def test_empty_list(self):
        u = VirtualMachineUpdateApps(apps=[])
        assert u.apps == []


class TestVirtualMachineIdList:
    def test_valid_list(self):
        ids = [uuid.uuid4(), uuid.uuid4()]
        vl = VirtualMachineIdList(vms=ids)
        assert len(vl.vms) == 2

    def test_none_vms(self):
        vl = VirtualMachineIdList()
        assert vl.vms is None
