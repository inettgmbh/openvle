"""Tests for pve/virtual_machines.py - ProxmoxVirtualMachine operations."""

import ipaddress
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from proxmoxer.core import ResourceException
from pve.worker_utils import TaskException

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_vm(db_session, system_user, **overrides):
    """Insert a VirtualMachine row into the test DB."""
    from models import VirtualMachine

    now = datetime.now(timezone.utc)
    defaults = {
        "id": uuid.uuid4(),
        "name": "test-vm",
        "proxmoxId": 100,
        "cpu": 2,
        "ram": 4096,
        "disk": 32,
        "status": "stopped",
        "prevent_delete": False,
        "createdAt": now,
        "updatedAt": now,
        "createdById": system_user.id,
        "updatedById": system_user.id,
    }
    defaults.update(overrides)
    vm = VirtualMachine(**defaults)
    db_session.add(vm)
    db_session.flush()
    return vm


def _make_template(db_session, system_user, **overrides):
    """Insert a Template row into the test DB."""
    from models.templates import Template

    now = datetime.now(timezone.utc)
    defaults = {
        "id": uuid.uuid4(),
        "name": "test-template",
        "proxmoxId": 9000,
        "cpu": 2,
        "ram": 4096,
        "disk": 32,
        "status": "available",
        "prevent_delete": False,
        "createdAt": now,
        "updatedAt": now,
        "createdById": system_user.id,
        "updatedById": system_user.id,
    }
    defaults.update(overrides)
    tpl = Template(**defaults)
    db_session.add(tpl)
    db_session.flush()
    return tpl


def _make_task_and_subtask(db_session, system_user, **sub_overrides):
    """Insert Task + SubTask rows (SubTask has FK to Task)."""
    from models import SubTask
    from models.tasks import Task

    now = datetime.now(timezone.utc)
    task = Task(
        id=uuid.uuid4(),
        name="parent-task",
        status="pending",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(task)
    db_session.flush()

    sub_defaults = {
        "id": uuid.uuid4(),
        "name": "sub-task",
        "status": "pending",
        "object_type": "VirtualMachine",
        "object_id": str(uuid.uuid4()),
        "action": "create",
        "attempt": "1",
        "parent_task": task.id,
        "createdAt": now,
        "updatedAt": now,
        "createdById": system_user.id,
        "updatedById": system_user.id,
    }
    sub_defaults.update(sub_overrides)
    st = SubTask(**sub_defaults)
    db_session.add(st)
    db_session.flush()
    return task, st


def _make_pvm(monkeypatch, db_session=None, task_id=None, vm_id=None):
    """Create a ProxmoxVirtualMachine with externals mocked.

    Returns (instance, mock_crud_instance, mock_cluster_instance).
    """
    mock_crud_instance = MagicMock()
    mock_crud_instance.worker_process_fail.return_value = Exception(
        "worker fail"
    )
    mock_crud_instance.worker_process_start.return_value = None
    mock_crud_instance.worker_process_success.return_value = None
    monkeypatch.setattr(
        "pve.virtual_machines.CRUDSubTask",
        MagicMock(return_value=mock_crud_instance),
    )

    mock_cluster = MagicMock()
    mock_cluster.proxmox = MagicMock()
    mock_cluster.pve_get_node.return_value = "node1"
    mock_cluster.get_free_node.return_value = "node1"
    mock_cluster.next_vm_id.return_value = 200
    monkeypatch.setattr(
        "pve.virtual_machines.ProxmoxCluster",
        MagicMock(return_value=mock_cluster),
    )

    if db_session is not None:
        monkeypatch.setattr(
            "pve.virtual_machines.SessionLocal", lambda: db_session
        )

    from pve.virtual_machines import ProxmoxVirtualMachine

    task_id = task_id or uuid.uuid4()
    vm_id = vm_id or uuid.uuid4()
    pvm = ProxmoxVirtualMachine(task_id, vm_id)
    return pvm, mock_crud_instance, mock_cluster


# ===========================================================================
# TestInit
# ===========================================================================
class TestInit:
    """ProxmoxVirtualMachine.__init__ sets attributes correctly."""

    def test_init_sets_core_attributes(self, monkeypatch):
        """All ID and connection attributes are initialised."""
        pvm, _, _ = _make_pvm(monkeypatch)

        assert pvm.db is None
        assert pvm.pve_connection is None
        assert pvm.proxmox is None
        assert pvm.kvs_vm is None
        assert pvm.source_template is None
        assert pvm.source_vm is None
        assert pvm.new_vmid is None
        assert pvm.pve_task is None
        assert pvm.pve_task_success is None

    def test_init_stores_ids(self, monkeypatch):
        """Constructor stores the supplied task and VM IDs."""
        task_id = uuid.uuid4()
        vm_id = uuid.uuid4()
        pvm, _, _ = _make_pvm(monkeypatch, task_id=task_id, vm_id=vm_id)

        assert pvm.kvs_task_object_id == task_id
        assert pvm.kvs_vm_id == vm_id

    def test_init_creates_settings(self, monkeypatch):
        """Constructor creates a Settings instance."""
        pvm, _, _ = _make_pvm(monkeypatch)
        assert pvm.settings is not None


# ===========================================================================
# TestStartProcess
# ===========================================================================
class TestStartProcess:
    """_start_process opens DB, updates task, and connects to PVE."""

    def test_opens_db_session(self, monkeypatch, db_session, system_user):
        """SessionLocal() is called and stored on self.db."""
        _, st = _make_task_and_subtask(db_session, system_user)
        pvm, _mock_crud, _ = _make_pvm(
            monkeypatch, db_session=db_session, task_id=st.id
        )

        pvm._start_process()

        assert pvm.db is db_session

    def test_calls_worker_process_start(
        self, monkeypatch, db_session, system_user
    ):
        """CRUDSubTask.worker_process_start is invoked."""
        _, st = _make_task_and_subtask(db_session, system_user)
        pvm, mock_crud, _ = _make_pvm(
            monkeypatch, db_session=db_session, task_id=st.id
        )

        pvm._start_process()

        mock_crud.worker_process_start.assert_called_once_with(
            db_session, st.id
        )

    def test_sets_request_user_id(self, monkeypatch, db_session, system_user):
        """request_user_id is loaded from SubTask.createdById."""
        _, st = _make_task_and_subtask(db_session, system_user)
        pvm, _, _ = _make_pvm(monkeypatch, db_session=db_session, task_id=st.id)

        pvm._start_process()

        assert pvm.request_user_id == system_user.id


# ===========================================================================
# TestPveInit
# ===========================================================================
class TestPveInit:
    """_pve_init connects to ProxmoxCluster."""

    def test_success(self, monkeypatch):
        """On success, pve_connection and proxmox are set."""
        pvm, _, _mock_cluster = _make_pvm(monkeypatch)

        pvm._pve_init()

        assert pvm.pve_connection is not None
        assert pvm.proxmox is not None

    def test_failure_calls_worker_process_fail(self, monkeypatch):
        """On ProxmoxCluster failure, worker_process_fail is called."""
        mock_crud_instance = MagicMock()
        mock_crud_instance.worker_process_fail.return_value = "fail-sentinel"
        monkeypatch.setattr(
            "pve.virtual_machines.CRUDSubTask",
            MagicMock(return_value=mock_crud_instance),
        )
        monkeypatch.setattr(
            "pve.virtual_machines.ProxmoxCluster",
            MagicMock(side_effect=ConnectionError("refused")),
        )

        from pve.virtual_machines import ProxmoxVirtualMachine

        pvm = ProxmoxVirtualMachine(uuid.uuid4(), uuid.uuid4())
        result = pvm._pve_init()

        mock_crud_instance.worker_process_fail.assert_called_once()
        assert result == "fail-sentinel"


# ===========================================================================
# TestGetVmAndTemplateObjects
# ===========================================================================
class TestGetVmAndTemplateObjects:
    """_get_vm_and_template_objects loads DB objects."""

    def test_loads_vm_and_template(self, monkeypatch, db_session, system_user):
        """VM and its template are loaded from DB."""
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id)
        pvm, _, _ = _make_pvm(monkeypatch, db_session=db_session, vm_id=vm.id)
        pvm.db = db_session

        pvm._get_vm_and_template_objects()

        assert pvm.kvs_vm is not None
        assert pvm.kvs_vm.id == vm.id
        assert pvm.source_template is not None

    def test_vm_not_found_raises(self, monkeypatch, db_session, system_user):
        """Missing VM raises via worker_process_fail."""
        pvm, mock_crud, _ = _make_pvm(
            monkeypatch, db_session=db_session, vm_id=uuid.uuid4()
        )
        pvm.db = db_session
        mock_crud.worker_process_fail.return_value = Exception("not found")

        with pytest.raises(Exception, match="not found"):
            pvm._get_vm_and_template_objects()

    def test_loads_template_from_vm(self, monkeypatch, db_session, system_user):
        """Template is loaded from kvs_vm.template FK."""
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id)
        pvm, _, _ = _make_pvm(monkeypatch, db_session=db_session, vm_id=vm.id)
        pvm.db = db_session

        pvm._get_vm_and_template_objects()

        assert pvm.source_template is not None
        assert pvm.source_template.id == tpl.id

    def test_template_not_found_raises(
        self, monkeypatch, db_session, system_user
    ):
        """Missing template raises via worker_process_fail."""
        from models import VirtualMachine as VMModel

        pvm, mock_crud, _ = _make_pvm(monkeypatch, vm_id=uuid.uuid4())
        # Use a mock DB that returns a VM with a non-existent template
        mock_vm = MagicMock(spec=VMModel)
        mock_vm.template = uuid.uuid4()
        mock_db = MagicMock()
        mock_db.get = lambda model, pk: mock_vm if pk == pvm.kvs_vm_id else None
        pvm.db = mock_db
        mock_crud.worker_process_fail.return_value = Exception(
            "template not found"
        )

        with pytest.raises(Exception, match="template not found"):
            pvm._get_vm_and_template_objects()


