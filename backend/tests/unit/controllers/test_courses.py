"""Tests for controllers/courses.py - CRUDCourse operations."""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from controllers.courses import CRUDCourse
from core.exceptions import (
    BadRequestError,
    ObjectInUseError,
    ObjectNotFound,
)
from models import Course, Event, Template
from schemas.courses import CourseCreate, CourseUpdate, CourseUpdateTemplate

from tests.helpers.mock_request import create_mock_request


class TestCRUDCourseGetByName:
    def setup_method(self):
        self.crud = CRUDCourse(Course)

    def test_get_by_name_found(self, db_session, system_user, sample_course):
        result = self.crud.get_by_name(db_session, name="Test Course")
        assert result is not None
        assert result.name == "Test Course"

    def test_get_by_name_not_found(self, db_session, system_user):
        result = self.crud.get_by_name(db_session, name="nonexistent")
        assert result is None


class TestCRUDCourseCreate:
    def setup_method(self):
        self.crud = CRUDCourse(Course)

    def test_create_course(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = CourseCreate(
            name="New Course", description="Description", guacamole=True
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.name == "New Course"
        assert result.guacamole is True
        assert result.createdById == active_user.id


class TestCRUDCourseUpdate:
    def setup_method(self):
        self.crud = CRUDCourse(Course)

    def test_update_course_name(self, db_session, active_user, sample_course):
        request = create_mock_request(active_user)
        obj_in = CourseUpdate(name="Updated Course")
        result = self.crud.update(
            sample_course.id, db_session, request, obj_in=obj_in
        )
        assert result.name == "Updated Course"


class TestCRUDCourseDelete:
    def setup_method(self):
        self.crud = CRUDCourse(Course)

    def _create_event(self, db_session, user, status_id, course_id):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"Event-{uuid.uuid4().hex[:6]}",
            slug=f"e{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=status_id,
            course=course_id,
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db_session.add(event)
        db_session.flush()
        return event

    def test_delete_course(self, db_session, system_user, sample_course):
        course_id = sample_course.id
        self.crud.delete(db_session, id=course_id)
        result = db_session.get(Course, course_id)
        assert result is None

    def test_delete_nonexistent_raises(self, db_session, system_user):
        with pytest.raises(ObjectNotFound):
            self.crud.delete(db_session, id=uuid.uuid4())

    def test_delete_course_with_events_raises(
        self, db_session, active_user, event_statuses, sample_course
    ):
        self._create_event(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        with pytest.raises(ObjectInUseError):
            self.crud.delete(db_session, id=sample_course.id)
        # The course must still exist after the rejected delete
        assert db_session.get(Course, sample_course.id) is not None


class TestCRUDCourseTemplates:
    def setup_method(self):
        self.crud = CRUDCourse(Course)

    def _create_template(self, db_session, active_user):
        now = datetime.now(timezone.utc)
        t = Template(
            id=uuid.uuid4(),
            name=f"Template-{uuid.uuid4().hex[:6]}",
            cpu=2,
            ram=2048,
            disk=16,
            proxmoxId=100,
            proxmoxNode="pve-01",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(t)
        db_session.flush()
        return t


class TestCRUDCourseUpdateTemplate:
    def setup_method(self):
        self.crud = CRUDCourse(Course)

    def _create_template(self, db_session, user, proxmox_id=100):
        now = datetime.now(timezone.utc)
        t = Template(
            id=uuid.uuid4(),
            name=f"Template-{uuid.uuid4().hex[:6]}",
            cpu=2,
            ram=2048,
            disk=16,
            proxmoxId=proxmox_id,
            proxmoxNode="pve-01",
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db_session.add(t)
        db_session.flush()
        return t

    def test_update_template_adds_template(
        self, db_session, active_user, sample_course
    ):
        t = self._create_template(db_session, active_user)
        request = create_mock_request(active_user)
        obj_in = CourseUpdateTemplate(templates=[{"id": str(t.id)}])
        result = self.crud.update_template(
            sample_course.id, db_session, request, obj_in=obj_in
        )
        assert len(result.templates) == 1
        assert result.templates[0].id == t.id

    def test_update_template_adds_multiple(
        self, db_session, active_user, sample_course
    ):
        t1 = self._create_template(db_session, active_user, proxmox_id=101)
        t2 = self._create_template(db_session, active_user, proxmox_id=102)
        request = create_mock_request(active_user)
        obj_in = CourseUpdateTemplate(
            templates=[{"id": str(t1.id)}, {"id": str(t2.id)}]
        )
        result = self.crud.update_template(
            sample_course.id, db_session, request, obj_in=obj_in
        )
        assert len(result.templates) == 2

    def test_update_template_duplicate_raises(
        self, db_session, active_user, sample_course
    ):
        t = self._create_template(db_session, active_user)
        request = create_mock_request(active_user)
        obj_in = CourseUpdateTemplate(templates=[{"id": str(t.id)}])
        self.crud.update_template(
            sample_course.id, db_session, request, obj_in=obj_in
        )
        # Try to add the same template again
        with pytest.raises(BadRequestError):
            self.crud.update_template(
                sample_course.id, db_session, request, obj_in=obj_in
            )

    def test_update_template_nonexistent_template_raises(
        self, db_session, active_user, sample_course
    ):
        request = create_mock_request(active_user)
        obj_in = CourseUpdateTemplate(templates=[{"id": str(uuid.uuid4())}])
        with pytest.raises(ObjectNotFound):
            self.crud.update_template(
                sample_course.id, db_session, request, obj_in=obj_in
            )

    def test_update_template_nonexistent_course_raises(
        self, db_session, active_user
    ):
        request = create_mock_request(active_user)
        obj_in = CourseUpdateTemplate(templates=[{"id": str(uuid.uuid4())}])
        with pytest.raises(ObjectNotFound):
            self.crud.update_template(
                uuid.uuid4(), db_session, request, obj_in=obj_in
            )


class TestCRUDCourseDeleteTemplate:
    def setup_method(self):
        self.crud = CRUDCourse(Course)

    def _create_template(self, db_session, user, proxmox_id=200):
        now = datetime.now(timezone.utc)
        t = Template(
            id=uuid.uuid4(),
            name=f"Template-{uuid.uuid4().hex[:6]}",
            cpu=2,
            ram=2048,
            disk=16,
            proxmoxId=proxmox_id,
            proxmoxNode="pve-01",
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db_session.add(t)
        db_session.flush()
        return t

    def test_delete_template_removes_template(
        self, db_session, active_user, sample_course
    ):
        t = self._create_template(db_session, active_user)
        # Assign the template directly via the ORM relationship
        sample_course.templates.append(t)
        db_session.flush()
        # Expire to ensure a fresh load on next access
        db_session.expire(sample_course)
        assert len(sample_course.templates) == 1

        request = create_mock_request(active_user)
        # Expire again so delete_template gets a clean object
        db_session.expire(sample_course)
        obj_in_del = CourseUpdateTemplate(templates=[{"id": str(t.id)}])
        result = self.crud.delete_template(
            sample_course.id, db_session, request, obj_in=obj_in_del
        )
        assert len(result.templates) == 0

    def test_delete_template_removes_one_keeps_others(
        self, db_session, active_user, sample_course
    ):
        t1 = self._create_template(db_session, active_user, proxmox_id=201)
        t2 = self._create_template(db_session, active_user, proxmox_id=202)
        # Assign both templates directly via the ORM relationship
        sample_course.templates.append(t1)
        sample_course.templates.append(t2)
        db_session.flush()
        db_session.expire(sample_course)
        assert len(sample_course.templates) == 2

        request = create_mock_request(active_user)
        # Expire again so delete_template gets a clean object
        db_session.expire(sample_course)
        obj_in_del = CourseUpdateTemplate(templates=[{"id": str(t1.id)}])
        result = self.crud.delete_template(
            sample_course.id, db_session, request, obj_in=obj_in_del
        )
        assert len(result.templates) == 1
        assert result.templates[0].id == t2.id

    def test_delete_template_nonexistent_template_raises(
        self, db_session, active_user, sample_course
    ):
        request = create_mock_request(active_user)
        obj_in = CourseUpdateTemplate(templates=[{"id": str(uuid.uuid4())}])
        with pytest.raises(ObjectNotFound):
            self.crud.delete_template(
                sample_course.id, db_session, request, obj_in=obj_in
            )

    def test_delete_template_not_assigned_raises(
        self, db_session, active_user, sample_course
    ):
        """Removing a template that is not assigned to the course should raise."""
        t = self._create_template(db_session, active_user)
        request = create_mock_request(active_user)
        obj_in = CourseUpdateTemplate(templates=[{"id": str(t.id)}])
        with pytest.raises(ValueError):
            self.crud.delete_template(
                sample_course.id, db_session, request, obj_in=obj_in
            )
