"""Tests for pve/templates.py - ProxmoxTemplate operations."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from proxmoxer.core import ResourceException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_template(db_session, system_user, **overrides):
    """Insert a Template row into the test DB."""
    from models.templates import Template

    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid.uuid4(),
        name="test-template",
        proxmoxId=9000,
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
    defaults.update(overrides)
    tpl = Template(**defaults)
    db_session.add(tpl)
    db_session.flush()
    return tpl


def _make_vm(db_session, system_user, **overrides):
    """Insert a VirtualMachine row into the test DB."""
    from models import VirtualMachine

    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid.uuid4(),
        name="test-vm",
        proxmoxId=100,
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
    defaults.update(overrides)
    vm = VirtualMachine(**defaults)
    db_session.add(vm)
    db_session.flush()
    return vm


def _make_task_and_subtask(db_session, system_user):
    """Insert Task + SubTask rows."""
    from models.tasks import Task
    from models import SubTask

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

    st = SubTask(
        id=uuid.uuid4(),
        name="sub-task",
        status="pending",
        object_type="Template",
        object_id=str(uuid.uuid4()),
        action="create",
        attempt="1",
        parent_task=task.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(st)
    db_session.flush()
    return task, st


def _make_pt(monkeypatch, db_session=None, task_id=None, template_id=None):
    """Create a ProxmoxTemplate with externals mocked.

    Returns (instance, mock_crud_instance, mock_cluster_instance).
    """
    mock_crud_instance = MagicMock()
    mock_crud_instance.worker_process_fail.return_value = Exception("worker fail")
    mock_crud_instance.worker_process_start.return_value = None
    mock_crud_instance.worker_process_success.return_value = None
    monkeypatch.setattr(
        "pve.templates.CRUDSubTask", MagicMock(return_value=mock_crud_instance)
    )

    mock_cluster = MagicMock()
    mock_cluster.proxmox = MagicMock()
    mock_cluster.pve_get_node.return_value = "node1"
    monkeypatch.setattr(
        "pve.templates.ProxmoxCluster", MagicMock(return_value=mock_cluster)
    )

    if db_session is not None:
        monkeypatch.setattr("pve.templates.SessionLocal", lambda: db_session)

    # Also mock the module-level db created at import time
    monkeypatch.setattr("pve.templates.db", MagicMock())

    from pve.templates import ProxmoxTemplate

    task_id = task_id or uuid.uuid4()
    template_id = template_id or uuid.uuid4()
    pt = ProxmoxTemplate(task_id, template_id)
    return pt, mock_crud_instance, mock_cluster


# ===========================================================================
# TestInit
# ===========================================================================
class TestInit:
    """ProxmoxTemplate.__init__ sets attributes correctly."""

    def test_init_sets_core_attributes(self, monkeypatch):
        pt, _, _ = _make_pt(monkeypatch)

        assert pt.db is None
        assert pt.pve_connection is None
        assert pt.proxmox is None
        assert pt.kvs_template is None
        assert pt.source_vm is None
        assert pt.pve_task is None
        assert pt.pve_task_success is None

    def test_init_stores_ids(self, monkeypatch):
        task_id = uuid.uuid4()
        tpl_id = uuid.uuid4()
        pt, _, _ = _make_pt(monkeypatch, task_id=task_id, template_id=tpl_id)

        assert pt.kvs_task_object_id == task_id
        assert pt.kvs_template_id == tpl_id


# ===========================================================================
# TestStartProcess
# ===========================================================================
class TestStartProcess:
    """_start_process opens DB and connects to PVE."""

    def test_opens_db_session(self, monkeypatch, db_session, system_user):
        _, st = _make_task_and_subtask(db_session, system_user)
        pt, mock_crud, _ = _make_pt(monkeypatch, db_session=db_session, task_id=st.id)

        pt._start_process()

        assert pt.db is db_session
        mock_crud.worker_process_start.assert_called_once()

    def test_calls_pve_init(self, monkeypatch, db_session, system_user):
        _, st = _make_task_and_subtask(db_session, system_user)
        pt, _, _ = _make_pt(monkeypatch, db_session=db_session, task_id=st.id)

        pt._start_process()

        assert pt.pve_connection is not None
        assert pt.proxmox is not None


# ===========================================================================
# TestPveInit
# ===========================================================================
class TestPveInit:
    """_pve_init connects to ProxmoxCluster."""

    def test_success(self, monkeypatch):
        pt, _, _ = _make_pt(monkeypatch)

        pt._pve_init()

        assert pt.pve_connection is not None
        assert pt.proxmox is not None

    def test_failure_calls_worker_process_fail(self, monkeypatch):
        mock_crud_instance = MagicMock()
        mock_crud_instance.worker_process_fail.return_value = "fail-sentinel"
        monkeypatch.setattr(
            "pve.templates.CRUDSubTask",
            MagicMock(return_value=mock_crud_instance),
        )
        monkeypatch.setattr(
            "pve.templates.ProxmoxCluster",
            MagicMock(side_effect=ConnectionError("refused")),
        )
        monkeypatch.setattr("pve.templates.db", MagicMock())

        from pve.templates import ProxmoxTemplate

        pt = ProxmoxTemplate(uuid.uuid4(), uuid.uuid4())
        result = pt._pve_init()

        mock_crud_instance.worker_process_fail.assert_called_once()
        assert result == "fail-sentinel"


# ===========================================================================
# TestGetVmAndTemplateObjects
# ===========================================================================
class TestGetVmAndTemplateObjects:
    """_get_vm_and_template_objects loads DB objects."""

    def test_loads_template(self, monkeypatch, db_session, system_user):
        tpl = _make_template(db_session, system_user)
        pt, _, _ = _make_pt(monkeypatch, db_session=db_session, template_id=tpl.id)
        pt.db = db_session

        pt._get_vm_and_template_objects()

        assert pt.kvs_template is not None
        assert pt.kvs_template.id == tpl.id

    def test_template_not_found_raises(self, monkeypatch, db_session, system_user):
        pt, mock_crud, _ = _make_pt(
            monkeypatch, db_session=db_session, template_id=uuid.uuid4()
        )
        pt.db = db_session
        mock_crud.worker_process_fail.return_value = Exception("not found")

        with pytest.raises(Exception, match="not found"):
            pt._get_vm_and_template_objects()

    def test_loads_source_vm(self, monkeypatch, db_session, system_user):
        tpl = _make_template(db_session, system_user)
        vm = _make_vm(db_session, system_user)
        pt, _, _ = _make_pt(monkeypatch, db_session=db_session, template_id=tpl.id)
        pt.db = db_session
        pt.source_vm_id = vm.id

        pt._get_vm_and_template_objects()

        assert pt.source_vm is not None
        assert pt.source_vm.id == vm.id


# ===========================================================================
# TestJobGet
# ===========================================================================
class TestJobGet:
    """_job_get fetches return_value from a completed RQ job."""

    def test_job_fetch_success(self, monkeypatch):
        pt, _, _ = _make_pt(monkeypatch)
        mock_job = MagicMock()
        # Job.fetch(...) returns a Job, .return_value() calls a method.
        # MagicMock's return_value collides with the method name, so we
        # need 3 levels: fetch() -> job_mock -> .return_value() -> result
        mock_job.return_value.return_value.return_value = {"vmid": 200}
        monkeypatch.setattr("pve.templates.Job.fetch", mock_job)

        result = pt._job_get("test-job-id")

        assert result == {"vmid": 200}

    def test_job_fetch_none_returns_fail(self, monkeypatch):
        pt, mock_crud, _ = _make_pt(monkeypatch)
        mock_job = MagicMock()
        mock_job.return_value.return_value.return_value = None
        monkeypatch.setattr("pve.templates.Job.fetch", mock_job)

        pt._job_get("test-job-id")

        mock_crud.worker_process_fail.assert_called_once()

    def test_job_fetch_exception_returns_fail(self, monkeypatch):
        pt, mock_crud, _ = _make_pt(monkeypatch)
        monkeypatch.setattr(
            "pve.templates.Job.fetch", MagicMock(side_effect=Exception("redis down"))
        )

        pt._job_get("test-job-id")

        mock_crud.worker_process_fail.assert_called_once()


# ===========================================================================
# TestMergePveAndKvsTags
# ===========================================================================
class TestMergePveAndKvsTags:
    """_merge_pve_and_kvs_tags merges and deduplicates tags."""

    def test_openvle_tags_only(self, monkeypatch):
        pt, _, _ = _make_pt(monkeypatch)
        pt.db = MagicMock()
        mock_crud_tag = MagicMock()
        mock_crud_tag._convert_kvs_to_pve.return_value = ["beta", "alpha"]
        monkeypatch.setattr(
            "pve.templates.CRUDTag", MagicMock(return_value=mock_crud_tag)
        )

        result = pt._merge_pve_and_kvs_tags(
            proxmox_id=9000, kvs_template_id=uuid.uuid4()
        )

        assert result == "alpha,beta"

    def test_deduplication(self, monkeypatch):
        pt, _, _ = _make_pt(monkeypatch)
        pt.db = MagicMock()
        pt._pve_config_get = MagicMock(return_value={"tags": "shared;pve-only"})
        mock_crud_tag = MagicMock()
        mock_crud_tag._convert_kvs_to_pve.return_value = ["shared", "kvs-only"]
        monkeypatch.setattr(
            "pve.templates.CRUDTag", MagicMock(return_value=mock_crud_tag)
        )

        result = pt._merge_pve_and_kvs_tags(
            proxmox_id=9000, kvs_template_id=uuid.uuid4(), pve_tags_merge=True
        )
        tags = result.split(",")
        assert tags.count("shared") == 1

    def test_tag_removal(self, monkeypatch):
        pt, _, _ = _make_pt(monkeypatch)
        pt.db = MagicMock()
        mock_crud_tag = MagicMock()
        mock_crud_tag._convert_kvs_to_pve.return_value = ["keep", "remove-me"]
        monkeypatch.setattr(
            "pve.templates.CRUDTag", MagicMock(return_value=mock_crud_tag)
        )

        result = pt._merge_pve_and_kvs_tags(
            proxmox_id=9000,
            kvs_template_id=uuid.uuid4(),
            tag_to_remove="remove-me",
        )

        assert "remove-me" not in result
        assert "keep" in result


# ===========================================================================
# TestPveUpdateAndDelete
# ===========================================================================
class TestPveUpdateAndDelete:
    """_pve_update and _pve_delete interact with PVE API."""

    def test_update_success(self, monkeypatch, db_session, system_user):
        tpl = _make_template(db_session, system_user, cpu=4, ram=8192, proxmoxId=9000)
        pt, _, _ = _make_pt(monkeypatch, db_session=db_session, template_id=tpl.id)
        pt.db = db_session
        pt.kvs_template = tpl
        pt.proxmox = MagicMock()

        pt._pve_update()

        pt.proxmox.nodes.return_value.qemu.return_value.config.put.assert_called_once()

    def test_update_exception(self, monkeypatch, db_session, system_user):
        tpl = _make_template(db_session, system_user, proxmoxId=9000)
        pt, mock_crud, _ = _make_pt(
            monkeypatch, db_session=db_session, template_id=tpl.id
        )
        pt.db = db_session
        pt.kvs_template = tpl
        pt.proxmox = MagicMock()
        pt.proxmox.nodes.return_value.qemu.return_value.config.put.side_effect = (
            RuntimeError("update failed")
        )

        pt._pve_update()

        mock_crud.worker_process_fail.assert_called_once()

    def test_delete_success(self, monkeypatch, db_session, system_user):
        tpl = _make_template(db_session, system_user, proxmoxId=9000)
        pt, _, _ = _make_pt(monkeypatch, db_session=db_session, template_id=tpl.id)
        pt.db = db_session
        pt.kvs_template = tpl
        pt.proxmox = MagicMock()
        pt.proxmox.nodes.return_value.qemu.return_value.delete.return_value = (
            "UPID:delete"
        )

        pt._pve_delete()

        assert pt.pve_task == "UPID:delete"

    def test_delete_no_proxmox_id_marks_success(
        self, monkeypatch, db_session, system_user
    ):
        """_pve_delete skips PVE when proxmoxId is None and marks task as success."""
        tpl = _make_template(db_session, system_user, proxmoxId=None)
        pt, _, mock_cluster = _make_pt(
            monkeypatch, db_session=db_session, template_id=tpl.id
        )
        pt.db = db_session
        pt.kvs_template = tpl
        pt.proxmox = MagicMock()

        pt._pve_delete()

        assert pt.pve_task_success is True
        pt.proxmox.nodes.assert_not_called()

    def test_delete_resource_exception_calls_kvs_delete(
        self, monkeypatch, db_session, system_user
    ):
        """ResourceException during PVE delete still cleans up DB."""
        tpl = _make_template(db_session, system_user, proxmoxId=9000)
        pt, mock_crud, _ = _make_pt(
            monkeypatch, db_session=db_session, template_id=tpl.id
        )
        pt.db = db_session
        pt.kvs_template = tpl
        pt.proxmox = MagicMock()
        pt.proxmox.nodes.return_value.qemu.return_value.delete.side_effect = (
            ResourceException(404, "not found", "")
        )

        pt._pve_delete()

        assert pt.pve_task_success is True
        mock_crud.worker_process_success.assert_called_once()


# ===========================================================================
# TestKvsTemplateDelete
# ===========================================================================
class TestKvsTemplateDelete:
    """_kvs_template_delete removes template from database."""

    def test_success(self, monkeypatch, db_session, system_user):
        tpl = _make_template(db_session, system_user)
        pt, _, _ = _make_pt(monkeypatch, db_session=db_session, template_id=tpl.id)
        pt.db = db_session
        pt.kvs_template = tpl

        pt._kvs_template_delete()

        # Template should be deleted from DB
        from models.templates import Template

        assert db_session.get(Template, tpl.id) is None

    def test_failure_sets_status_deleted(self, monkeypatch, db_session, system_user):
        """If DB delete fails, template status is set to 'deleted'."""
        tpl = _make_template(db_session, system_user)
        pt, mock_crud, _ = _make_pt(
            monkeypatch, db_session=db_session, template_id=tpl.id
        )
        pt.db = db_session
        pt.kvs_template = tpl

        # Force db.delete to fail
        original_delete = db_session.delete

        def fail_delete(obj):
            raise RuntimeError("FK constraint")

        db_session.delete = fail_delete

        pt._kvs_template_delete()

        db_session.delete = original_delete

        assert tpl.status == "deleted"
        assert tpl.proxmoxId is None
        mock_crud.worker_process_fail.assert_called_once()


# ===========================================================================
# TestHighLevelWorkflows
# ===========================================================================
class TestHighLevelWorkflows:
    """High-level async workflow methods."""

    @pytest.mark.anyio
    async def test_delete_prevent_delete(self, monkeypatch, db_session, system_user):
        """delete() returns failure when prevent_delete is True."""
        _, st = _make_task_and_subtask(db_session, system_user)
        tpl = _make_template(db_session, system_user, prevent_delete=True)
        pt, mock_crud, _ = _make_pt(
            monkeypatch, db_session=db_session, task_id=st.id, template_id=tpl.id
        )

        await pt.delete()

        mock_crud.worker_process_fail.assert_called_once()
        args = mock_crud.worker_process_fail.call_args[0]
        assert args[1] == 403

    @pytest.mark.anyio
    async def test_delete_proceeds_when_pve_config_raises_resource_exception(
        self, monkeypatch, db_session, system_user
    ):
        """delete() proceeds with deletion when PVE config fetch raises ResourceException.

        A broken template (not present on PVE) raises ResourceException during the
        protection check — we treat it as not-protected and proceed.
        """
        _, st = _make_task_and_subtask(db_session, system_user)
        tpl = _make_template(db_session, system_user, proxmoxId=9000)
        pt, mock_crud, mock_cluster = _make_pt(
            monkeypatch, db_session=db_session, task_id=st.id, template_id=tpl.id
        )

        # PVE config fetch raises ResourceException (e.g. 501 Not Implemented)
        mock_cluster.proxmox.nodes.return_value.qemu.return_value.config.get.side_effect = ResourceException(
            501, "Not Implemented", ""
        )
        # _pve_delete and _kvs_template_delete are not the focus — stub them out
        pt._pve_delete = MagicMock()
        pt._kvs_template_delete = MagicMock()
        pt.pve_task_success = True

        await pt.delete()

        # Must NOT call worker_process_fail with 502 (old behaviour)
        for call in mock_crud.worker_process_fail.call_args_list:
            assert call[0][1] != 502, (
                "Should not fail with 502 for missing PVE resource"
            )
        pt._pve_delete.assert_called_once()

    @pytest.mark.anyio
    async def test_delete_no_proxmox_id_proceeds(
        self, monkeypatch, db_session, system_user
    ):
        """delete() skips PVE protection check and deletes when proxmoxId is None."""
        _, st = _make_task_and_subtask(db_session, system_user)
        tpl = _make_template(db_session, system_user, proxmoxId=None)
        pt, mock_crud, _ = _make_pt(
            monkeypatch, db_session=db_session, task_id=st.id, template_id=tpl.id
        )
        pt._pve_delete = MagicMock()
        pt._kvs_template_delete = MagicMock()
        pt.pve_task_success = True

        await pt.delete()

        pt._pve_delete.assert_called_once()
        mock_crud.worker_process_success.assert_called_once()