# ===========================================================================
# TestPveVmInit
# ===========================================================================
class TestPveVmInit:
    """_pve_vm_init checks for existing VM on PVE or allocates a new ID."""

    def test_existing_vm_on_pve_sets_success(
        self, monkeypatch, db_session, system_user
    ):
        """When VM exists on PVE (config returns), pve_task_success=True."""
        vm = _make_vm(db_session, system_user, proxmoxId=100)
        pvm, _, _mock_cluster = _make_pvm(
            monkeypatch, db_session=db_session, vm_id=vm.id
        )
        pvm.db = db_session
        pvm.kvs_vm = vm
        # Mock the proxmox.nodes().qemu().config.get() chain
        pvm.proxmox = MagicMock()
        pvm.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "name": "test"
        }

        pvm._pve_vm_init()

        assert pvm.pve_task_success is True

    def test_resource_exception_continues(
        self, monkeypatch, db_session, system_user
    ):
        """ResourceException means VM doesn't exist on PVE; allocates new ID."""
        vm = _make_vm(db_session, system_user, proxmoxId=100)
        pvm, _, mock_cluster = _make_pvm(
            monkeypatch, db_session=db_session, vm_id=vm.id
        )
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.pve_connection = mock_cluster
        pvm.proxmox = MagicMock()
        pvm.proxmox.nodes.return_value.qemu.return_value.config.get.side_effect = ResourceException(
            404, "not found", ""
        )

        pvm._pve_vm_init()

        assert pvm.new_vmid == 200
        assert pvm.kvs_vm.proxmoxId == 200
        assert pvm.kvs_vm.status == "cloning"

    def test_generic_exception_raises(
        self, monkeypatch, db_session, system_user
    ):
        """Non-ResourceException raises TaskException."""
        vm = _make_vm(db_session, system_user, proxmoxId=100)
        mock_crud_instance = MagicMock()
        mock_crud_instance.worker_process_fail.return_value = Exception(
            "pve error"
        )
        monkeypatch.setattr(
            "pve.virtual_machines.CRUDSubTask",
            MagicMock(return_value=mock_crud_instance),
        )
        mock_cluster = MagicMock()
        mock_cluster.next_vm_id.return_value = 200
        monkeypatch.setattr(
            "pve.virtual_machines.ProxmoxCluster",
            MagicMock(return_value=mock_cluster),
        )
        monkeypatch.setattr(
            "pve.virtual_machines.SessionLocal", lambda: db_session
        )

        from pve.virtual_machines import ProxmoxVirtualMachine

        pvm = ProxmoxVirtualMachine(uuid.uuid4(), vm.id)
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.proxmox = MagicMock()
        pvm.proxmox.nodes.return_value.qemu.return_value.config.get.side_effect = RuntimeError(
            "connection lost"
        )

        with pytest.raises(TaskException):
            pvm._pve_vm_init()

    def test_no_proxmox_id_gets_new_vmid(
        self, monkeypatch, db_session, system_user
    ):
        """When proxmoxId is None, allocates a new vmid."""
        vm = _make_vm(db_session, system_user, proxmoxId=None)
        pvm, _, mock_cluster = _make_pvm(
            monkeypatch, db_session=db_session, vm_id=vm.id
        )
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.pve_connection = mock_cluster

        pvm._pve_vm_init()

        assert pvm.new_vmid == 200
        assert pvm.kvs_vm.proxmoxId == 200
        assert pvm.kvs_vm.status == "cloning"


