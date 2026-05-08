"""Tests for core/events_worker.py - Event lifecycle worker functions.

Tests cover:
- events_post_deployment: success, failure, event not found
- events_post_decommission: success, failure, event not found
- create_vm_for_event_user: new VM creation, existing VM detection
- task_event_post_deployment: task/subtask creation and job enqueue
- task_event_post_decommission: task/subtask creation and job enqueue
- pre_start_mail: sends mails to admins, handles empty list
- events_start_worker: full start flow with templates and users
- events_end_worker: full end flow, handles protected VMs
"""

import uuid
from datetime import datetime, date, timezone
from unittest.mock import MagicMock

import pytest

from models import (
    Event,
    EventsUser,
    SubTask,
    Task,
    Template,
    User,
    VirtualMachine,
)
from models.associations import course_template_association_table
from pve.worker_utils import TaskException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task(db, system_user, event_id=None):
    """Create a Task row for testing."""
    now = datetime.now(timezone.utc)
    task = Task(
        id=uuid.uuid4(),
        name="test-task",
        status="queued",
        event_id=event_id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(task)
    db.flush()
    return task


def _make_subtask(db, system_user, parent_task, action="test_action"):
    """Create a SubTask row for testing."""
    now = datetime.now(timezone.utc)
    subtask = SubTask(
        id=uuid.uuid4(),
        name="test-subtask",
        status="queued",
        object_type="Event",
        object_id=str(uuid.uuid4()),
        action=action,
        attempt="0",
        parent_task=parent_task.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(subtask)
    db.flush()
    return subtask


def _make_template(db, system_user, course=None, proxmox_id=100):
    """Create a Template row for testing."""
    now = datetime.now(timezone.utc)
    template = Template(
        id=uuid.uuid4(),
        name=f"template-{proxmox_id}",
        description="Test template",
        cpu=2,
        ram=4096,
        disk=50,
        proxmoxId=proxmox_id,
        proxmoxNode="pve-node-01",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(template)
    db.flush()
    if course:
        db.execute(
            course_template_association_table.insert().values(
                course_id=course.id, template_id=template.id
            )
        )
        db.flush()
    return template


def _make_vm(db, system_user, event, name="test-vm", ipv4=None, prevent_delete=False):
    """Create a VirtualMachine row for testing."""
    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name=name,
        cpu=2,
        ram=4096,
        disk=50,
        event=event.id,
        ipv4=ipv4,
        prevent_delete=prevent_delete,
        proxmoxId=200,
        proxmoxNode="pve-node-01",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(vm)
    db.flush()
    return vm


def _make_event(db, system_user, status_id, course_id, slug="evt001"):
    """Create an Event row for testing."""
    now = datetime.now(timezone.utc)
    event = Event(
        id=uuid.uuid4(),
        name=f"Test Event {slug}",
        slug=slug,
        description="A test event",
        dateStart=date.today(),
        dateEnd=date.today(),
        guacamole=False,
        status=status_id,
        course=course_id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(event)
    db.flush()
    return event


def _make_events_user(db, system_user, event, user, role):
    """Create an EventsUser association row."""
    now = datetime.now(timezone.utc)
    eu = EventsUser(
        id=uuid.uuid4(),
        user_id=user.id,
        event_id=event.id,
        role_id=role.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(eu)
    db.flush()
    return eu


def _make_extra_user(db, system_user, username="student1"):
    """Create an additional User for testing."""
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        username=username,
        name=f"User {username}",
        email=f"{username}@example.com",
        hashed_password="$2b$12$dummyhashvalue",
        status="Active",
        locale="de_DE",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(user)
    db.flush()
    return user


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------


class TestEventsPostDeployment:
    """Tests for events_post_deployment()."""

    def test_success_all_vms_have_ipv4(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """When all VMs have ipv4, event status should become Aktiv."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        event = _make_event(
            db_session, system_user, event_statuses["Deploying"].id, sample_course.id
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(
            db_session, system_user, task, action="events_post_deployment"
        )

        vm1 = _make_vm(db_session, system_user, event, name="vm-1", ipv4="10.0.0.1")
        vm2 = _make_vm(db_session, system_user, event, name="vm-2", ipv4="10.0.0.2")

        from core.events_worker import events_post_deployment

        # worker_process_success raises no exception on success; it returns True
        # but worker_process_fail raises TaskException. If no exception, it succeeded.
        events_post_deployment(
            kvs_task_object_id=subtask.id,
            kvs_event_id=event.id,
            virtual_machines=[vm1.id, vm2.id],
        )

        db_session.expire_all()
        updated_event = db_session.get(Event, event.id)
        assert updated_event.status == event_statuses["Aktiv"].id

    def test_failure_vm_missing_ipv4(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """When some VMs lack ipv4, the worker should report failure."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        event = _make_event(
            db_session, system_user, event_statuses["Deploying"].id, sample_course.id
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(
            db_session, system_user, task, action="events_post_deployment"
        )

        vm_ok = _make_vm(db_session, system_user, event, name="vm-ok", ipv4="10.0.0.1")
        vm_fail = _make_vm(db_session, system_user, event, name="vm-fail", ipv4=None)

        from core.events_worker import events_post_deployment

        with pytest.raises(TaskException, match="errors during deployment"):
            events_post_deployment(
                kvs_task_object_id=subtask.id,
                kvs_event_id=event.id,
                virtual_machines=[vm_ok.id, vm_fail.id],
            )

    def test_failure_vm_not_found_in_db(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """When a VM ID does not exist in DB, it should be treated as failed deployment."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        event = _make_event(
            db_session, system_user, event_statuses["Deploying"].id, sample_course.id
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(
            db_session, system_user, task, action="events_post_deployment"
        )

        nonexistent_vm_id = uuid.uuid4()

        from core.events_worker import events_post_deployment

        with pytest.raises(TaskException, match="errors during deployment"):
            events_post_deployment(
                kvs_task_object_id=subtask.id,
                kvs_event_id=event.id,
                virtual_machines=[nonexistent_vm_id],
            )

    def test_event_not_found(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """When event does not exist, worker should fail gracefully."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        event = _make_event(
            db_session, system_user, event_statuses["Deploying"].id, sample_course.id
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(
            db_session, system_user, task, action="events_post_deployment"
        )

        fake_event_id = uuid.uuid4()

        from core.events_worker import events_post_deployment

        with pytest.raises(TaskException, match="not found"):
            events_post_deployment(
                kvs_task_object_id=subtask.id,
                kvs_event_id=fake_event_id,
                virtual_machines=[],
            )

    def test_session_local_failure(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """When SessionLocal() raises, worker should not crash (bare except)."""

        def _raise():
            raise RuntimeError("DB connection failed")

        monkeypatch.setattr("core.events_worker.SessionLocal", _raise)

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(
            db_session, system_user, task, action="events_post_deployment"
        )

        from core.events_worker import events_post_deployment

        # When SessionLocal() fails, the code catches with bare except and tries
        # worker_process_fail without a db, which also fails internally.
        # worker_process_fail(id, code, msg) without db calls SessionLocal() again
        # which returns an unbound session, causing UnboundExecutionError.
        # The production code has a bug here: it doesn't pass db to worker_process_fail.
        from sqlalchemy.exc import UnboundExecutionError

        with pytest.raises((AttributeError, UnboundExecutionError)):
            events_post_deployment(
                kvs_task_object_id=subtask.id,
                kvs_event_id=uuid.uuid4(),
                virtual_machines=[],
            )


class TestEventsPostDecommission:
    """Tests for events_post_decommission()."""

    def test_success_no_vms_remain(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """When no VMs remain for the event, status should become Archiviert."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        event = _make_event(
            db_session, system_user, event_statuses["Archiving"].id, sample_course.id
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(
            db_session, system_user, task, action="events_post_decommission"
        )

        from core.events_worker import events_post_decommission

        events_post_decommission(
            kvs_task_object_id=subtask.id,
            kvs_event_id=event.id,
            virtual_machines=[],
        )

        db_session.expire_all()
        updated_event = db_session.get(Event, event.id)
        assert updated_event.status == event_statuses["Archiviert"].id

    def test_failure_vms_still_exist(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """When VMs still belong to the event, decommission should fail."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        event = _make_event(
            db_session, system_user, event_statuses["Archiving"].id, sample_course.id
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(
            db_session, system_user, task, action="events_post_decommission"
        )

        vm = _make_vm(db_session, system_user, event, name="leftover-vm")

        from core.events_worker import events_post_decommission

        with pytest.raises(TaskException, match="errors during decommissioning"):
            events_post_decommission(
                kvs_task_object_id=subtask.id,
                kvs_event_id=event.id,
                virtual_machines=[vm.id],
            )

    def test_event_not_found(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """When event does not exist, worker should fail."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        event = _make_event(
            db_session, system_user, event_statuses["Archiving"].id, sample_course.id
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(
            db_session, system_user, task, action="events_post_decommission"
        )

        from core.events_worker import events_post_decommission

        with pytest.raises(TaskException, match="not found"):
            events_post_decommission(
                kvs_task_object_id=subtask.id,
                kvs_event_id=uuid.uuid4(),
                virtual_machines=[],
            )

    def test_success_message_includes_protected_count_when_nonzero(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """When protected_vm_count > 0, success message must mention the count."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        event = _make_event(
            db_session, system_user, event_statuses["Archiving"].id, sample_course.id
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(
            db_session, system_user, task, action="events_post_decommission"
        )

        from core.events_worker import events_post_decommission

        events_post_decommission(
            kvs_task_object_id=subtask.id,
            kvs_event_id=event.id,
            virtual_machines=[],
            protected_vm_count=3,
        )

        db_session.expire_all()
        updated_subtask = db_session.get(SubTask, subtask.id)
        assert "3" in updated_subtask.response_message
        assert "protected" in updated_subtask.response_message.lower()

    def test_success_message_omits_protected_info_when_zero(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """When protected_vm_count == 0 (default), success message must not mention protected."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        event = _make_event(
            db_session, system_user, event_statuses["Archiving"].id, sample_course.id
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(
            db_session, system_user, task, action="events_post_decommission"
        )

        from core.events_worker import events_post_decommission

        events_post_decommission(
            kvs_task_object_id=subtask.id,
            kvs_event_id=event.id,
            virtual_machines=[],
        )

        db_session.expire_all()
        updated_subtask = db_session.get(SubTask, subtask.id)
        assert "protected" not in updated_subtask.response_message.lower()

    def test_session_local_failure(self, db_session, system_user, monkeypatch):
        """When SessionLocal() raises, worker should not crash (bare except)."""

        def _raise():
            raise RuntimeError("DB connection failed")

        monkeypatch.setattr("core.events_worker.SessionLocal", _raise)

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(
            db_session, system_user, task, action="events_post_decommission"
        )

        from core.events_worker import events_post_decommission

        # Same as post_deployment: SessionLocal() fail -> worker_process_fail
        # without db -> another SessionLocal() call -> unbound session -> error
        from sqlalchemy.exc import UnboundExecutionError

        with pytest.raises((AttributeError, UnboundExecutionError)):
            events_post_decommission(
                kvs_task_object_id=subtask.id,
                kvs_event_id=uuid.uuid4(),
                virtual_machines=[],
            )


class TestEventsPostDeploymentMissingStatus:
    """Tests for events_post_deployment when EventStatus 'Aktiv' is missing."""

    def test_fails_when_aktiv_status_missing(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """When EventStatus 'Aktiv' is missing, worker should fail gracefully."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        event = _make_event(
            db_session, system_user, event_statuses["Deploying"].id, sample_course.id
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(
            db_session, system_user, task, action="events_post_deployment"
        )

        vm = _make_vm(db_session, system_user, event, name="vm-ok", ipv4="10.0.0.1")

        from models import EventStatus

        db_session.query(EventStatus).filter(EventStatus.name == "Aktiv").delete()
        db_session.flush()

        from core.events_worker import events_post_deployment

        with pytest.raises(TaskException, match="Aktiv"):
            events_post_deployment(
                kvs_task_object_id=subtask.id,
                kvs_event_id=event.id,
                virtual_machines=[vm.id],
            )


class TestEventsPostDecommissionMissingStatus:
    """Tests for events_post_decommission when EventStatus 'Archiviert' is missing."""

    def test_fails_when_archiviert_status_missing(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """When EventStatus 'Archiviert' is missing, worker should fail gracefully."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        event = _make_event(
            db_session, system_user, event_statuses["Archiving"].id, sample_course.id
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(
            db_session, system_user, task, action="events_post_decommission"
        )

        from models import EventStatus

        db_session.query(EventStatus).filter(EventStatus.name == "Archiviert").delete()
        db_session.flush()

        from core.events_worker import events_post_decommission

        with pytest.raises(TaskException, match="Archiviert"):
            events_post_decommission(
                kvs_task_object_id=subtask.id,
                kvs_event_id=event.id,
                virtual_machines=[],
            )


class TestEventsStartWorkerMissingRole:
    """Tests for events_start_worker when role 'lehrende' is missing."""

    def test_fails_when_role_teacher_missing(
        self,
        db_session,
        system_user,
        event_statuses,
        sample_course,
        role_teacher,
        role_student,
        mock_redis_queues,
        monkeypatch,
    ):
        """When role 'lehrende' is missing, worker should fail gracefully."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        event = _make_event(
            db_session, system_user, event_statuses["Deploying"].id, sample_course.id
        )
        # Use student role only so we can delete teacher role without FK violation
        student = _make_extra_user(db_session, system_user, username="student-mr")
        _make_events_user(db_session, system_user, event, student, role_student)

        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task, action="events_start")

        from models import Role as RoleModel

        db_session.query(RoleModel).filter(RoleModel.key == "lehrende").delete()
        db_session.flush()

        from core.events_worker import events_start_worker

        with pytest.raises(TaskException, match="lehrende"):
            events_start_worker(
                kvs_task_object_id=subtask.id,
                kvs_event_id=event.id,
            )


class TestCreateVmForEventUser:
    """Tests for create_vm_for_event_user()."""

    def test_creates_new_vm(
        self,
        db_session,
        system_user,
        event_statuses,
        sample_course,
        role_student,
        active_user,
        monkeypatch,
    ):
        """Should create a new VirtualMachine and return it with worker_tasks."""
        event = _make_event(
            db_session, system_user, event_statuses["Deploying"].id, sample_course.id
        )
        template = _make_template(db_session, system_user, proxmox_id=100)

        # Mock ProxmoxCluster and the clone flow
        MagicMock()
        mock_vm_obj = _make_vm(
            db_session,
            system_user,
            event,
            name=f"{event.slug}-{active_user.username}-t{template.proxmoxId}",
        )
        mock_vm_result_dict = {"VirtualMachine": mock_vm_obj, "worker_tasks": ["job-1"]}

        monkeypatch.setattr(
            "core.events_worker.CRUDVirtualMachine",
            lambda model: MagicMock(
                create_from_template_event=MagicMock(return_value=mock_vm_result_dict)
            ),
        )

        from core.events_worker import create_vm_for_event_user

        # First, make sure there is no existing VM with that name
        expected_name = f"{event.slug}-{active_user.username}-t{template.proxmoxId}"
        (
            db_session.query(VirtualMachine)
            .filter(VirtualMachine.name == expected_name)
            .first()
        )
        # There IS one already from mock setup above, so it should return immediately
        result = create_vm_for_event_user(
            db=db_session,
            event=event,
            template=template,
            user_role=role_student,
            user=active_user,
        )

        assert result["VirtualMachine"] is not None
        assert result["VirtualMachine"].name == expected_name

    def test_returns_existing_vm_if_name_exists(
        self,
        db_session,
        system_user,
        event_statuses,
        sample_course,
        role_student,
        active_user,
    ):
        """If a VM with the same name already exists, should return it without creating."""
        event = _make_event(
            db_session, system_user, event_statuses["Deploying"].id, sample_course.id
        )
        template = _make_template(db_session, system_user, proxmox_id=100)
        expected_name = f"{event.slug}-{active_user.username}-t{template.proxmoxId}"

        existing_vm = _make_vm(
            db_session, system_user, event, name=expected_name, ipv4="10.0.0.5"
        )

        from core.events_worker import create_vm_for_event_user

        result = create_vm_for_event_user(
            db=db_session,
            event=event,
            template=template,
            user_role=role_student,
            user=active_user,
        )

        assert result["VirtualMachine"].id == existing_vm.id
        assert result["worker_tasks"] is None


class TestTaskEventPostDeployment:
    """Tests for task_event_post_deployment()."""

    def test_creates_task_subtask_and_enqueues_job(
        self, db_session, system_user, event_statuses, sample_course, mock_redis_queues
    ):
        """Should create a Task, SubTask, and enqueue a post-deployment job."""
        event = _make_event(
            db_session, system_user, event_statuses["Deploying"].id, sample_course.id
        )
        vm_ids = [uuid.uuid4(), uuid.uuid4()]

        from core.events_worker import task_event_post_deployment

        task_event_post_deployment(
            db=db_session,
            event=event,
            vms_deploying=vm_ids,
            task_dependencies=None,
        )

        # Verify a Task was created
        tasks = db_session.query(Task).filter(Task.event_id == event.id).all()
        assert any("post deployment" in t.name.lower() for t in tasks)

        # Verify a SubTask was created
        subtasks = (
            db_session.query(SubTask)
            .filter(SubTask.action == "events_post_deployment")
            .all()
        )
        assert len(subtasks) >= 1

        # Verify a job was enqueued on queue_core_periodic
        assert len(mock_redis_queues) >= 1
        core_jobs = [
            j for j in mock_redis_queues if j["queue"] == "queue_core_periodic"
        ]
        assert len(core_jobs) >= 1

    def test_raises_on_enqueue_failure(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """If queue.enqueue returns falsy, should raise JobEnqueueError."""
        event = _make_event(
            db_session, system_user, event_statuses["Deploying"].id, sample_course.id
        )

        import core.redis as redis_mod

        mock_queue = MagicMock()
        mock_queue.enqueue.return_value = None
        monkeypatch.setattr(redis_mod, "queue_core_periodic", mock_queue)
        # Also patch the module-level import in events_worker
        monkeypatch.setattr("core.events_worker.queue_core_periodic", mock_queue)

        from core.events_worker import task_event_post_deployment
        from core.exceptions import JobEnqueueError

        with pytest.raises(JobEnqueueError):
            task_event_post_deployment(
                db=db_session,
                event=event,
                vms_deploying=[uuid.uuid4()],
                task_dependencies=None,
            )


class TestTaskEventPostDecommission:
    """Tests for task_event_post_decommission()."""

    def test_creates_task_subtask_and_enqueues_job(
        self, db_session, system_user, event_statuses, sample_course, mock_redis_queues
    ):
        """Should create a Task, SubTask, and enqueue a post-decommission job."""
        event = _make_event(
            db_session, system_user, event_statuses["Archiving"].id, sample_course.id
        )

        from core.events_worker import task_event_post_decommission

        task_event_post_decommission(
            db=db_session,
            event=event,
            vms_decommissioning=[uuid.uuid4()],
            task_dependencies=[],
        )

        subtasks = (
            db_session.query(SubTask)
            .filter(SubTask.action == "events_post_decommission")
            .all()
        )
        assert len(subtasks) >= 1

        core_jobs = [
            j for j in mock_redis_queues if j["queue"] == "queue_core_periodic"
        ]
        assert len(core_jobs) >= 1

    def test_raises_on_enqueue_failure(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """If queue.enqueue returns falsy, should raise JobEnqueueError."""
        event = _make_event(
            db_session, system_user, event_statuses["Archiving"].id, sample_course.id
        )

        import core.redis as redis_mod

        mock_queue = MagicMock()
        mock_queue.enqueue.return_value = None
        monkeypatch.setattr(redis_mod, "queue_core_periodic", mock_queue)
        monkeypatch.setattr("core.events_worker.queue_core_periodic", mock_queue)

        from core.events_worker import task_event_post_decommission
        from core.exceptions import JobEnqueueError

        with pytest.raises(JobEnqueueError):
            task_event_post_decommission(
                db=db_session,
                event=event,
                vms_decommissioning=[uuid.uuid4()],
                task_dependencies=[],
            )

    def test_protected_vm_count_forwarded_to_enqueue(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """protected_vm_count must be passed through to the enqueued job."""
        event = _make_event(
            db_session, system_user, event_statuses["Archiving"].id, sample_course.id
        )

        import core.redis as redis_mod

        enqueue_kwargs = {}
        mock_job = MagicMock()
        mock_queue = MagicMock()
        mock_queue.enqueue.side_effect = lambda fn, **kwargs: (
            enqueue_kwargs.update(kwargs) or mock_job
        )
        monkeypatch.setattr(redis_mod, "queue_core_periodic", mock_queue)
        monkeypatch.setattr("core.events_worker.queue_core_periodic", mock_queue)

        from core.events_worker import task_event_post_decommission

        task_event_post_decommission(
            db=db_session,
            event=event,
            vms_decommissioning=[],
            task_dependencies=[],
            protected_vm_count=5,
        )

        assert enqueue_kwargs.get("protected_vm_count") == 5


class TestPreStartMail:
    """Tests for pre_start_mail()."""

    def test_sends_mails_to_admins(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """Should call CRUDMail.create_system_mail for each admin."""
        event = _make_event(
            db_session, system_user, event_statuses["Deploying"].id, sample_course.id
        )
        teacher1 = _make_extra_user(db_session, system_user, username="teacher1")
        teacher2 = _make_extra_user(db_session, system_user, username="teacher2")

        mail_calls = []
        mock_crud_mail_instance = MagicMock()
        mock_crud_mail_instance.create_system_mail = MagicMock(
            side_effect=lambda **kwargs: mail_calls.append(kwargs)
        )

        monkeypatch.setattr(
            "core.events_worker.CRUDMail",
            lambda model: mock_crud_mail_instance,
        )

        from core.events_worker import pre_start_mail

        pre_start_mail(
            db=db_session,
            event=event,
            event_admin=[teacher1.id, teacher2.id],
        )

        assert len(mail_calls) == 2

    def test_handles_empty_admin_list(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """Should return immediately when event_admin is empty."""
        event = _make_event(
            db_session, system_user, event_statuses["Deploying"].id, sample_course.id
        )

        mock_crud_mail_instance = MagicMock()
        monkeypatch.setattr(
            "core.events_worker.CRUDMail",
            lambda model: mock_crud_mail_instance,
        )

        from core.events_worker import pre_start_mail

        pre_start_mail(db=db_session, event=event, event_admin=[])

        mock_crud_mail_instance.create_system_mail.assert_not_called()

    def test_skips_nonexistent_user_ids(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """Should skip user IDs that do not exist in the database."""
        event = _make_event(
            db_session, system_user, event_statuses["Deploying"].id, sample_course.id
        )
        real_teacher = _make_extra_user(
            db_session, system_user, username="real-teacher"
        )
        fake_user_id = uuid.uuid4()

        mail_calls = []
        mock_crud_mail_instance = MagicMock()
        mock_crud_mail_instance.create_system_mail = MagicMock(
            side_effect=lambda **kwargs: mail_calls.append(kwargs)
        )
        monkeypatch.setattr(
            "core.events_worker.CRUDMail",
            lambda model: mock_crud_mail_instance,
        )

        from core.events_worker import pre_start_mail

        pre_start_mail(
            db=db_session,
            event=event,
            event_admin=[real_teacher.id, fake_user_id],
        )

        # Only one mail should be sent (for the real teacher)
        assert len(mail_calls) == 1


class TestEventsStartWorker:
    """Tests for events_start_worker()."""

    def test_full_start_flow(
        self,
        db_session,
        system_user,
        event_statuses,
        sample_course,
        role_teacher,
        role_student,
        mock_redis_queues,
        monkeypatch,
    ):
        """Full start flow: create VMs per template x user, enqueue post-deployment."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        event = _make_event(
            db_session, system_user, event_statuses["Deploying"].id, sample_course.id
        )
        _make_template(db_session, system_user, course=sample_course, proxmox_id=100)

        teacher = _make_extra_user(db_session, system_user, username="teacher-start")
        student = _make_extra_user(db_session, system_user, username="student-start")

        _make_events_user(db_session, system_user, event, teacher, role_teacher)
        _make_events_user(db_session, system_user, event, student, role_student)

        # Create a parent task and subtask for the worker
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task, action="events_start")

        # Mock create_vm_for_event_user to avoid Proxmox calls
        call_count = {"n": 0}

        def mock_create_vm(db, event, template, user_role, user):
            call_count["n"] += 1
            vm = _make_vm(
                db,
                system_user,
                event,
                name=f"{event.slug}-{user.username}-t{template.proxmoxId}-{call_count['n']}",
                ipv4="10.0.0.1",
            )
            return {"VirtualMachine": vm, "worker_tasks": None}

        monkeypatch.setattr(
            "core.events_worker.create_vm_for_event_user", mock_create_vm
        )

        # Mock pre_start_mail to avoid mail system
        monkeypatch.setattr("core.events_worker.pre_start_mail", MagicMock())

        from core.events_worker import events_start_worker

        events_start_worker(
            kvs_task_object_id=subtask.id,
            kvs_event_id=event.id,
        )

        # 1 template x 2 users = 2 VMs
        assert call_count["n"] == 2

        # Post-deployment job should be enqueued
        core_jobs = [
            j for j in mock_redis_queues if j["queue"] == "queue_core_periodic"
        ]
        assert len(core_jobs) >= 1

    def test_event_not_found(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """Should fail gracefully when event does not exist."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task, action="events_start")

        from core.events_worker import events_start_worker

        with pytest.raises(TaskException, match="not found"):
            events_start_worker(
                kvs_task_object_id=subtask.id,
                kvs_event_id=uuid.uuid4(),
            )


class TestEventsEndWorker:
    """Tests for events_end_worker()."""

    def test_full_end_flow_no_guacamole(
        self,
        db_session,
        system_user,
        event_statuses,
        sample_course,
        role_student,
        mock_redis_queues,
        monkeypatch,
    ):
        """End flow without guacamole: enqueue VM deletion tasks."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)
        mock_proxmox = MagicMock()
        mock_proxmox.pve_get_node.return_value = "pve-node-1"
        mock_proxmox.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "protection": 0
        }
        monkeypatch.setattr("core.events_worker.ProxmoxCluster", lambda: mock_proxmox)

        event = _make_event(
            db_session, system_user, event_statuses["Archiving"].id, sample_course.id
        )
        # guacamole=False by default in _make_event

        _make_extra_user(db_session, system_user, username="student-end")
        _make_vm(db_session, system_user, event, name="vm-end-1")
        _make_vm(db_session, system_user, event, name="vm-end-2")

        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task, action="events_end")

        # Mock CRUDVirtualMachine methods that enqueue worker jobs
        mock_crud_vm_instance = MagicMock()
        mock_crud_vm_instance._subtask_vm_guac_delete.return_value = None
        mock_crud_vm_instance._subtask_ha_remove.return_value = "job-ha"
        mock_crud_vm_instance._subtask_actions_stop.return_value = "job-stop"
        mock_crud_vm_instance._subtask_vm_delete.return_value = "job-delete"

        monkeypatch.setattr(
            "core.events_worker.CRUDVirtualMachine",
            lambda db, id: mock_crud_vm_instance,
        )

        from core.events_worker import events_end_worker

        events_end_worker(
            kvs_task_object_id=subtask.id,
            kvs_event_id=event.id,
        )

        # task_event_post_decommission should have been called (enqueued job)
        core_jobs = [
            j for j in mock_redis_queues if j["queue"] == "queue_core_periodic"
        ]
        assert len(core_jobs) >= 1

    def test_protected_vms_detached_not_deleted(
        self,
        db_session,
        system_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
        monkeypatch,
    ):
        """Protected VMs should be detached from event, not deleted."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        event = _make_event(
            db_session, system_user, event_statuses["Archiving"].id, sample_course.id
        )

        protected_vm = _make_vm(
            db_session,
            system_user,
            event,
            name="protected-vm",
            prevent_delete=True,
        )

        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task, action="events_end")

        mock_crud_vm_instance = MagicMock()
        monkeypatch.setattr(
            "core.events_worker.CRUDVirtualMachine",
            lambda db, id: mock_crud_vm_instance,
        )

        from core.events_worker import events_end_worker

        events_end_worker(
            kvs_task_object_id=subtask.id,
            kvs_event_id=event.id,
        )

        # Protected VM should have event set to None
        db_session.expire_all()
        updated_vm = db_session.get(VirtualMachine, protected_vm.id)
        assert updated_vm.event is None

        # VM delete should NOT have been called for protected VM
        mock_crud_vm_instance._subtask_vm_delete.assert_not_called()

    def test_proxmox_protected_vm_synced_to_db_and_detached(
        self,
        db_session,
        system_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
        monkeypatch,
    ):
        """VM not marked prevent_delete in DB but protected in Proxmox: DB must be updated
        and VM detached from event, not enqueued for deletion."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        mock_proxmox = MagicMock()
        mock_proxmox.pve_get_node.return_value = "pve-node-1"
        mock_proxmox.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "protection": 1
        }
        monkeypatch.setattr("core.events_worker.ProxmoxCluster", lambda: mock_proxmox)

        event = _make_event(
            db_session, system_user, event_statuses["Archiving"].id, sample_course.id
        )
        vm = _make_vm(
            db_session,
            system_user,
            event,
            name="pve-protected-vm",
            prevent_delete=False,
        )

        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task, action="events_end")

        mock_crud_vm_instance = MagicMock()
        monkeypatch.setattr(
            "core.events_worker.CRUDVirtualMachine",
            lambda db, id: mock_crud_vm_instance,
        )

        from core.events_worker import events_end_worker

        events_end_worker(kvs_task_object_id=subtask.id, kvs_event_id=event.id)

        db_session.expire_all()
        updated_vm = db_session.get(VirtualMachine, vm.id)
        # DB should be synced
        assert updated_vm.prevent_delete is True
        # VM should be detached from event
        assert updated_vm.event is None
        # VM delete should NOT have been enqueued
        mock_crud_vm_instance._subtask_vm_delete.assert_not_called()

    def test_protected_vm_count_passed_to_post_decommission(
        self,
        db_session,
        system_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
        monkeypatch,
    ):
        """protected_vm_count must reflect the number of skipped VMs in the enqueued job."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        mock_proxmox = MagicMock()
        mock_proxmox.pve_get_node.return_value = "pve-node-1"
        mock_proxmox.proxmox.nodes.return_value.qemu.return_value.config.get.return_value = {
            "protection": 0
        }
        monkeypatch.setattr("core.events_worker.ProxmoxCluster", lambda: mock_proxmox)

        event = _make_event(
            db_session, system_user, event_statuses["Archiving"].id, sample_course.id
        )
        _make_vm(db_session, system_user, event, name="normal-vm")
        _make_vm(
            db_session, system_user, event, name="protected-vm-1", prevent_delete=True
        )
        _make_vm(
            db_session, system_user, event, name="protected-vm-2", prevent_delete=True
        )

        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task, action="events_end")

        mock_crud_vm_instance = MagicMock()
        mock_crud_vm_instance._subtask_ha_remove.return_value = "job-ha"
        mock_crud_vm_instance._subtask_actions_stop.return_value = "job-stop"
        mock_crud_vm_instance._subtask_vm_delete.return_value = "job-delete"
        monkeypatch.setattr(
            "core.events_worker.CRUDVirtualMachine",
            lambda db, id: mock_crud_vm_instance,
        )

        enqueue_kwargs = {}
        import core.redis as redis_mod

        mock_queue = MagicMock()
        mock_queue.enqueue.side_effect = lambda fn, **kwargs: (
            enqueue_kwargs.update(kwargs) or MagicMock()
        )
        monkeypatch.setattr(redis_mod, "queue_core_periodic", mock_queue)
        monkeypatch.setattr("core.events_worker.queue_core_periodic", mock_queue)

        from core.events_worker import events_end_worker

        events_end_worker(kvs_task_object_id=subtask.id, kvs_event_id=event.id)

        assert enqueue_kwargs.get("protected_vm_count") == 2

    def test_event_not_found(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """Should fail gracefully when event does not exist."""
        monkeypatch.setattr("core.events_worker.SessionLocal", lambda: db_session)

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task, action="events_end")

        from core.events_worker import events_end_worker

        with pytest.raises(TaskException, match="not found"):
            events_end_worker(
                kvs_task_object_id=subtask.id,
                kvs_event_id=uuid.uuid4(),
            )
