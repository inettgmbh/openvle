"""Tests for core/mail_automated.py - System-triggered mail handling."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from models import (
    Event,
    Language,
    ObjectPermission,
    SubTask,
    Task,
    VirtualMachine,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def sample_language(db_session, system_user):
    return db_session.query(Language).filter_by(key="de_DE").one()


def _make_task(db, system_user, event_id=None):
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


def _make_subtask(
    db,
    system_user,
    parent_task,
    object_type,
    object_id,
    action,
    status="success",
):
    now = datetime.now(timezone.utc)
    subtask = SubTask(
        id=uuid.uuid4(),
        name="test-subtask",
        status=status,
        object_type=object_type,
        object_id=str(object_id),
        action=action,
        attempt="1",
        parent_task=parent_task.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(subtask)
    db.flush()
    return subtask


def _make_vm(db, system_user, event_id=None, users=None):
    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name="test-vm",
        cpu=2,
        ram=4096,
        disk=50,
        status="running",
        event=event_id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(vm)
    db.flush()
    if users:
        for user in users:
            vm.users.append(user)
        db.flush()
    return vm


def _make_event(db, system_user, event_statuses, sample_course):
    now = datetime.now(timezone.utc)
    event = Event(
        id=uuid.uuid4(),
        name=f"test-event-{uuid.uuid4().hex[:6]}",
        slug=uuid.uuid4().hex[:8],
        dateStart=now.date(),
        dateEnd=now.date(),
        guacamole=True,
        status=event_statuses["Geplant"].id,
        course=sample_course.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(event)
    db.flush()
    return event


# ---------------------------------------------------------------------------
# Tests: get_object_owners
# ---------------------------------------------------------------------------
class TestGetObjectOwners:
    def test_returns_users_with_permissions(
        self, db_session, system_user, active_user
    ):
        """Users with ObjectPermission for an object are returned."""
        from core.mail_automated import get_object_owners

        vm_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="VirtualMachine",
            object_id=vm_id,
            entity_type="User",
            entity_id=active_user.id,
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(perm)
        db_session.flush()

        owners = get_object_owners(db_session, vm_id, "VirtualMachine")
        owner_ids = [u.id for u in owners]
        assert active_user.id in owner_ids

    def test_empty_when_no_permissions(self, db_session, system_user):
        """No permissions -> empty result."""
        from core.mail_automated import get_object_owners

        owners = get_object_owners(db_session, uuid.uuid4(), "VirtualMachine")
        assert owners.count() == 0


# ---------------------------------------------------------------------------
# Tests: system_triggered_mail_handler
# ---------------------------------------------------------------------------
class TestSystemTriggeredMailHandler:
    """Test that system_triggered_mail_handler routes to correct mail slug."""

    def _patch_all(self, monkeypatch, db_session):
        """Patch SessionLocal and CRUDMail.create_system_mail."""
        monkeypatch.setattr(
            "core.mail_automated.SessionLocal", lambda: db_session
        )
        self._create_system_mail_calls = []

        def fake_create_system_mail(
            self_crud,
            db,
            *,
            mail_action_slug,
            user,
            context_objects=None,
            event_id=None,
        ):
            self._create_system_mail_calls.append(
                {
                    "slug": mail_action_slug,
                    "user": user,
                    "context_objects": context_objects,
                    "event_id": event_id,
                }
            )
            return MagicMock()

        # Patch on the class
        from controllers.mails import CRUDMail

        monkeypatch.setattr(
            CRUDMail, "create_system_mail", fake_create_system_mail
        )

    def test_vm_create_success_sends_mail(
        self, db_session, system_user, active_user, monkeypatch
    ):
        """SubTask VirtualMachine/vm_clone/success -> slug 'vm_create_success'."""
        self._patch_all(monkeypatch, db_session)

        vm = _make_vm(db_session, system_user, users=[active_user])
        task = _make_task(db_session, system_user)
        subtask = _make_subtask(
            db_session,
            system_user,
            task,
            object_type="VirtualMachine",
            object_id=vm.id,
            action="vm_clone",
            status="success",
        )

        from core.mail_automated import system_triggered_mail_handler

        system_triggered_mail_handler(subtask.id)

        assert len(self._create_system_mail_calls) >= 1
        slugs = [c["slug"] for c in self._create_system_mail_calls]
        assert "vm_create_success" in slugs

    def test_vm_create_failed_sends_mail(
        self, db_session, system_user, active_user, monkeypatch
    ):
        """SubTask VirtualMachine/vm_clone/failed -> slug 'vm_create_failed'."""
        self._patch_all(monkeypatch, db_session)

        vm = _make_vm(db_session, system_user, users=[active_user])
        task = _make_task(db_session, system_user)
        subtask = _make_subtask(
            db_session,
            system_user,
            task,
            object_type="VirtualMachine",
            object_id=vm.id,
            action="vm_clone",
            status="failed",
        )

        from core.mail_automated import system_triggered_mail_handler

        system_triggered_mail_handler(subtask.id)

        slugs = [c["slug"] for c in self._create_system_mail_calls]
        assert "vm_create_failed" in slugs

    def test_vm_delete_failed_sends_mail(
        self, db_session, system_user, active_user, monkeypatch
    ):
        """SubTask VirtualMachine/vm_delete/failed -> slug 'vm_delete_failed'."""
        self._patch_all(monkeypatch, db_session)

        vm = _make_vm(db_session, system_user)
        # Create ObjectPermission so get_object_owners returns a user
        now = datetime.now(timezone.utc)
        perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="VirtualMachine",
            object_id=vm.id,
            entity_type="User",
            entity_id=active_user.id,
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(perm)
        db_session.flush()

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(
            db_session,
            system_user,
            task,
            object_type="VirtualMachine",
            object_id=vm.id,
            action="vm_delete",
            status="failed",
        )

        from core.mail_automated import system_triggered_mail_handler

        system_triggered_mail_handler(subtask.id)

        slugs = [c["slug"] for c in self._create_system_mail_calls]
        assert "vm_delete_failed" in slugs

    def test_event_deployment_success_sends_mail(
        self,
        db_session,
        system_user,
        active_user,
        event_statuses,
        sample_course,
        monkeypatch,
    ):
        """SubTask Event/events_post_deployment/success -> slug 'events_post_deployment_success'."""
        self._patch_all(monkeypatch, db_session)

        event = _make_event(
            db_session, system_user, event_statuses, sample_course
        )
        task = _make_task(db_session, system_user, event_id=event.id)
        subtask = _make_subtask(
            db_session,
            system_user,
            task,
            object_type="Event",
            object_id=event.id,
            action="events_post_deployment",
            status="success",
        )

        # Mock get_event_admin to return empty list (no admin)
        from controllers.events import CRUDEvent

        monkeypatch.setattr(
            CRUDEvent, "get_event_admin", lambda self, db, id: []
        )

        from core.mail_automated import system_triggered_mail_handler

        system_triggered_mail_handler(subtask.id)

        slugs = [c["slug"] for c in self._create_system_mail_calls]
        assert "events_post_deployment_success" in slugs

    def test_event_deployment_failed_sends_mail(
        self,
        db_session,
        system_user,
        active_user,
        event_statuses,
        sample_course,
        monkeypatch,
    ):
        """SubTask Event/events_post_deployment/failed -> slug 'events_post_deployment_failed'."""
        self._patch_all(monkeypatch, db_session)

        event = _make_event(
            db_session, system_user, event_statuses, sample_course
        )
        task = _make_task(db_session, system_user, event_id=event.id)
        subtask = _make_subtask(
            db_session,
            system_user,
            task,
            object_type="Event",
            object_id=event.id,
            action="events_post_deployment",
            status="failed",
        )

        from controllers.events import CRUDEvent

        monkeypatch.setattr(
            CRUDEvent, "get_event_admin", lambda self, db, id: []
        )

        from core.mail_automated import system_triggered_mail_handler

        system_triggered_mail_handler(subtask.id)

        slugs = [c["slug"] for c in self._create_system_mail_calls]
        assert "events_post_deployment_failed" in slugs

    def test_event_decommission_success_sends_mail(
        self,
        db_session,
        system_user,
        active_user,
        event_statuses,
        sample_course,
        monkeypatch,
    ):
        """SubTask Event/events_post_decommission/success -> slug 'events_post_decommission_success'."""
        self._patch_all(monkeypatch, db_session)

        event = _make_event(
            db_session, system_user, event_statuses, sample_course
        )
        task = _make_task(db_session, system_user, event_id=event.id)
        subtask = _make_subtask(
            db_session,
            system_user,
            task,
            object_type="Event",
            object_id=event.id,
            action="events_post_decommission",
            status="success",
        )

        from controllers.events import CRUDEvent

        monkeypatch.setattr(
            CRUDEvent, "get_event_admin", lambda self, db, id: []
        )

        from core.mail_automated import system_triggered_mail_handler

        system_triggered_mail_handler(subtask.id)

        slugs = [c["slug"] for c in self._create_system_mail_calls]
        assert "events_post_decommission_success" in slugs

    def test_event_decommission_failed_sends_mail(
        self,
        db_session,
        system_user,
        active_user,
        event_statuses,
        sample_course,
        monkeypatch,
    ):
        """SubTask Event/events_post_decommission/failed -> slug 'events_post_decommission_failed'."""
        self._patch_all(monkeypatch, db_session)

        event = _make_event(
            db_session, system_user, event_statuses, sample_course
        )
        task = _make_task(db_session, system_user, event_id=event.id)
        subtask = _make_subtask(
            db_session,
            system_user,
            task,
            object_type="Event",
            object_id=event.id,
            action="events_post_decommission",
            status="failed",
        )

        from controllers.events import CRUDEvent

        monkeypatch.setattr(
            CRUDEvent, "get_event_admin", lambda self, db, id: []
        )

        from core.mail_automated import system_triggered_mail_handler

        system_triggered_mail_handler(subtask.id)

        slugs = [c["slug"] for c in self._create_system_mail_calls]
        assert "events_post_decommission_failed" in slugs