# ===========================================================================
# TestParseExcludedIps
# ===========================================================================
class TestParseExcludedIps:
    """_parse_excluded_ips converts a comma-separated string to a set of IPs."""

    def _make_instance(self, monkeypatch):
        pvm, _, _ = _make_pvm(monkeypatch)
        return pvm

    def test_empty_string(self, monkeypatch):
        pvm = self._make_instance(monkeypatch)
        result = pvm._parse_excluded_ips("")
        assert result == set()

    def test_none_input(self, monkeypatch):
        pvm = self._make_instance(monkeypatch)
        result = pvm._parse_excluded_ips(None)
        assert result == set()

    def test_single_ip(self, monkeypatch):
        pvm = self._make_instance(monkeypatch)
        result = pvm._parse_excluded_ips("10.0.0.5")
        assert result == {ipaddress.ip_address("10.0.0.5")}

    def test_ip_range(self, monkeypatch):
        pvm = self._make_instance(monkeypatch)
        result = pvm._parse_excluded_ips("10.0.0.10-10.0.0.12")
        expected = {
            ipaddress.ip_address("10.0.0.10"),
            ipaddress.ip_address("10.0.0.11"),
            ipaddress.ip_address("10.0.0.12"),
        }
        assert result == expected

    def test_cidr(self, monkeypatch):
        """CIDR notation expands to all hosts in the network."""
        pvm = self._make_instance(monkeypatch)
        result = pvm._parse_excluded_ips("10.0.0.0/30")
        # /30 has hosts: 10.0.0.1, 10.0.0.2
        expected = set(ipaddress.ip_network("10.0.0.0/30").hosts())
        assert result == expected

    def test_mixed(self, monkeypatch):
        """Combination of single IP, range, and CIDR."""
        pvm = self._make_instance(monkeypatch)
        result = pvm._parse_excluded_ips(
            "10.0.0.5, 10.0.0.10-10.0.0.11, 10.0.0.0/30"
        )
        assert ipaddress.ip_address("10.0.0.5") in result
        assert ipaddress.ip_address("10.0.0.10") in result
        assert ipaddress.ip_address("10.0.0.11") in result
        # /30 hosts
        assert ipaddress.ip_address("10.0.0.1") in result
        assert ipaddress.ip_address("10.0.0.2") in result


# ===========================================================================
# TestGetNextAvailableIp
# ===========================================================================
class TestGetNextAvailableIp:
    """_get_next_available_ip finds the first free IP in the subnet."""

    def _setup_pvm(self, monkeypatch, db_session, system_user):
        """Create PVM with mock settings for IP allocation."""
        pvm, mock_crud, _ = _make_pvm(monkeypatch, db_session=db_session)
        pvm.db = db_session
        # Override settings for deterministic IP allocation
        pvm.settings = MagicMock()
        pvm.settings.pve_vms_network = "10.0.0.0"
        pvm.settings.pve_vms_subnet = "/24"
        pvm.settings.pve_vms_excluded_ips = ""
        pvm.settings.pve_vms_gateway = "10.0.0.1"
        return pvm, mock_crud

    def test_returns_first_available(
        self, monkeypatch, db_session, system_user
    ):
        """Returns first usable IP (skipping .0, .1, .254, .255)."""
        pvm, _ = self._setup_pvm(monkeypatch, db_session, system_user)

        ip = pvm._get_next_available_ip()

        # .0 and .1 are skipped, gateway 10.0.0.1 excluded, so first is 10.0.0.2
        assert ip == ipaddress.ip_address("10.0.0.2")

    def test_skips_allocated_ips(self, monkeypatch, db_session, system_user):
        """IPs already in the database are skipped."""
        pvm, _ = self._setup_pvm(monkeypatch, db_session, system_user)
        # Allocate 10.0.0.2
        _make_vm(db_session, system_user, ipv4="10.0.0.2", proxmoxId=101)

        ip = pvm._get_next_available_ip()

        assert ip == ipaddress.ip_address("10.0.0.3")

    def test_skips_excluded_ips(self, monkeypatch, db_session, system_user):
        """Excluded IPs from settings are skipped."""
        pvm, _ = self._setup_pvm(monkeypatch, db_session, system_user)
        pvm.settings.pve_vms_excluded_ips = "10.0.0.2-10.0.0.5"

        ip = pvm._get_next_available_ip()

        assert ip == ipaddress.ip_address("10.0.0.6")

    def test_full_subnet_raises(self, monkeypatch, db_session, system_user):
        """Raises when no IPs are available."""
        pvm, mock_crud = self._setup_pvm(monkeypatch, db_session, system_user)
        # Use tiny /30 subnet: hosts are .1 and .2, but .1 is gateway, .0/.1/.254/.255 skipped
        pvm.settings.pve_vms_network = "10.0.0.0"
        pvm.settings.pve_vms_subnet = "/30"
        # /30 hosts: 10.0.0.1, 10.0.0.2 - gateway is .1, and .1 is skipped by octet check
        # .2 is the only candidate; exclude it
        pvm.settings.pve_vms_excluded_ips = "10.0.0.2"
        mock_crud.worker_process_fail.return_value = Exception("no IPs left")

        with pytest.raises(Exception, match="no IPs left"):
            pvm._get_next_available_ip()


