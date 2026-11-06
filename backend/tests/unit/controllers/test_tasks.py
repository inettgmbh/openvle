"""Tests for controllers/tasks.py - CRUDTask operations."""

import uuid
from datetime import datetime, timezone

import pytest
from controllers.tasks import CRUDTask
from core.exceptions import ObjectNotFound
from models import Event, Task
from schemas.tasks import TaskCreate

from tests.helpers.mock_request import create_mock_request


class TestCRUDTaskCreate:
    def setup_method(self):
        self.crud = CRUDTask(Task)

    def test_create_task_without_event(self, db_session, active_user):
        """Creating a task without an event_id should succeed."""
        request = create_mock_request(active_user)
        obj_in = TaskCreate(name="Simple Task", event_id=None)
        result = self.crud.create(db_session, request, obj_in=obj_in)

        assert result is not None
        assert isinstance(result.id, uuid.UUID)
        assert result.name == "Simple Task"
        assert result.status == "queued"
        assert result.event_id is None

    def test_create_task_sets_audit_fields(self, db_session, active_user):
        """Created task should have audit fields set from the request user."""
        request = create_mock_request(active_user)
        obj_in = TaskCreate(name="Audit Task", event_id=None)
        result = self.crud.create(db_session, request, obj_in=obj_in)

        assert result.createdById == active_user.id
        assert result.updatedById == active_user.id
        assert result.createdAt is not None
        assert result.updatedAt is not None

    def test_create_task_with_valid_event(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
    ):
        """Creating a task with a valid event_id should link the task to the event."""
        now = datetime.now(timezone.utc)
        planned_status = event_statuses["Geplant"]

        event = Event(
            id=uuid.uuid4(),
            name="Task Event",
            slug="tsk-evnt",
            dateStart=now.date(),
            dateEnd=now.date(),
            status=planned_status.id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(event)
        db_session.flush()

        request = create_mock_request(active_user)
        obj_in = TaskCreate(name="Event Task", event_id=event.id)
        result = self.crud.create(db_session, request, obj_in=obj_in)

        assert result.event_id == event.id

    def test_create_task_with_nonexistent_event_raises(
        self, db_session, active_user
    ):
        """Creating a task with a non-existent event_id should raise ObjectNotFound."""
        request = create_mock_request(active_user)
        fake_event_id = uuid.uuid4()
        obj_in = TaskCreate(name="Bad Event Task", event_id=fake_event_id)

        with pytest.raises(ObjectNotFound):
            self.crud.create(db_session, request, obj_in=obj_in)

    def test_create_task_default_status_is_queued(
        self, db_session, active_user
    ):
        """Default status for a new task should be 'queued'."""
        request = create_mock_request(active_user)
        obj_in = TaskCreate(name="Default Status Task", event_id=None)
        result = self.crud.create(db_session, request, obj_in=obj_in)

        assert result.status == "queued"

    def test_create_task_persisted_to_db(self, db_session, active_user):
        """The created task should be retrievable from the database."""
        request = create_mock_request(active_user)
        obj_in = TaskCreate(name="Persisted Task", event_id=None)
        result = self.crud.create(db_session, request, obj_in=obj_in)

        db_obj = db_session.get(Task, result.id)
        assert db_obj is not None
        assert db_obj.name == "Persisted Task"

    def test_create_task_with_system_user(self, db_session, system_user):
        """Creating a task with the system user request should work."""
        request = create_mock_request(system_user)
        obj_in = TaskCreate(name="System Task", event_id=None)
        result = self.crud.create(db_session, request, obj_in=obj_in)

        assert result is not None
        assert result.createdById == system_user.id