# ===========================================================================
# TestMergePveAndKvsTags
# ===========================================================================
class TestMergePveAndKvsTags:
    """_merge_pve_and_kvs_tags merges and deduplicates tags."""

    def test_openvle_tags_only_sorted(self, monkeypatch):
        """Without pve_tags_merge, only KVS tags are returned (sorted)."""
        pvm, _, _ = _make_pvm(monkeypatch)
        pvm.db = MagicMock()

        mock_crud_tag = MagicMock()
        mock_crud_tag._convert_kvs_to_pve.return_value = ["zebra", "alpha"]
        monkeypatch.setattr(
            "pve.virtual_machines.CRUDTag",
            MagicMock(return_value=mock_crud_tag),
        )

        result = pvm._merge_pve_and_kvs_tags(
            proxmox_id=100, kvs_vm_id=uuid.uuid4()
        )

        assert result == "alpha,zebra"

    def test_pve_merge_combines_tags(self, monkeypatch):
        """With pve_tags_merge=True, PVE and KVS tags are merged."""
        pvm, _, _ = _make_pvm(monkeypatch)
        pvm.db = MagicMock()

        # Mock _pve_config_get to return PVE tags
        pvm._pve_config_get = MagicMock(
            return_value={"tags": "pve-tag1;pve-tag2"}
        )

        mock_crud_tag = MagicMock()
        mock_crud_tag._convert_kvs_to_pve.return_value = ["kvs-tag1"]
        monkeypatch.setattr(
            "pve.virtual_machines.CRUDTag",
            MagicMock(return_value=mock_crud_tag),
        )

        result = pvm._merge_pve_and_kvs_tags(
            proxmox_id=100, kvs_vm_id=uuid.uuid4(), pve_tags_merge=True
        )

        assert "kvs-tag1" in result
        assert "pve-tag1" in result
        assert "pve-tag2" in result

    def test_deduplication(self, monkeypatch):
        """Duplicate tags across PVE and KVS are deduplicated."""
        pvm, _, _ = _make_pvm(monkeypatch)
        pvm.db = MagicMock()
        pvm._pve_config_get = MagicMock(
            return_value={"tags": "shared;pve-only"}
        )

        mock_crud_tag = MagicMock()
        mock_crud_tag._convert_kvs_to_pve.return_value = ["shared", "kvs-only"]
        monkeypatch.setattr(
            "pve.virtual_machines.CRUDTag",
            MagicMock(return_value=mock_crud_tag),
        )

        result = pvm._merge_pve_and_kvs_tags(
            proxmox_id=100, kvs_vm_id=uuid.uuid4(), pve_tags_merge=True
        )

        tags = result.split(",")
        assert tags.count("shared") == 1

    def test_tag_removal(self, monkeypatch):
        """tag_to_remove filters out the specified tag."""
        pvm, _, _ = _make_pvm(monkeypatch)
        pvm.db = MagicMock()

        mock_crud_tag = MagicMock()
        mock_crud_tag._convert_kvs_to_pve.return_value = ["keep", "remove-me"]
        monkeypatch.setattr(
            "pve.virtual_machines.CRUDTag",
            MagicMock(return_value=mock_crud_tag),
        )

        result = pvm._merge_pve_and_kvs_tags(
            proxmox_id=100,
            kvs_vm_id=uuid.uuid4(),
            tag_to_remove="remove-me",
        )

        assert "remove-me" not in result
        assert "keep" in result


# ===========================================================================
# TestPveClone
# ===========================================================================
class TestPveClone:
    """_pve_clone_template and _pve_clone_vm interact with PVE API."""

    def test_clone_template_success(self, monkeypatch, db_session, system_user):
        """Successful template clone stores pve_task."""
        tpl = _make_template(db_session, system_user, proxmoxId=9000)
        vm = _make_vm(db_session, system_user, template=tpl.id)
        pvm, _, _mock_cluster = _make_pvm(
            monkeypatch, db_session=db_session, vm_id=vm.id
        )
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.source_template = tpl
        pvm.new_vmid = 200
        pvm.target_node = "node1"
        pvm.proxmox = MagicMock()
        pvm.proxmox.nodes.return_value.qemu.return_value.clone.post.return_value = "UPID:node1:00001"
        # Mock tag merging
        pvm._merge_pve_and_kvs_tags = MagicMock(return_value="tag1,tag2")
        # Mock module-level settings
        monkeypatch.setattr(
            "pve.virtual_machines.settings",
            MagicMock(pve_vms_full_clone_default=True, pve_vms_pool="pool1"),
        )

        pvm._pve_clone_template()

        assert pvm.pve_task == "UPID:node1:00001"

    def test_clone_vm_success(self, monkeypatch, db_session, system_user):
        """Successful VM clone stores pve_task."""
        tpl = _make_template(db_session, system_user, proxmoxId=9000)
        source_vm = _make_vm(
            db_session, system_user, name="source", proxmoxId=150
        )
        vm = _make_vm(db_session, system_user, template=tpl.id, proxmoxId=None)
        pvm, _, _mock_cluster = _make_pvm(
            monkeypatch, db_session=db_session, vm_id=vm.id
        )
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.source_template = tpl
        pvm.source_vm = source_vm
        pvm.new_vmid = 200
        pvm.target_node = "node1"
        pvm.proxmox = MagicMock()
        pvm.proxmox.nodes.return_value.qemu.return_value.clone.post.return_value = "UPID:node1:00002"
        pvm._merge_pve_and_kvs_tags = MagicMock(return_value="tag1")
        monkeypatch.setattr(
            "pve.virtual_machines.settings", MagicMock(pve_vms_pool="pool1")
        )

        pvm._pve_clone_vm()

        assert pvm.pve_task == "UPID:node1:00002"

    def test_clone_exception_raises(self, monkeypatch, db_session, system_user):
        """Exception during clone raises worker_process_fail."""
        tpl = _make_template(db_session, system_user, proxmoxId=9000)
        vm = _make_vm(db_session, system_user, template=tpl.id)
        pvm, mock_crud, _ = _make_pvm(
            monkeypatch, db_session=db_session, vm_id=vm.id
        )
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.source_template = tpl
        pvm.new_vmid = 200
        pvm.target_node = "node1"
        pvm.proxmox = MagicMock()
        pvm.proxmox.nodes.return_value.qemu.return_value.clone.post.side_effect = RuntimeError(
            "clone failed"
        )
        pvm._merge_pve_and_kvs_tags = MagicMock(return_value="")
        monkeypatch.setattr(
            "pve.virtual_machines.settings",
            MagicMock(pve_vms_full_clone_default=True, pve_vms_pool="pool1"),
        )
        mock_crud.worker_process_fail.return_value = Exception("clone error")

        with pytest.raises(Exception, match="clone error"):
            pvm._pve_clone_template()


# ===========================================================================
# TestPveActions
# ===========================================================================
class TestPveActions:
    """PVE action methods (start, stop, reboot, etc.)."""

    def _setup_pvm_with_vm(self, monkeypatch, db_session, system_user):
        vm = _make_vm(db_session, system_user, proxmoxId=100)
        pvm, mock_crud, _mock_cluster = _make_pvm(
            monkeypatch, db_session=db_session, vm_id=vm.id
        )
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.proxmox = MagicMock()
        return pvm, mock_crud, vm

    def test_start_success(self, monkeypatch, db_session, system_user):
        """_pve_actions_start stores pve_task on success."""
        pvm, _, _ = self._setup_pvm_with_vm(
            monkeypatch, db_session, system_user
        )
        pvm.proxmox.nodes.return_value.qemu.return_value.status.start.post.return_value = "UPID:start"

        pvm._pve_actions_start()

        assert pvm.pve_task == "UPID:start"

    def test_start_exception(self, monkeypatch, db_session, system_user):
        """_pve_actions_start calls worker_process_fail on exception."""
        pvm, mock_crud, _ = self._setup_pvm_with_vm(
            monkeypatch, db_session, system_user
        )
        pvm.proxmox.nodes.return_value.qemu.return_value.status.start.post.side_effect = RuntimeError(
            "start failed"
        )

        pvm._pve_actions_start()

        mock_crud.worker_process_fail.assert_called_once()

    def test_stop_success(self, monkeypatch, db_session, system_user):
        """_pve_actions_stop stores pve_task on success."""
        pvm, _, _ = self._setup_pvm_with_vm(
            monkeypatch, db_session, system_user
        )
        pvm.proxmox.nodes.return_value.qemu.return_value.status.stop.post.return_value = "UPID:stop"

        pvm._pve_actions_stop()

        assert pvm.pve_task == "UPID:stop"

    def test_stop_resource_exception(
        self, monkeypatch, db_session, system_user
    ):
        """_pve_actions_stop sets pve_task_success on ResourceException."""
        pvm, _, _ = self._setup_pvm_with_vm(
            monkeypatch, db_session, system_user
        )
        pvm.proxmox.nodes.return_value.qemu.return_value.status.stop.post.side_effect = ResourceException(
            500, "already stopped", ""
        )

        pvm._pve_actions_stop()

        assert pvm.pve_task_success is True

    def test_reboot_success(self, monkeypatch, db_session, system_user):
        """_pve_actions_reboot stores pve_task on success."""
        pvm, _, _ = self._setup_pvm_with_vm(
            monkeypatch, db_session, system_user
        )
        pvm.proxmox.nodes.return_value.qemu.return_value.status.reboot.post.return_value = "UPID:reboot"

        pvm._pve_actions_reboot()

        assert pvm.pve_task == "UPID:reboot"

    def test_reboot_exception(self, monkeypatch, db_session, system_user):
        """_pve_actions_reboot calls worker_process_fail on exception."""
        pvm, mock_crud, _ = self._setup_pvm_with_vm(
            monkeypatch, db_session, system_user
        )
        pvm.proxmox.nodes.return_value.qemu.return_value.status.reboot.post.side_effect = RuntimeError(
            "reboot failed"
        )

        pvm._pve_actions_reboot()

        mock_crud.worker_process_fail.assert_called_once()

    def test_shutdown_success(self, monkeypatch, db_session, system_user):
        """_pve_actions_shutdown stores pve_task on success."""
        pvm, _, _ = self._setup_pvm_with_vm(
            monkeypatch, db_session, system_user
        )
        pvm.proxmox.nodes.return_value.qemu.return_value.status.shutdown.post.return_value = "UPID:shutdown"

        pvm._pve_actions_shutdown()

        assert pvm.pve_task == "UPID:shutdown"

    def test_shutdown_exception(self, monkeypatch, db_session, system_user):
        """_pve_actions_shutdown calls worker_process_fail on exception."""
        pvm, mock_crud, _ = self._setup_pvm_with_vm(
            monkeypatch, db_session, system_user
        )
        pvm.proxmox.nodes.return_value.qemu.return_value.status.shutdown.post.side_effect = RuntimeError(
            "shutdown failed"
        )

        pvm._pve_actions_shutdown()

        mock_crud.worker_process_fail.assert_called_once()


# ===========================================================================
# TestPveDelete
# ===========================================================================
class TestPveDelete:
    """_pve_delete handles VM existence check + deletion on PVE."""

    def test_vm_exists_on_pve(self, monkeypatch, db_session, system_user):
        """When VM exists on PVE, delete is called and pve_task is set."""
        vm = _make_vm(db_session, system_user, proxmoxId=100)
        pvm, _, _ = _make_pvm(monkeypatch, db_session=db_session, vm_id=vm.id)
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.proxmox = MagicMock()
        pvm.proxmox.cluster.resources.get.return_value = [
            {"vmid": 100, "node": "node1"}
        ]
        pvm.proxmox.nodes.return_value.qemu.return_value.delete.return_value = (
            "UPID:delete"
        )

        pvm._pve_delete()

        assert pvm.pve_task == "UPID:delete"

    def test_vm_not_on_pve(self, monkeypatch, db_session, system_user):
        """When VM doesn't exist on PVE, pve_task_success is set directly."""
        vm = _make_vm(db_session, system_user, proxmoxId=100)
        pvm, _, _ = _make_pvm(monkeypatch, db_session=db_session, vm_id=vm.id)
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.proxmox = MagicMock()
        pvm.proxmox.cluster.resources.get.return_value = [
            {"vmid": 999, "node": "node1"}
        ]

        pvm._pve_delete()

        assert pvm.pve_task_success is True

    def test_no_proxmox_id(self, monkeypatch, db_session, system_user):
        """When VM has no proxmoxId, pve_task_success is set directly."""
        vm = _make_vm(db_session, system_user, proxmoxId=None)
        pvm, _, _ = _make_pvm(monkeypatch, db_session=db_session, vm_id=vm.id)
        pvm.db = db_session
        pvm.kvs_vm = vm

        pvm._pve_delete()

        assert pvm.pve_task_success is True

    def test_resource_exception_sets_success(
        self, monkeypatch, db_session, system_user
    ):
        """ResourceException during delete sets pve_task_success=True."""
        vm = _make_vm(db_session, system_user, proxmoxId=100)
        pvm, _, _ = _make_pvm(monkeypatch, db_session=db_session, vm_id=vm.id)
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.proxmox = MagicMock()
        pvm.proxmox.cluster.resources.get.side_effect = ResourceException(
            404, "not found", ""
        )

        pvm._pve_delete()

        assert pvm.pve_task_success is True


# ===========================================================================
# TestPveHa
# ===========================================================================
class TestPveHa:
    """HA configuration methods."""

    def _setup_pvm_with_vm(self, monkeypatch, db_session, system_user):
        vm = _make_vm(db_session, system_user, proxmoxId=100)
        pvm, mock_crud, _ = _make_pvm(
            monkeypatch, db_session=db_session, vm_id=vm.id
        )
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.proxmox = MagicMock()
        return pvm, mock_crud

    def test_ha_configured_true(self, monkeypatch, db_session, system_user):
        """_pve_ha_configured returns True when HA state exists."""
        pvm, _ = self._setup_pvm_with_vm(monkeypatch, db_session, system_user)
        pvm.proxmox.cluster.ha.resources.get.return_value = {"state": "started"}

        assert pvm._pve_ha_configured() is True

    def test_ha_configured_false(self, monkeypatch, db_session, system_user):
        """_pve_ha_configured returns False on ResourceException."""
        pvm, _ = self._setup_pvm_with_vm(monkeypatch, db_session, system_user)
        pvm.proxmox.cluster.ha.resources.get.side_effect = ResourceException(
            404, "not found", ""
        )

        assert pvm._pve_ha_configured() is False

    def test_ha_set_new(self, monkeypatch, db_session, system_user):
        """_pve_ha_set calls resources.post when HA is not configured."""
        pvm, _ = self._setup_pvm_with_vm(monkeypatch, db_session, system_user)
        # _pve_ha_configured returns False (ResourceException)
        pvm.proxmox.cluster.ha.resources.get.side_effect = ResourceException(
            404, "not found", ""
        )

        pvm._pve_ha_set(ha_state="started", ha_max_restart=3, ha_max_relocate=3)

        pvm.proxmox.cluster.ha.resources.post.assert_called_once()

    def test_ha_remove_resource_exception(
        self, monkeypatch, db_session, system_user
    ):
        """_pve_ha_remove handles ResourceException gracefully."""
        pvm, _ = self._setup_pvm_with_vm(monkeypatch, db_session, system_user)
        pvm.proxmox.cluster.ha.resources.return_value.delete.side_effect = (
            ResourceException(404, "not found", "")
        )

        pvm._pve_ha_remove()

        assert pvm.pve_task_success is True


# ===========================================================================
# TestHighLevelWorkflows
# ===========================================================================
class TestHighLevelWorkflows:
    """High-level async workflow methods."""

    @pytest.mark.anyio
    async def test_create_from_template_happy_path(
        self, monkeypatch, db_session, system_user
    ):
        """create_from_template clones template, updates status to stopped."""
        tpl = _make_template(db_session, system_user, proxmoxId=9000)
        _, st = _make_task_and_subtask(db_session, system_user)
        vm = _make_vm(
            db_session,
            system_user,
            template=tpl.id,
            proxmoxId=None,
            status="pending",
        )

        pvm, mock_crud, _mock_cluster = _make_pvm(
            monkeypatch, db_session=db_session, task_id=st.id, vm_id=vm.id
        )
        # Mock _pve_clone_template to set pve_task
        pvm.proxmox = MagicMock()
        pvm.proxmox.nodes.return_value.qemu.return_value.clone.post.return_value = "UPID:clone"
        pvm.proxmox.nodes.return_value.qemu.return_value.config.get.side_effect = ResourceException(
            404, "not found", ""
        )
        # Mock tag merge
        monkeypatch.setattr(
            "pve.virtual_machines.CRUDTag",
            MagicMock(
                return_value=MagicMock(
                    _convert_kvs_to_pve=MagicMock(return_value=[])
                )
            ),
        )
        monkeypatch.setattr("pve.virtual_machines.CRUDChangelog", MagicMock())
        monkeypatch.setattr(
            "pve.virtual_machines.settings",
            MagicMock(pve_vms_full_clone_default=True, pve_vms_pool="pool1"),
        )
        # Mock kvs_await_pve_task_exit to return True (success)
        monkeypatch.setattr(
            "pve.virtual_machines.kvs_await_pve_task_exit",
            AsyncMock(return_value=True),
        )

        await pvm.create_from_template()

        assert vm.status == "stopped"
        mock_crud.worker_process_success.assert_called_once()

    @pytest.mark.anyio
    async def test_delete_prevent_delete(
        self, monkeypatch, db_session, system_user
    ):
        """delete() returns failure when prevent_delete is True."""
        tpl = _make_template(db_session, system_user)
        _, st = _make_task_and_subtask(db_session, system_user)
        vm = _make_vm(
            db_session,
            system_user,
            prevent_delete=True,
            proxmoxId=100,
            template=tpl.id,
        )
        pvm, mock_crud, _ = _make_pvm(
            monkeypatch, db_session=db_session, task_id=st.id, vm_id=vm.id
        )

        await pvm.delete()

        mock_crud.worker_process_fail.assert_called_once()
        args = mock_crud.worker_process_fail.call_args[0]
        assert args[1] == 403

    @pytest.mark.anyio
    async def test_delete_proceeds_when_pve_config_raises_resource_exception(
        self, monkeypatch, db_session, system_user
    ):
        """delete() proceeds with deletion when PVE config fetch raises ResourceException.

        A broken VM (not present on PVE) raises ResourceException during the
        protection check — we treat it as not-protected and proceed.
        """
        tpl = _make_template(db_session, system_user)
        _, st = _make_task_and_subtask(db_session, system_user)
        vm = _make_vm(db_session, system_user, proxmoxId=100, template=tpl.id)
        pvm, mock_crud, mock_cluster = _make_pvm(
            monkeypatch, db_session=db_session, task_id=st.id, vm_id=vm.id
        )

        # PVE config fetch raises ResourceException (e.g. 501 Not Implemented)
        # Use mock_cluster.proxmox — pvm.proxmox is None until _start_process() runs
        mock_cluster.proxmox.nodes.return_value.qemu.return_value.config.get.side_effect = ResourceException(
            501, "Not Implemented", ""
        )
        pvm._pve_delete = MagicMock()
        pvm._kvs_vm_delete = MagicMock()
        pvm.pve_task_success = True

        await pvm.delete()

        # Must NOT call worker_process_fail with 502 (old behaviour)
        for call in mock_crud.worker_process_fail.call_args_list:
            assert call[0][1] != 502, (
                "Should not fail with 502 for missing PVE resource"
            )
        pvm._pve_delete.assert_called_once()

    @pytest.mark.anyio
    async def test_delete_no_proxmox_id_proceeds(
        self, monkeypatch, db_session, system_user
    ):
        """delete() skips PVE protection check and deletes when proxmoxId is None."""
        tpl = _make_template(db_session, system_user)
        _, st = _make_task_and_subtask(db_session, system_user)
        vm = _make_vm(db_session, system_user, proxmoxId=None, template=tpl.id)
        pvm, mock_crud, _ = _make_pvm(
            monkeypatch, db_session=db_session, task_id=st.id, vm_id=vm.id
        )
        pvm._pve_delete = MagicMock()
        pvm._kvs_vm_delete = MagicMock()
        pvm.pve_task_success = True

        await pvm.delete()

        pvm._pve_delete.assert_called_once()
        mock_crud.worker_process_success.assert_called_once()


# ===========================================================================
# TestBuildSmbios1String
# ===========================================================================


def _make_event(
    db_session, system_user, event_statuses, sample_course, slug="evt001"
):
    """Insert an Event row into the test DB."""
    from models import Event

    now = datetime.now(timezone.utc)
    event = Event(
        id=uuid.uuid4(),
        name=f"Test Event {slug}",
        slug=slug,
        description="A test event",
        dateStart=datetime.now(timezone.utc).date(),
        dateEnd=datetime.now(timezone.utc).date(),
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


PVE_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def _b64(val):
    """Base64-encode a value, matching _build_smbios1_string encoding."""
    import base64

    return base64.b64encode(str(val).encode()).decode()


def _setup_pvm_for_smbios(
    monkeypatch, db_session, vm, pve_smbios1=f"uuid={PVE_UUID}"
):
    """Create a PVM instance with mocked PVE config for SMBIOS tests."""
    pvm, mock_crud, mock_cluster = _make_pvm(
        monkeypatch, db_session=db_session, vm_id=vm.id
    )
    pvm.db = db_session
    pvm.kvs_vm = vm
    pvm.proxmox = mock_cluster.proxmox
    # Mock _pve_config_get to return existing smbios1 with UUID
    pvm.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
        "smbios1": pve_smbios1,
    }
    return pvm, mock_crud, mock_cluster


class TestBuildSmbios1String:
    """_build_smbios1_string builds the correct SMBIOS type 1 string."""

    def test_vm_with_event_uses_slug_as_family(
        self,
        monkeypatch,
        db_session,
        system_user,
        event_statuses,
        sample_course,
    ):
        """family field should contain the base64-encoded event slug."""
        tpl = _make_template(db_session, system_user)
        event = _make_event(
            db_session,
            system_user,
            event_statuses,
            sample_course,
            slug="myslug",
        )
        vm = _make_vm(db_session, system_user, template=tpl.id, event=event.id)

        pvm, _, _ = _setup_pvm_for_smbios(monkeypatch, db_session, vm)

        result = pvm._build_smbios1_string()

        assert f"family={_b64('event_slug=myslug')}" in result

    def test_vm_without_event_uses_zero_as_family(
        self, monkeypatch, db_session, system_user
    ):
        """family field should be base64('0') when VM has no event."""
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id, event=None)

        pvm, _, _ = _setup_pvm_for_smbios(monkeypatch, db_session, vm)

        result = pvm._build_smbios1_string()

        assert f"family={_b64('event_slug=null')}" in result

    def test_starts_with_base64_flag(
        self, monkeypatch, db_session, system_user
    ):
        """Result string must start with base64=1."""
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id)

        pvm, _, _ = _setup_pvm_for_smbios(monkeypatch, db_session, vm)

        result = pvm._build_smbios1_string()

        assert result.startswith("base64=1,")

    def test_contains_all_smbios_fields(
        self, monkeypatch, db_session, system_user
    ):
        """Result string must contain all six SMBIOS fields plus uuid."""
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id)

        pvm, _, _ = _setup_pvm_for_smbios(monkeypatch, db_session, vm)

        result = pvm._build_smbios1_string()

        for field in (
            "uuid=",
            "manufacturer=",
            "product=",
            "version=",
            "serial=",
            "sku=",
            "family=",
        ):
            assert field in result

    def test_manufacturer_is_project_title(
        self, monkeypatch, db_session, system_user
    ):
        """manufacturer should be base64-encoded settings.project_title."""
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id)

        pvm, _, _ = _setup_pvm_for_smbios(monkeypatch, db_session, vm)

        result = pvm._build_smbios1_string()

        expected = _b64(pvm.settings.project_title)
        assert f"manufacturer={expected}" in result

    def test_product_is_vm_name(self, monkeypatch, db_session, system_user):
        """product should be base64-encoded VM name."""
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(
            db_session, system_user, template=tpl.id, name="my-special-vm"
        )

        pvm, _, _ = _setup_pvm_for_smbios(monkeypatch, db_session, vm)

        result = pvm._build_smbios1_string()

        assert f"product={_b64('name=my-special-vm')}" in result

    def test_version_is_template_id(self, monkeypatch, db_session, system_user):
        """version should be base64-encoded template UUID."""
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id)

        pvm, _, _ = _setup_pvm_for_smbios(monkeypatch, db_session, vm)

        result = pvm._build_smbios1_string()

        assert f"version={_b64(f'template_id={tpl.id}')}" in result

    def test_serial_is_vm_id(self, monkeypatch, db_session, system_user):
        """serial should be base64-encoded VM UUID."""
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id)

        pvm, _, _ = _setup_pvm_for_smbios(monkeypatch, db_session, vm)

        result = pvm._build_smbios1_string()

        assert f"serial={_b64(f'vm_id={vm.id}')}" in result

    def test_sku_is_null_placeholder(
        self, monkeypatch, db_session, system_user
    ):
        """sku should be base64-encoded 'null'."""
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id)

        pvm, _, _ = _setup_pvm_for_smbios(monkeypatch, db_session, vm)

        result = pvm._build_smbios1_string()

        assert f"sku={_b64('null')}" in result

    def test_values_decode_to_original(
        self, monkeypatch, db_session, system_user
    ):
        """All base64-encoded values should decode back to originals."""
        import base64

        tpl = _make_template(db_session, system_user)
        vm = _make_vm(
            db_session, system_user, template=tpl.id, name="test-vm-42"
        )

        pvm, _, _ = _setup_pvm_for_smbios(monkeypatch, db_session, vm)

        result = pvm._build_smbios1_string()

        # Parse key=value pairs (skip base64=1)
        pairs = {}
        for part in result.split(","):
            k, v = part.split("=", 1)
            pairs[k] = v

        assert base64.b64decode(pairs["product"]).decode() == "name=test-vm-42"
        assert base64.b64decode(pairs["serial"]).decode() == f"vm_id={vm.id}"
        assert (
            base64.b64decode(pairs["version"]).decode()
            == f"template_id={tpl.id}"
        )
        assert base64.b64decode(pairs["sku"]).decode() == "null"
        assert base64.b64decode(pairs["family"]).decode() == "event_slug=null"

    def test_preserves_existing_pve_uuid(
        self, monkeypatch, db_session, system_user
    ):
        """The PVE-assigned UUID must be preserved in the output."""
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id)

        pvm, _, _ = _setup_pvm_for_smbios(monkeypatch, db_session, vm)

        result = pvm._build_smbios1_string()

        assert f"uuid={PVE_UUID}" in result

    def test_no_uuid_when_pve_has_none(
        self, monkeypatch, db_session, system_user
    ):
        """When PVE config has no smbios1 UUID, output should omit uuid=."""
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id)

        pvm, _, _ = _setup_pvm_for_smbios(
            monkeypatch, db_session, vm, pve_smbios1=""
        )

        result = pvm._build_smbios1_string()

        assert "uuid=" not in result

    def test_uuid_preserved_when_config_has_other_fields(
        self, monkeypatch, db_session, system_user
    ):
        """UUID is extracted even when smbios1 contains other fields."""
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id)
        pve_uuid = "11111111-2222-3333-4444-555555555555"

        pvm, _, _ = _setup_pvm_for_smbios(
            monkeypatch,
            db_session,
            vm,
            pve_smbios1=f"uuid={pve_uuid},manufacturer=old",
        )

        result = pvm._build_smbios1_string()

        assert f"uuid={pve_uuid}" in result

    def test_uuid_survives_pve_config_error(
        self, monkeypatch, db_session, system_user
    ):
        """When PVE config read fails, UUID is omitted gracefully."""
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id)

        pvm, _, mock_cluster = _make_pvm(
            monkeypatch, db_session=db_session, vm_id=vm.id
        )
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.proxmox = mock_cluster.proxmox
        # Simulate PVE config read failure
        pvm.proxmox.nodes.return_value.qemu.return_value.config.get.side_effect = Exception(
            "PVE unreachable"
        )

        result = pvm._build_smbios1_string()

        # Should still produce a valid string, just without uuid
        assert result.startswith("base64=1,")
        assert "uuid=" not in result
        assert "manufacturer=" in result

    def test_pve_update_passes_smbios1(
        self, monkeypatch, db_session, system_user
    ):
        """_pve_update should pass smbios1 to Proxmox config.put()."""
        tpl = _make_template(db_session, system_user)
        _, st = _make_task_and_subtask(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id, proxmoxId=100)

        pvm, _, mock_cluster = _make_pvm(
            monkeypatch, db_session=db_session, task_id=st.id, vm_id=vm.id
        )
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.proxmox = mock_cluster.proxmox

        pvm._pve_update()

        config_put = pvm.proxmox.nodes.return_value.qemu.return_value.config.put
        config_put.assert_called_once()
        call_kwargs = config_put.call_args[1]
        assert "smbios1" in call_kwargs
        assert call_kwargs["smbios1"].startswith("base64=1,")
        assert "manufacturer=" in call_kwargs["smbios1"]
        assert "product=" in call_kwargs["smbios1"]
        assert "serial=" in call_kwargs["smbios1"]
        assert call_kwargs["agent"] == "1"

    def test_pve_update_smbios1_reflects_current_vm_name(
        self, monkeypatch, db_session, system_user
    ):
        """After renaming a VM, _pve_update should use the new name."""
        tpl = _make_template(db_session, system_user)
        _, st = _make_task_and_subtask(db_session, system_user)
        vm = _make_vm(
            db_session,
            system_user,
            template=tpl.id,
            proxmoxId=100,
            name="old-name",
        )

        pvm, _, mock_cluster = _make_pvm(
            monkeypatch, db_session=db_session, task_id=st.id, vm_id=vm.id
        )
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.proxmox = mock_cluster.proxmox

        # Simulate a rename
        vm.name = "new-name"

        pvm._pve_update()

        config_put = pvm.proxmox.nodes.return_value.qemu.return_value.config.put
        smbios1 = config_put.call_args[1]["smbios1"]
        assert f"product={_b64('name=new-name')}" in smbios1

    def test_pve_update_skips_smbios_when_disabled(
        self, monkeypatch, db_session, system_user
    ):
        """When pve_vms_smbios_metadata is False, no smbios1 but agent still set."""
        tpl = _make_template(db_session, system_user)
        _, st = _make_task_and_subtask(db_session, system_user)
        vm = _make_vm(db_session, system_user, template=tpl.id, proxmoxId=100)

        pvm, _, mock_cluster = _make_pvm(
            monkeypatch, db_session=db_session, task_id=st.id, vm_id=vm.id
        )
        pvm.db = db_session
        pvm.kvs_vm = vm
        pvm.proxmox = mock_cluster.proxmox
        pvm.settings.pve_vms_smbios_metadata = False

        pvm._pve_update()

        config_put = pvm.proxmox.nodes.return_value.qemu.return_value.config.put
        config_put.assert_called_once()
        call_kwargs = config_put.call_args[1]
        assert "smbios1" not in call_kwargs
        assert call_kwargs["agent"] == "1"
