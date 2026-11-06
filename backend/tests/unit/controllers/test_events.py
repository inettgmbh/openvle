"""Tests for controllers/events.py - CRUDEvent operations."""

import uuid
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from controllers.events import CRUDEvent
from core.exceptions import (
    BadRequestError,
    DuplicateEventUserRoleError,
    InvalidStatusError,
    ObjectInUseError,
    ObjectNotFound,
    OperationDependencyMissing,
)
from models import (
    Event,
    EventsUser,
    Guacamole,
    GuacamoleConnectionProfile,
    Template,
    User,
    VirtualMachine,
)
from models.associations import course_template_association_table
from models.sub_tasks import SubTask as SubTaskModel
from models.tasks import Task as TaskModel
from schemas.events import (
    EventCreate,
    EventUpdate,
    EventUpdateEndDateTime,
    EventUpdateTemplate,
    EventUpdateVirtualMachine,
    EventVirtualMachinesHaAdd,
)
from schemas.events_user import EventsUserCreate

from tests.helpers.mock_request import create_mock_request


class TestCRUDEventCreate:
    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def test_create_event(
        self, db_session, active_user, event_statuses, sample_course
    ):
        request = create_mock_request(active_user)
        obj_in = EventCreate(
            name="Test Event 001",
            slug="tev1",
            description="A test event",
            dateStart=date.today().isoformat(),
            dateEnd=(date.today() + timedelta(days=7)).isoformat(),
            timeStart="08:00:00",
            timeEnd="17:00:00",
            guacamole=False,
            status=str(event_statuses["Geplant"].id),
            course=str(sample_course.id),
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.id is not None
        assert result.name == "Test Event 001"
        assert result.slug == "tev1"
        assert result.status == event_statuses["Geplant"].id
        assert result.course == sample_course.id


class TestCRUDEventStatusValidation:
    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def _create_event(self, db_session, active_user, status_id, course_id):
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
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()
        return event

    def test_update_blocked_when_status_aktiv(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Aktiv"].id,
            sample_course.id,
        )
        request = create_mock_request(active_user)
        obj_in = EventUpdate(name="Updated Name")
        with pytest.raises(InvalidStatusError):
            self.crud.update(event.id, db_session, request, obj_in=obj_in)

    def test_update_allowed_when_geplant(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        request = create_mock_request(active_user)
        obj_in = EventUpdate(name="Updated Geplant")
        result = self.crud.update(event.id, db_session, request, obj_in=obj_in)
        assert result.name == "Updated Geplant"

    def test_update_resets_error_to_geplant(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Core Fehler"].id,
            sample_course.id,
        )
        request = create_mock_request(active_user)
        obj_in = EventUpdate(name="Fixed Event")
        result = self.crud.update(event.id, db_session, request, obj_in=obj_in)
        assert result.status == event_statuses["Geplant"].id


class TestCRUDEventActionsStart:
    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def _create_event_with_participants(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        role_teacher,
        role_student,
        *,
        with_teacher=True,
        with_student=True,
        with_templates=True,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"Start-{uuid.uuid4().hex[:6]}",
            slug=f"s{uuid.uuid4().hex[:4]}",
            description="Start test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        if with_teacher:
            eu = EventsUser(
                id=uuid.uuid4(),
                event_id=event.id,
                user_id=active_user.id,
                role_id=role_teacher.id,
                createdAt=now,
                updatedAt=now,
                createdById=active_user.id,
                updatedById=active_user.id,
            )
            db_session.add(eu)

        if with_student:
            # Create a second user as student
            student = User(
                id=uuid.uuid4(),
                username=f"student-{uuid.uuid4().hex[:6]}",
                email=f"st-{uuid.uuid4().hex[:6]}@example.com",
                name="Student",
                status="Active",
                locale="de_DE",
                createdAt=now,
                updatedAt=now,
            )
            db_session.add(student)
            db_session.flush()
            eu2 = EventsUser(
                id=uuid.uuid4(),
                event_id=event.id,
                user_id=student.id,
                role_id=role_student.id,
                createdAt=now,
                updatedAt=now,
                createdById=active_user.id,
                updatedById=active_user.id,
            )
            db_session.add(eu2)

        if with_templates:
            template = Template(
                id=uuid.uuid4(),
                name=f"Template-{uuid.uuid4().hex[:6]}",
                cpu=2,
                ram=4096,
                disk=32,
                proxmoxId=1000,
                proxmoxNode="pve-01",
                createdAt=now,
                updatedAt=now,
                createdById=active_user.id,
                updatedById=active_user.id,
            )
            db_session.add(template)
            db_session.flush()
            # Associate template with course
            db_session.execute(
                course_template_association_table.insert().values(
                    course_id=sample_course.id,
                    template_id=template.id,
                )
            )

        db_session.flush()
        return event

    def test_start_requires_status_geplant(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
        role_teacher,
        role_student,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name="Already Active",
            slug="actv",
            description="T",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Aktiv"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()
        request = create_mock_request(active_user)

        with pytest.raises(InvalidStatusError):
            self.crud.actions_start(event.id, db_session, request)

    def test_start_requires_participants(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
        role_teacher,
        role_student,
    ):
        # Event with no participants
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name="No Participants",
            slug="nope",
            description="T",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()
        request = create_mock_request(active_user)

        with pytest.raises(OperationDependencyMissing):
            self.crud.actions_start(event.id, db_session, request)

    def test_start_requires_at_least_one_teacher(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
        role_teacher,
        role_student,
    ):
        event = self._create_event_with_participants(
            db_session,
            active_user,
            event_statuses,
            sample_course,
            role_teacher,
            role_student,
            with_teacher=False,
            with_student=True,
        )
        request = create_mock_request(active_user)
        with pytest.raises(OperationDependencyMissing):
            self.crud.actions_start(event.id, db_session, request)

    def test_start_requires_course_templates(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
        role_teacher,
        role_student,
    ):
        event = self._create_event_with_participants(
            db_session,
            active_user,
            event_statuses,
            sample_course,
            role_teacher,
            role_student,
            with_templates=False,
        )
        request = create_mock_request(active_user)
        with pytest.raises(OperationDependencyMissing):
            self.crud.actions_start(event.id, db_session, request)

    def test_start_updates_status_to_deploying_and_enqueues(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
        role_teacher,
        role_student,
    ):
        event = self._create_event_with_participants(
            db_session,
            active_user,
            event_statuses,
            sample_course,
            role_teacher,
            role_student,
        )
        request = create_mock_request(active_user)
        result = self.crud.actions_start(event.id, db_session, request)
        assert result.status == event_statuses["Deploying"].id
        # Verify a job was enqueued
        assert len(mock_redis_queues) > 0

    def test_start_raises_when_role_teacher_missing(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
        role_teacher,
        role_student,
    ):
        """If role 'lehrende' is missing, actions_start should raise ObjectNotFound."""
        from models import Role as RoleModel

        # Create event with only students (no teacher EventsUser referencing role)
        event = self._create_event_with_participants(
            db_session,
            active_user,
            event_statuses,
            sample_course,
            role_teacher,
            role_student,
            with_teacher=False,
            with_student=True,
        )
        db_session.query(RoleModel).filter(RoleModel.key == "lehrende").delete()
        db_session.flush()

        request = create_mock_request(active_user)
        with pytest.raises(ObjectNotFound):
            self.crud.actions_start(event.id, db_session, request)

    def test_start_raises_when_role_student_missing(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
        role_teacher,
        role_student,
    ):
        """If role 'studierende' is missing, actions_start should raise ObjectNotFound."""
        from models import Role as RoleModel

        # Create event with only teachers (no student EventsUser referencing role)
        event = self._create_event_with_participants(
            db_session,
            active_user,
            event_statuses,
            sample_course,
            role_teacher,
            role_student,
            with_teacher=True,
            with_student=False,
        )
        db_session.query(RoleModel).filter(
            RoleModel.key == "studierende"
        ).delete()
        db_session.flush()

        request = create_mock_request(active_user)
        with pytest.raises(ObjectNotFound):
            self.crud.actions_start(event.id, db_session, request)

    def test_start_raises_when_deploying_status_missing(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
        role_teacher,
        role_student,
    ):
        """If EventStatus 'Deploying' is missing, actions_start should raise ObjectNotFound."""
        from models import EventStatus

        event = self._create_event_with_participants(
            db_session,
            active_user,
            event_statuses,
            sample_course,
            role_teacher,
            role_student,
        )
        db_session.query(EventStatus).filter(
            EventStatus.name == "Deploying"
        ).delete()
        db_session.flush()

        request = create_mock_request(active_user)
        with pytest.raises(ObjectNotFound):
            self.crud.actions_start(event.id, db_session, request)


class TestCRUDEventActionsEnd:
    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def test_end_requires_status_aktiv(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name="Still Planned",
            slug="plan",
            description="T",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()
        request = create_mock_request(active_user)

        with pytest.raises(InvalidStatusError):
            self.crud.actions_stop(event.id, db_session, request)

    def test_end_updates_status_to_archiving_and_enqueues(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name="Active Event",
            slug="aevt",
            description="T",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Aktiv"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()
        request = create_mock_request(active_user)

        result = self.crud.actions_stop(event.id, db_session, request)
        assert result.status == event_statuses["Archiving"].id
        assert len(mock_redis_queues) > 0

    def test_end_raises_when_archiving_status_missing(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
    ):
        """If EventStatus 'Archiving' is missing, actions_stop should raise ObjectNotFound."""
        from models import EventStatus

        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name="Active NoArch",
            slug="noar",
            description="T",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Aktiv"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        db_session.query(EventStatus).filter(
            EventStatus.name == "Archiving"
        ).delete()
        db_session.flush()

        request = create_mock_request(active_user)
        with pytest.raises(ObjectNotFound):
            self.crud.actions_stop(event.id, db_session, request)


class TestCRUDEventAddUser:
    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def test_add_user_creates_events_user_record(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        role_teacher,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name="Add User Event",
            slug="addu",
            description="T",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        request = create_mock_request(active_user)
        obj_in = EventsUserCreate(
            user_id=str(active_user.id),
            role_id=str(role_teacher.id),
        )
        self.crud.add_user(event.id, db_session, request, obj_in=obj_in)

        eu = (
            db_session.query(EventsUser)
            .filter(
                EventsUser.event_id == event.id,
                EventsUser.user_id == active_user.id,
            )
            .first()
        )
        assert eu is not None
        assert eu.role_id == role_teacher.id

    def test_add_duplicate_user_raises(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        role_teacher,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name="Dup User Evt",
            slug="dupe",
            description="T",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        request = create_mock_request(active_user)
        obj_in = EventsUserCreate(
            user_id=str(active_user.id),
            role_id=str(role_teacher.id),
        )
        self.crud.add_user(event.id, db_session, request, obj_in=obj_in)

        # Adding the same user again should raise
        with pytest.raises(DuplicateEventUserRoleError):
            self.crud.add_user(event.id, db_session, request, obj_in=obj_in)


class TestCRUDEventDelete:
    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def test_delete_allowed_when_geplant(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        role_teacher,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name="Del Planned",
            slug="delp",
            description="T",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()
        event_id = event.id

        self.crud.delete(db_session, id=event_id)
        result = db_session.get(Event, event_id)
        assert result is None

    def test_delete_blocked_when_vms_assigned(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        role_teacher,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name="Del VMs",
            slug="delv",
            description="T",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()
        vm = VirtualMachine(
            id=uuid.uuid4(),
            name="vm-using-event",
            status="running",
            proxmoxId=301,
            cpu=2,
            ram=4096,
            disk=32,
            event=event.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(vm)
        db_session.flush()

        with pytest.raises(ObjectInUseError):
            self.crud.delete(db_session, id=event.id)
        # The event must still exist after the rejected delete
        assert db_session.get(Event, event.id) is not None

    def test_delete_blocked_when_aktiv(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        role_teacher,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name="Del Active",
            slug="dela",
            description="T",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Aktiv"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        with pytest.raises(InvalidStatusError):
            self.crud.delete(db_session, id=event.id)

    def test_delete_event_with_associated_mails(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
        role_teacher,
        mock_redis_queues,
    ):
        """Deleting an event that has associated mails must not fail.

        Regression: previously the FK from sys_mails.event → kvs_events.id
        caused an IntegrityError when the event was deleted while mail rows
        still referenced it.
        """
        from models import Mail, MailAction, MailTemplate

        now = datetime.now(timezone.utc)

        # Use the seeded MailAction + MailTemplate for "events_delete".
        mail_action = (
            db_session.query(MailAction).filter_by(slug="events_delete").one()
        )
        mail_template = (
            db_session.query(MailTemplate)
            .filter_by(mail_action=mail_action.id)
            .first()
        )

        # Create an event
        event = Event(
            id=uuid.uuid4(),
            name="Del With Mails",
            slug="delm",
            description="T",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        # Pre-existing mail that references the event (should be cleaned up)
        existing_mail = Mail(
            id=uuid.uuid4(),
            subject="Old notification",
            fromName="KVS",
            fromMail="test@example.com",
            toMail=active_user.email,
            sendStatus="sent",
            templateId=mail_template.id,
            replyTo="test@example.com",
            event=event.id,
            user_id=active_user.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(existing_mail)
        db_session.flush()

        # Assign active_user as teacher (event_admin) so _delete_mail fires
        eu = EventsUser(
            id=uuid.uuid4(),
            event_id=event.id,
            user_id=active_user.id,
            role_id=role_teacher.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(eu)
        db_session.flush()

        event_id = event.id
        existing_mail_id = existing_mail.id

        # Should succeed without IntegrityError
        result = self.crud.delete(db_session, id=event_id)
        assert (
            "deleted" in result["detail"].lower()
            or str(event_id) in result["detail"]
        )

        # Event must be gone
        assert db_session.get(Event, event_id) is None

        # Old mail referencing the event must also be gone
        assert db_session.get(Mail, existing_mail_id) is None

    def test_delete_notification_mail_has_no_event_fk(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
        role_teacher,
        mock_redis_queues,
    ):
        """The deletion notification mail must not set the event FK.

        Regression: if the mail carried a FK to the just-deleted event the
        DB would reject it with a constraint violation.
        """
        from models import Mail, MailAction, MailTemplate

        now = datetime.now(timezone.utc)

        # Use seeded MailAction + MailTemplate for "events_delete"
        mail_action = (
            db_session.query(MailAction).filter_by(slug="events_delete").one()
        )
        mail_template = (
            db_session.query(MailTemplate)
            .filter_by(mail_action=mail_action.id)
            .first()
        )

        event = Event(
            id=uuid.uuid4(),
            name="Del Check FK",
            slug="delfk",
            description="T",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        eu = EventsUser(
            id=uuid.uuid4(),
            event_id=event.id,
            user_id=active_user.id,
            role_id=role_teacher.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(eu)
        db_session.flush()

        event_id = event.id
        self.crud.delete(db_session, id=event_id)

        # Find the notification mail created by _delete_mail
        notification_mails = (
            db_session.query(Mail)
            .filter(
                Mail.user_id == active_user.id,
                Mail.templateId == mail_template.id,
            )
            .all()
        )

        assert len(notification_mails) == 1
        # The notification mail must NOT reference the deleted event
        assert notification_mails[0].event is None


class TestCRUDEventGetByName:
    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def test_get_by_name_returns_event(
        self, db_session, active_user, event_statuses, sample_course
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name="FindByName",
            slug="fbnm",
            description="T",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        result = self.crud.get_by_name(db_session, name="FindByName")
        assert result is not None
        assert result.id == event.id
        assert result.name == "FindByName"

    def test_get_by_name_returns_none_when_not_found(
        self, db_session, active_user, event_statuses, sample_course
    ):
        result = self.crud.get_by_name(db_session, name="NonExistent")
        assert result is None


class TestCRUDEventGetBySlug:
    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def test_get_by_slug_returns_event(
        self, db_session, active_user, event_statuses, sample_course
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name="Slug Event",
            slug="slge",
            description="T",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        result = self.crud.get_by_slug(db_session, slug="slge")
        assert result is not None
        assert result.id == event.id
        assert result.slug == "slge"

    def test_get_by_slug_returns_none_when_not_found(
        self, db_session, active_user, event_statuses, sample_course
    ):
        result = self.crud.get_by_slug(db_session, slug="nosl")
        assert result is None


class TestCRUDEventUpdateEndDatetime:
    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def _create_event(self, db_session, active_user, status_id, course_id):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"EndDt-{uuid.uuid4().hex[:6]}",
            slug=f"e{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=status_id,
            course=course_id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()
        return event

    def test_update_end_datetime_when_geplant(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        request = create_mock_request(active_user)
        new_end_date = date.today() + timedelta(days=14)
        obj_in = EventUpdateEndDateTime(
            dateEnd=new_end_date.isoformat(),
            timeEnd="18:00:00",
        )
        result = self.crud.update_end_datetime(
            event.id, db_session, request, obj_in=obj_in
        )
        assert result.dateEnd == new_end_date

    def test_update_end_datetime_when_aktiv(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Aktiv"].id,
            sample_course.id,
        )
        request = create_mock_request(active_user)
        new_end_date = date.today() + timedelta(days=14)
        obj_in = EventUpdateEndDateTime(
            dateEnd=new_end_date.isoformat(),
            timeEnd="18:00:00",
        )
        result = self.crud.update_end_datetime(
            event.id, db_session, request, obj_in=obj_in
        )
        assert result.dateEnd == new_end_date

    def test_update_end_datetime_blocked_when_archiviert(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Archiviert"].id,
            sample_course.id,
        )
        request = create_mock_request(active_user)
        obj_in = EventUpdateEndDateTime(
            dateEnd=(date.today() + timedelta(days=14)).isoformat(),
            timeEnd="18:00:00",
        )
        with pytest.raises(InvalidStatusError):
            self.crud.update_end_datetime(
                event.id, db_session, request, obj_in=obj_in
            )

    def test_update_end_datetime_resets_core_fehler_to_geplant(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Core Fehler"].id,
            sample_course.id,
        )
        request = create_mock_request(active_user)
        obj_in = EventUpdateEndDateTime(
            dateEnd=(date.today() + timedelta(days=14)).isoformat(),
            timeEnd="18:00:00",
        )
        result = self.crud.update_end_datetime(
            event.id, db_session, request, obj_in=obj_in
        )
        assert result.status == event_statuses["Geplant"].id


class TestCRUDEventAddTemplates:
    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def _create_event(self, db_session, active_user, status_id, course_id):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"TplEvt-{uuid.uuid4().hex[:6]}",
            slug=f"t{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=status_id,
            course=course_id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()
        return event

    def _create_template(self, db_session, active_user, proxmox_id=1000):
        now = datetime.now(timezone.utc)
        template = Template(
            id=uuid.uuid4(),
            name=f"Template-{uuid.uuid4().hex[:6]}",
            cpu=2,
            ram=4096,
            disk=32,
            proxmoxId=proxmox_id,
            proxmoxNode="pve-01",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(template)
        db_session.flush()
        return template

    def test_add_templates_when_geplant(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        template = self._create_template(db_session, active_user)
        request = create_mock_request(active_user)
        obj_in = EventUpdateTemplate(
            templates=[{"id": str(template.id)}],
        )
        result = self.crud.add_templates(
            event.id, db_session, request, obj_in=obj_in
        )
        assert len(result.templates) == 1
        assert result.templates[0].id == template.id

    def test_add_templates_blocked_when_archiviert(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Archiviert"].id,
            sample_course.id,
        )
        template = self._create_template(db_session, active_user)
        request = create_mock_request(active_user)
        obj_in = EventUpdateTemplate(
            templates=[{"id": str(template.id)}],
        )
        with pytest.raises(InvalidStatusError):
            self.crud.add_templates(
                event.id, db_session, request, obj_in=obj_in
            )

    def test_add_templates_raises_when_template_not_found(
        self, db_session, active_user, event_statuses, sample_course
    ):
        from core.exceptions import ObjectNotFound

        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        fake_template_id = str(uuid.uuid4())
        request = create_mock_request(active_user)
        obj_in = EventUpdateTemplate(
            templates=[{"id": fake_template_id}],
        )
        with pytest.raises(ObjectNotFound):
            self.crud.add_templates(
                event.id, db_session, request, obj_in=obj_in
            )

    def test_add_templates_raises_when_no_proxmox_id(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        template = self._create_template(
            db_session, active_user, proxmox_id=None
        )
        request = create_mock_request(active_user)
        obj_in = EventUpdateTemplate(
            templates=[{"id": str(template.id)}],
        )
        with pytest.raises(OperationDependencyMissing):
            self.crud.add_templates(
                event.id, db_session, request, obj_in=obj_in
            )

    def test_add_templates_resets_core_fehler_to_geplant(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Core Fehler"].id,
            sample_course.id,
        )
        template = self._create_template(db_session, active_user)
        request = create_mock_request(active_user)
        obj_in = EventUpdateTemplate(
            templates=[{"id": str(template.id)}],
        )
        result = self.crud.add_templates(
            event.id, db_session, request, obj_in=obj_in
        )
        assert result.status == event_statuses["Geplant"].id


class TestCRUDEventDeleteVirtualMachine:
    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def _create_event_with_vm(
        self, db_session, active_user, status_id, course_id
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"VmDel-{uuid.uuid4().hex[:6]}",
            slug=f"v{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=status_id,
            course=course_id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        vm = VirtualMachine(
            id=uuid.uuid4(),
            name="test-vm",
            cpu=2,
            ram=4096,
            disk=32,
            event=event.id,
            prevent_delete=False,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(vm)
        db_session.flush()
        return event, vm

    def test_delete_virtual_machine_removes_vm_from_event(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event, vm = self._create_event_with_vm(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        request = create_mock_request(active_user)
        obj_in = EventUpdateVirtualMachine(
            vms=[{"id": str(vm.id)}],
        )
        self.crud.delete_virtual_machine(
            event.id, db_session, request, obj_in=obj_in
        )
        db_session.refresh(vm)
        assert vm.event is None

    def test_delete_virtual_machine_raises_when_vms_key_missing(
        self, db_session, active_user, event_statuses, sample_course
    ):
        """Passing an obj_in without 'vms' should raise RequiredParameterMissingError."""
        from core.exceptions import RequiredParameterMissingError

        event, vm = self._create_event_with_vm(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        request = create_mock_request(active_user)
        # EventUpdateVirtualMachine requires 'vms', but after merge if the key
        # is not in update_data the method raises RequiredParameterMissingError.
        # We mock the merge to simulate missing 'vms' key.
        with (
            patch.object(
                self.crud,
                "_merge_request_with_db_object",
                return_value={"name": "test"},
            ),
            pytest.raises(RequiredParameterMissingError),
        ):
            obj_in = EventUpdateVirtualMachine(
                vms=[{"id": str(vm.id)}],
            )
            self.crud.delete_virtual_machine(
                event.id, db_session, request, obj_in=obj_in
            )


class TestCRUDEventDeleteEventUser:
    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def _create_event_with_user(
        self,
        db_session,
        active_user,
        status_id,
        course_id,
        role_id,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"EuDel-{uuid.uuid4().hex[:6]}",
            slug=f"d{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=status_id,
            course=course_id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        eu = EventsUser(
            id=uuid.uuid4(),
            event_id=event.id,
            user_id=active_user.id,
            role_id=role_id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(eu)
        db_session.flush()
        return event, eu

    def test_delete_event_user_removes_record(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        role_teacher,
    ):
        event, _eu = self._create_event_with_user(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
            role_teacher.id,
        )
        request = create_mock_request(active_user)
        result = self.crud.delete_event_user(
            db_session,
            request,
            event_id=event.id,
            user_id=active_user.id,
            role_id=role_teacher.id,
        )
        assert "detail" in result

        remaining = (
            db_session.query(EventsUser)
            .filter(
                EventsUser.event_id == event.id,
                EventsUser.user_id == active_user.id,
            )
            .first()
        )
        assert remaining is None

    def test_delete_event_user_raises_when_not_found(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        role_teacher,
        role_student,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"EuDel2-{uuid.uuid4().hex[:6]}",
            slug=f"d{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        request = create_mock_request(active_user)
        with pytest.raises(BadRequestError):
            self.crud.delete_event_user(
                db_session,
                request,
                event_id=event.id,
                user_id=active_user.id,
                role_id=role_student.id,
            )


class TestCRUDEventGetEventStudents:
    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def test_get_event_students_returns_students(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        role_student,
        role_teacher,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"Stu-{uuid.uuid4().hex[:6]}",
            slug=f"s{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        student_user = User(
            id=uuid.uuid4(),
            username=f"student-{uuid.uuid4().hex[:6]}",
            email=f"stu-{uuid.uuid4().hex[:6]}@example.com",
            name="Student User",
            status="Active",
            locale="de_DE",
            createdAt=now,
            updatedAt=now,
        )
        db_session.add(student_user)
        db_session.flush()

        eu_student = EventsUser(
            id=uuid.uuid4(),
            event_id=event.id,
            user_id=student_user.id,
            role_id=role_student.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(eu_student)

        # Also add a teacher to confirm they are not returned
        eu_teacher = EventsUser(
            id=uuid.uuid4(),
            event_id=event.id,
            user_id=active_user.id,
            role_id=role_teacher.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(eu_teacher)
        db_session.flush()

        result = self.crud.get_event_students(db_session, id=event.id)
        assert len(result) == 1
        assert result[0].user_id == student_user.id
        assert result[0].role_id == role_student.id

    def test_get_event_students_returns_empty_when_no_students(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        role_student,
        role_teacher,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"NoStu-{uuid.uuid4().hex[:6]}",
            slug=f"n{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        # Only add a teacher, no students
        eu_teacher = EventsUser(
            id=uuid.uuid4(),
            event_id=event.id,
            user_id=active_user.id,
            role_id=role_teacher.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(eu_teacher)
        db_session.flush()

        result = self.crud.get_event_students(db_session, id=event.id)
        assert len(result) == 0

    def test_get_event_students_raises_when_role_missing(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
    ):
        """If role 'studierende' doesn't exist, raise ObjectNotFound."""
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"NoRole-{uuid.uuid4().hex[:6]}",
            slug=f"r{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        from models import Role as RoleModel

        db_session.query(RoleModel).filter(
            RoleModel.key == "studierende"
        ).delete()
        db_session.flush()

        with pytest.raises(ObjectNotFound):
            self.crud.get_event_students(db_session, id=event.id)


class TestCRUDEventVirtualMachinesBulkActions:
    """Tests for VM bulk action methods that delegate to CRUDVirtualMachine."""

    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def _create_active_event_with_vm(
        self, db_session, active_user, event_statuses, sample_course
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"Bulk-{uuid.uuid4().hex[:6]}",
            slug=f"b{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Aktiv"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        vm = VirtualMachine(
            id=uuid.uuid4(),
            name="bulk-vm",
            cpu=2,
            ram=4096,
            disk=32,
            event=event.id,
            prevent_delete=False,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(vm)
        db_session.flush()
        return event, vm

    def _make_request_with_route(self, active_user, operation_id="test_op"):
        request = create_mock_request(active_user)
        route = MagicMock()
        route.operation_id = operation_id
        request.scope = {"route": route}
        return request

    @pytest.mark.parametrize(
        "action_method,bulk_method",
        [
            ("virtual_machines_start", "bulk_start"),
            ("virtual_machines_stop", "bulk_stop"),
            ("virtual_machines_pause", "bulk_pause"),
            ("virtual_machines_reset", "bulk_reset"),
            ("virtual_machines_reboot", "bulk_reboot"),
            ("virtual_machines_shutdown", "bulk_shutdown"),
            ("virtual_machines_resume", "bulk_resume"),
            ("virtual_machines_hibernate", "bulk_hibernate"),
        ],
    )
    def test_bulk_action_delegates_to_crud_vm(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
        action_method,
        bulk_method,
    ):
        event, _vm = self._create_active_event_with_vm(
            db_session, active_user, event_statuses, sample_course
        )
        request = self._make_request_with_route(active_user)
        expected_result = {
            "task_id": uuid.uuid4(),
            "enqueued": 1,
            "skipped": [],
        }

        with patch(
            f"controllers.events.CRUDVirtualMachine.{bulk_method}",
            return_value=expected_result,
        ) as mock_bulk:
            method = getattr(self.crud, action_method)
            result = method(db_session, event.id, request)
            assert result == expected_result
            mock_bulk.assert_called_once()
            call_kwargs = mock_bulk.call_args
            assert call_kwargs.kwargs.get("event_id") == event.id

    def test_bulk_action_requires_aktiv_status(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"NotAct-{uuid.uuid4().hex[:6]}",
            slug=f"n{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        request = self._make_request_with_route(active_user)
        with pytest.raises(InvalidStatusError):
            self.crud.virtual_machines_start(db_session, event.id, request)

    def test_virtual_machines_migrate_delegates_with_target_node(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
    ):
        event, _vm = self._create_active_event_with_vm(
            db_session, active_user, event_statuses, sample_course
        )
        request = self._make_request_with_route(active_user)
        expected_result = {
            "task_id": uuid.uuid4(),
            "enqueued": 1,
            "skipped": [],
        }

        with patch(
            "controllers.events.CRUDVirtualMachine.bulk_migrate",
            return_value=expected_result,
        ) as mock_migrate:
            result = self.crud.virtual_machines_migrate(
                db_session, event.id, request, target_node="pve-02"
            )
            assert result == expected_result
            mock_migrate.assert_called_once()
            call_kwargs = mock_migrate.call_args
            assert call_kwargs.kwargs.get("target_node") == "pve-02"
            assert call_kwargs.kwargs.get("event_id") == event.id


class TestCRUDEventVirtualMachinesHaOperations:
    """Tests for HA add/remove bulk operations."""

    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def _create_active_event_with_vm(
        self, db_session, active_user, event_statuses, sample_course
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"HA-{uuid.uuid4().hex[:6]}",
            slug=f"h{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Aktiv"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        vm = VirtualMachine(
            id=uuid.uuid4(),
            name="ha-vm",
            cpu=2,
            ram=4096,
            disk=32,
            event=event.id,
            prevent_delete=False,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(vm)
        db_session.flush()
        return event, vm

    def _make_request_with_route(self, active_user, operation_id="test_op"):
        request = create_mock_request(active_user)
        route = MagicMock()
        route.operation_id = operation_id
        request.scope = {"route": route}
        return request

    def test_ha_add_delegates_to_crud_vm(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
    ):
        event, _vm = self._create_active_event_with_vm(
            db_session, active_user, event_statuses, sample_course
        )
        request = self._make_request_with_route(active_user)
        obj_in = EventVirtualMachinesHaAdd(
            ha_state="started",
            ha_max_restart=3,
            ha_max_relocate=3,
        )
        expected_result = {
            "task_id": uuid.uuid4(),
            "enqueued": 1,
            "skipped": [],
        }

        with patch(
            "controllers.events.CRUDVirtualMachine.bulk_ha_add",
            return_value=expected_result,
        ) as mock_ha_add:
            result = self.crud.virtual_machines_ha_add(
                db_session, event.id, request, obj_in=obj_in
            )
            assert result == expected_result
            mock_ha_add.assert_called_once()
            call_kwargs = mock_ha_add.call_args
            assert call_kwargs.kwargs.get("event_id") == event.id

    def test_ha_add_requires_aktiv_status(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"HAna-{uuid.uuid4().hex[:6]}",
            slug=f"h{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        request = self._make_request_with_route(active_user)
        obj_in = EventVirtualMachinesHaAdd(
            ha_state="started",
            ha_max_restart=3,
            ha_max_relocate=3,
        )
        with pytest.raises(InvalidStatusError):
            self.crud.virtual_machines_ha_add(
                db_session, event.id, request, obj_in=obj_in
            )

    def test_ha_remove_delegates_to_crud_vm(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
    ):
        event, _vm = self._create_active_event_with_vm(
            db_session, active_user, event_statuses, sample_course
        )
        request = self._make_request_with_route(active_user)
        expected_result = {
            "task_id": uuid.uuid4(),
            "enqueued": 1,
            "skipped": [],
        }

        with patch(
            "controllers.events.CRUDVirtualMachine.bulk_ha_remove",
            return_value=expected_result,
        ) as mock_ha_remove:
            result = self.crud.virtual_machines_ha_remove(
                db_session, event.id, request
            )
            assert result == expected_result
            mock_ha_remove.assert_called_once()
            call_kwargs = mock_ha_remove.call_args
            assert call_kwargs.kwargs.get("event_id") == event.id

    def test_ha_remove_requires_aktiv_status(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"HArmna-{uuid.uuid4().hex[:6]}",
            slug=f"h{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        request = self._make_request_with_route(active_user)
        with pytest.raises(InvalidStatusError):
            self.crud.virtual_machines_ha_remove(db_session, event.id, request)


class TestCRUDEventGuacamoleOperations:
    """Tests for guacamoles_delete and guacamoles_create methods."""

    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def _create_active_event(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        guacamole=True,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"Guac-{uuid.uuid4().hex[:6]}",
            slug=f"g{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=guacamole,
            status=event_statuses["Aktiv"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()
        return event

    def _make_request_with_route(self, active_user, operation_id="test_op"):
        request = create_mock_request(active_user)
        route = MagicMock()
        route.operation_id = operation_id
        request.scope = {"route": route}
        return request

    def test_guacamoles_delete_requires_aktiv_status(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"GdNA-{uuid.uuid4().hex[:6]}",
            slug=f"g{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=True,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        request = self._make_request_with_route(active_user)
        with pytest.raises(InvalidStatusError):
            self.crud.guacamoles_delete(db_session, event.id, request)

    def test_guacamoles_delete_raises_when_no_guacamoles(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
    ):
        from core.exceptions import BulkActionRequirementMissing

        event = self._create_active_event(
            db_session, active_user, event_statuses, sample_course
        )
        request = self._make_request_with_route(active_user)
        with pytest.raises(BulkActionRequirementMissing):
            self.crud.guacamoles_delete(db_session, event.id, request)

    def test_guacamoles_delete_enqueues_jobs(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
        role_teacher,
    ):
        event = self._create_active_event(
            db_session, active_user, event_statuses, sample_course
        )
        now = datetime.now(timezone.utc)

        # Create a GuacamoleConnectionProfile for the guacamole object
        gcp = GuacamoleConnectionProfile(
            id=uuid.uuid4(),
            port=3389,
            protocol="RDP",
            objectId=uuid.uuid4(),
            objectType="VirtualMachine",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(gcp)
        db_session.flush()

        guac = Guacamole(
            id=uuid.uuid4(),
            name="test-guac",
            guacd_hostname="",
            guacd_port=4822,
            guacd_encryption=True,
            connection_profile=gcp.id,
            userId=active_user.id,
            eventId=event.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(guac)
        db_session.flush()

        request = self._make_request_with_route(active_user)
        result = self.crud.guacamoles_delete(db_session, event.id, request)
        assert "task_id" in result
        assert result["enqueued"] == 1
        assert len(mock_redis_queues) > 0

    def test_guacamoles_create_requires_aktiv_status(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"GcNA-{uuid.uuid4().hex[:6]}",
            slug=f"g{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=True,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        request = self._make_request_with_route(active_user)
        with pytest.raises(InvalidStatusError):
            self.crud.guacamoles_create(db_session, event.id, request)

    def test_guacamoles_create_raises_when_all_exist(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        mock_redis_queues,
        role_teacher,
    ):
        from core.exceptions import BulkActionRequirementMissing

        event = self._create_active_event(
            db_session, active_user, event_statuses, sample_course
        )
        # No VMs means no guacamoles to create -> raises
        request = self._make_request_with_route(active_user)
        with pytest.raises(BulkActionRequirementMissing):
            self.crud.guacamoles_create(db_session, event.id, request)


class TestCRUDEventDeleteEmptyParents:
    """Tests for the _delete_empty_parents cleanup helper."""

    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def test_delete_empty_parents_removes_task(
        self, db_session, active_user, event_statuses, sample_course
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"Dep-{uuid.uuid4().hex[:6]}",
            slug=f"p{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        task = TaskModel(
            id=uuid.uuid4(),
            name="Empty parent task",
            status="pending",
            event_id=event.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(task)
        db_session.flush()
        task_id = task.id

        self.crud._delete_empty_parents(db=db_session, parent_task_id=task_id)

        result = db_session.get(TaskModel, task_id)
        assert result is None

    def test_delete_empty_parents_raises_on_invalid_id(
        self, db_session, active_user, event_statuses, sample_course
    ):
        fake_id = uuid.uuid4()
        with pytest.raises(BadRequestError):
            self.crud._delete_empty_parents(
                db=db_session, parent_task_id=fake_id
            )


class TestCRUDEventGetEventAdmin:
    """Tests for get_event_admin() method."""

    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def test_get_event_admin_returns_teachers(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        role_teacher,
        role_student,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"Admin-{uuid.uuid4().hex[:6]}",
            slug=f"a{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        eu_teacher = EventsUser(
            id=uuid.uuid4(),
            event_id=event.id,
            user_id=active_user.id,
            role_id=role_teacher.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(eu_teacher)

        student_user = User(
            id=uuid.uuid4(),
            username=f"student-{uuid.uuid4().hex[:6]}",
            email=f"st-{uuid.uuid4().hex[:6]}@example.com",
            name="Student",
            status="Active",
            locale="de_DE",
            createdAt=now,
            updatedAt=now,
        )
        db_session.add(student_user)
        db_session.flush()

        eu_student = EventsUser(
            id=uuid.uuid4(),
            event_id=event.id,
            user_id=student_user.id,
            role_id=role_student.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(eu_student)
        db_session.flush()

        result = self.crud.get_event_admin(db_session, id=event.id)
        assert len(result) == 1
        assert result[0].user_id == active_user.id
        assert result[0].role_id == role_teacher.id

    def test_get_event_admin_returns_empty_when_no_teachers(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
        role_teacher,
        role_student,
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"NoAdm-{uuid.uuid4().hex[:6]}",
            slug=f"n{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        eu_student = EventsUser(
            id=uuid.uuid4(),
            event_id=event.id,
            user_id=active_user.id,
            role_id=role_student.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(eu_student)
        db_session.flush()

        result = self.crud.get_event_admin(db_session, id=event.id)
        assert len(result) == 0

    def test_get_event_admin_raises_when_role_missing(
        self,
        db_session,
        active_user,
        event_statuses,
        sample_course,
    ):
        """If role 'lehrende' doesn't exist, raise ObjectNotFound."""
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"NoRole-{uuid.uuid4().hex[:6]}",
            slug=f"r{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        # Delete the 'lehrende' role so lookup returns None
        from models import Role as RoleModel

        db_session.query(RoleModel).filter(RoleModel.key == "lehrende").delete()
        db_session.flush()

        with pytest.raises(ObjectNotFound):
            self.crud.get_event_admin(db_session, id=event.id)


class TestCRUDEventAddVirtualMachines:
    """Tests for add_virtual_machines() method."""

    def setup_method(self):
        self.crud = CRUDEvent(Event)

    def _create_event(self, db_session, active_user, status_id, course_id):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"AddVM-{uuid.uuid4().hex[:6]}",
            slug=f"v{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=status_id,
            course=course_id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()
        return event

    def test_add_virtual_machines_assigns_vms_to_event(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        now = datetime.now(timezone.utc)
        vm = VirtualMachine(
            id=uuid.uuid4(),
            name="unassigned-vm",
            cpu=2,
            ram=4096,
            disk=32,
            prevent_delete=False,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(vm)
        db_session.flush()

        request = create_mock_request(active_user)
        obj_in = EventUpdateVirtualMachine(
            vms=[{"id": str(vm.id)}],
        )
        self.crud.add_virtual_machines(
            event.id, db_session, request, obj_in=obj_in
        )
        db_session.refresh(vm)
        assert vm.event == event.id

    def test_add_virtual_machines_raises_when_vms_key_missing(
        self, db_session, active_user, event_statuses, sample_course
    ):
        from core.exceptions import RequiredParameterMissingError

        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        request = create_mock_request(active_user)
        with patch.object(
            self.crud,
            "_merge_request_with_db_object",
            return_value={"name": "test"},
        ):
            obj_in = EventUpdateVirtualMachine(
                vms=[{"id": str(uuid.uuid4())}],
            )
            with pytest.raises(RequiredParameterMissingError):
                self.crud.add_virtual_machines(
                    event.id, db_session, request, obj_in=obj_in
                )

    def test_add_virtual_machines_raises_on_invalid_vm_id(
        self, db_session, active_user, event_statuses, sample_course
    ):
        from core.exceptions import ObjectNotFound

        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        request = create_mock_request(active_user)
        fake_vm_id = str(uuid.uuid4())
        obj_in = EventUpdateVirtualMachine(
            vms=[{"id": fake_vm_id}],
        )
        with pytest.raises((ObjectNotFound, BadRequestError)):
            self.crud.add_virtual_machines(
                event.id, db_session, request, obj_in=obj_in
            )


# ---------------------------------------------------------------------------
# TestCRUDEventGetStatus
# ---------------------------------------------------------------------------


class TestCRUDEventGetStatus:
    """Tests for CRUDEvent.get_status() - covers initiator logic, VM stats,
    and task summary for every meaningful event status."""

    def setup_method(self):
        self.crud = CRUDEvent(Event)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_event(self, db, user, status_id, course_id, creator=None):
        now = datetime.now(timezone.utc)
        creator = creator or user
        event = Event(
            id=uuid.uuid4(),
            name=f"Status-Event-{uuid.uuid4().hex[:6]}",
            slug=f"s{uuid.uuid4().hex[:4]}",
            description="Test",
            dateStart=date.today(),
            dateEnd=date.today() + timedelta(days=7),
            guacamole=False,
            status=status_id,
            course=course_id,
            createdAt=now,
            updatedAt=now,
            createdById=creator.id,
            updatedById=user.id,
        )
        db.add(event)
        db.flush()
        return event

    def _create_task(self, db, user, event, name="Start Event"):
        now = datetime.now(timezone.utc)
        task = TaskModel(
            id=uuid.uuid4(),
            name=name,
            status="queued",
            event_id=event.id,
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db.add(task)
        db.flush()
        return task

    def _create_subtask(
        self,
        db,
        user,
        task,
        status="queued",
        object_type="Event",
        object_id=None,
    ):
        now = datetime.now(timezone.utc)
        subtask = SubTaskModel(
            id=uuid.uuid4(),
            name="Deploy VM",
            status=status,
            object_type=object_type,
            object_id=str(object_id or task.event_id),
            action="events_actions_start",
            attempt="1",
            parent_task=task.id,
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db.add(subtask)
        db.flush()
        return subtask

    def _create_vm(
        self,
        db,
        user,
        event,
        status="running",
        ipv4="10.0.0.1",
        prevent_delete=False,
    ):
        now = datetime.now(timezone.utc)
        vm = VirtualMachine(
            id=uuid.uuid4(),
            name=f"vm-{uuid.uuid4().hex[:6]}",
            cpu=2,
            ram=4096,
            disk=50,
            status=status,
            event=event.id,
            ipv4=ipv4,
            prevent_delete=prevent_delete,
            proxmoxId=100,
            proxmoxNode="pve-node-01",
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db.add(vm)
        db.flush()
        return vm

    def _create_guac_profile(self, db, user):
        now = datetime.now(timezone.utc)
        gcp = GuacamoleConnectionProfile(
            id=uuid.uuid4(),
            port=3389,
            protocol="RDP",
            username="admin",
            password="secret",
            objectId=uuid.uuid4(),
            objectType="Template",
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db.add(gcp)
        db.flush()
        return gcp

    def _create_guacamole(self, db, user, event, profile, identifier=None):
        now = datetime.now(timezone.utc)
        guac = Guacamole(
            id=uuid.uuid4(),
            name=f"guac-{uuid.uuid4().hex[:6]}",
            connection_profile=profile.id,
            identifier=identifier,
            userId=user.id,
            eventId=event.id,
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db.add(guac)
        db.flush()
        return guac

    # ------------------------------------------------------------------
    # statusInitiator per status
    # ------------------------------------------------------------------

    def test_initiator_geplant_is_creator(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
    ):
        """For Geplant, the initiator is the event creator, not updatedById."""
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
            creator=system_user,
        )
        result = self.crud.get_status(db_session, event.id)
        assert result.currentStatus == "Geplant"
        assert result.statusInitiator == system_user.id

    def test_initiator_deploying_is_start_task_creator(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Deploying"].id,
            sample_course.id,
        )
        task = self._create_task(
            db_session, system_user, event, name="Start Event"
        )
        self._create_subtask(db_session, active_user, task)

        result = self.crud.get_status(db_session, event.id)
        assert result.currentStatus == "Deploying"
        assert result.statusInitiator == system_user.id

    def test_initiator_aktiv_is_start_task_creator(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Aktiv"].id,
            sample_course.id,
        )
        task = self._create_task(
            db_session, system_user, event, name="Start Event"
        )
        self._create_subtask(db_session, active_user, task)

        result = self.crud.get_status(db_session, event.id)
        assert result.currentStatus == "Aktiv"
        assert result.statusInitiator == system_user.id

    def test_initiator_deployment_fehler_is_start_task_creator(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Deployment Fehler"].id,
            sample_course.id,
        )
        task = self._create_task(
            db_session, system_user, event, name="Start Event"
        )
        self._create_subtask(db_session, active_user, task, status="failed")

        result = self.crud.get_status(db_session, event.id)
        assert result.currentStatus == "Deployment Fehler"
        assert result.statusInitiator == system_user.id

    def test_initiator_archiving_is_end_task_creator(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Archiving"].id,
            sample_course.id,
        )
        task = self._create_task(
            db_session, system_user, event, name="End Event"
        )
        self._create_subtask(db_session, active_user, task)

        result = self.crud.get_status(db_session, event.id)
        assert result.currentStatus == "Archiving"
        assert result.statusInitiator == system_user.id

    def test_initiator_archiviert_is_end_task_creator(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Archiviert"].id,
            sample_course.id,
        )
        task = self._create_task(
            db_session, system_user, event, name="End Event"
        )
        self._create_subtask(db_session, active_user, task, status="success")

        result = self.crud.get_status(db_session, event.id)
        assert result.currentStatus == "Archiviert"
        assert result.statusInitiator == system_user.id

    def test_initiator_archival_fehler_is_end_task_creator(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Archival Fehler"].id,
            sample_course.id,
        )
        task = self._create_task(
            db_session, system_user, event, name="End Event"
        )
        self._create_subtask(db_session, active_user, task, status="failed")

        result = self.crud.get_status(db_session, event.id)
        assert result.currentStatus == "Archival Fehler"
        assert result.statusInitiator == system_user.id

    def test_initiator_core_fehler_falls_back_to_updated_by(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
    ):
        """Core Fehler has no associated task, so initiator falls back to updatedById."""
        event = self._create_event(
            db_session,
            system_user,
            event_statuses["Core Fehler"].id,
            sample_course.id,
        )
        # updatedById is active_user (set by _create_event), createdById is system_user
        result = self.crud.get_status(db_session, event.id)
        assert result.currentStatus == "Core Fehler"
        assert result.statusInitiator == system_user.id  # updatedById

    def test_initiator_inaktiv_falls_back_to_updated_by(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
    ):
        """Inaktiv is not in any lifecycle set, so initiator falls back to updatedById."""
        event = self._create_event(
            db_session,
            system_user,
            event_statuses["Inaktiv"].id,
            sample_course.id,
        )
        result = self.crud.get_status(db_session, event.id)
        assert result.currentStatus == "Inaktiv"
        assert result.statusInitiator == system_user.id  # updatedById

    def test_initiator_uses_most_recent_start_task(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
    ):
        """When an event has been restarted, initiator should be from the latest task."""
        now = datetime.now(timezone.utc)
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Deploying"].id,
            sample_course.id,
        )
        # Older task created by system_user
        old_task = TaskModel(
            id=uuid.uuid4(),
            name="Start Event",
            status="failed",
            event_id=event.id,
            createdAt=now - timedelta(hours=2),
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(old_task)
        # Newer task created by active_user
        new_task = TaskModel(
            id=uuid.uuid4(),
            name="Start Event",
            status="queued",
            event_id=event.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(new_task)
        db_session.flush()
        self._create_subtask(db_session, active_user, new_task)

        result = self.crud.get_status(db_session, event.id)
        assert result.statusInitiator == active_user.id

    # ------------------------------------------------------------------
    # VM stats
    # ------------------------------------------------------------------

    def test_vm_stats_empty_event(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        result = self.crud.get_status(db_session, event.id)
        assert result.vmStats.total == 0
        assert result.vmStats.running == 0
        assert result.vmStats.stopped == 0
        assert result.vmStats.pending == 0
        assert result.vmStats.protected == 0

    def test_vm_stats_counts_by_status(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Aktiv"].id,
            sample_course.id,
        )
        self._create_vm(
            db_session, active_user, event, status="running", ipv4="10.0.0.1"
        )
        self._create_vm(
            db_session, active_user, event, status="running", ipv4="10.0.0.2"
        )
        self._create_vm(
            db_session, active_user, event, status="stopped", ipv4="10.0.0.3"
        )
        self._create_vm(
            db_session, active_user, event, status="stopped", ipv4=None
        )  # pending

        result = self.crud.get_status(db_session, event.id)
        assert result.vmStats.total == 4
        assert result.vmStats.running == 2
        assert result.vmStats.stopped == 1
        assert result.vmStats.pending == 1  # no ipv4

    def test_vm_stats_protected_count(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Archiving"].id,
            sample_course.id,
        )
        self._create_vm(
            db_session, active_user, event, ipv4="10.0.0.1", prevent_delete=True
        )
        self._create_vm(
            db_session, active_user, event, ipv4="10.0.0.2", prevent_delete=True
        )
        self._create_vm(
            db_session,
            active_user,
            event,
            ipv4="10.0.0.3",
            prevent_delete=False,
        )

        result = self.crud.get_status(db_session, event.id)
        assert result.vmStats.protected == 2
        assert result.vmStats.total == 3

    def test_vm_stats_only_counts_vms_for_this_event(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event_a = self._create_event(
            db_session,
            active_user,
            event_statuses["Aktiv"].id,
            sample_course.id,
        )
        event_b = self._create_event(
            db_session,
            active_user,
            event_statuses["Aktiv"].id,
            sample_course.id,
        )
        self._create_vm(db_session, active_user, event_a, ipv4="10.0.0.1")
        self._create_vm(db_session, active_user, event_b, ipv4="10.0.0.2")
        self._create_vm(db_session, active_user, event_b, ipv4="10.0.0.3")

        result = self.crud.get_status(db_session, event_a.id)
        assert result.vmStats.total == 1

    # ------------------------------------------------------------------
    # Connection stats
    # ------------------------------------------------------------------

    def test_connection_stats_zero_when_no_guacs(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        result = self.crud.get_status(db_session, event.id)
        assert result.connectionStats.total == 0
        assert result.connectionStats.deployed == 0
        assert result.connectionStats.pending == 0

    def test_connection_stats_counts_deployed_and_pending(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Aktiv"].id,
            sample_course.id,
        )
        gcp = self._create_guac_profile(db_session, active_user)
        self._create_guacamole(
            db_session, active_user, event, gcp, identifier=42
        )
        self._create_guacamole(
            db_session, active_user, event, gcp, identifier=43
        )
        self._create_guacamole(
            db_session, active_user, event, gcp, identifier=None
        )

        result = self.crud.get_status(db_session, event.id)
        assert result.connectionStats.total == 3
        assert result.connectionStats.deployed == 2
        assert result.connectionStats.pending == 1

    def test_connection_stats_only_counts_guacs_for_this_event(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event_a = self._create_event(
            db_session,
            active_user,
            event_statuses["Aktiv"].id,
            sample_course.id,
        )
        event_b = self._create_event(
            db_session,
            active_user,
            event_statuses["Aktiv"].id,
            sample_course.id,
        )
        gcp = self._create_guac_profile(db_session, active_user)
        self._create_guacamole(
            db_session, active_user, event_a, gcp, identifier=1
        )
        self._create_guacamole(
            db_session, active_user, event_b, gcp, identifier=2
        )
        self._create_guacamole(
            db_session, active_user, event_b, gcp, identifier=None
        )

        result = self.crud.get_status(db_session, event_a.id)
        assert result.connectionStats.total == 1
        assert result.connectionStats.deployed == 1
        assert result.connectionStats.pending == 0

    # ------------------------------------------------------------------
    # Task stats
    # ------------------------------------------------------------------

    def test_task_stats_empty(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        result = self.crud.get_status(db_session, event.id)
        assert result.taskStats.total == 0
        assert result.taskStats.queued == 0
        assert result.taskStats.processing == 0
        assert result.taskStats.success == 0
        assert result.taskStats.failed == 0

    def test_task_stats_counts_all_subtask_statuses(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Deploying"].id,
            sample_course.id,
        )
        task = self._create_task(
            db_session, active_user, event, name="Start Event"
        )
        self._create_subtask(db_session, active_user, task, status="queued")
        self._create_subtask(db_session, active_user, task, status="queued")
        self._create_subtask(db_session, active_user, task, status="processing")
        self._create_subtask(db_session, active_user, task, status="success")
        self._create_subtask(db_session, active_user, task, status="failed")

        result = self.crud.get_status(db_session, event.id)
        assert result.taskStats.total == 5
        assert result.taskStats.queued == 2
        assert result.taskStats.processing == 1
        assert result.taskStats.success == 1
        assert result.taskStats.failed == 1

    def test_task_stats_spans_multiple_tasks(
        self, db_session, active_user, event_statuses, sample_course
    ):
        """Counts subtasks across all tasks for the event (start + end lifecycle)."""
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Archiviert"].id,
            sample_course.id,
        )
        start_task = self._create_task(
            db_session, active_user, event, name="Start Event"
        )
        end_task = self._create_task(
            db_session, active_user, event, name="End Event"
        )
        self._create_subtask(
            db_session, active_user, start_task, status="success"
        )
        self._create_subtask(
            db_session, active_user, start_task, status="success"
        )
        self._create_subtask(
            db_session, active_user, end_task, status="success"
        )
        self._create_subtask(db_session, active_user, end_task, status="failed")

        result = self.crud.get_status(db_session, event.id)
        assert result.taskStats.total == 4
        assert result.taskStats.success == 3
        assert result.taskStats.failed == 1

    def test_task_stats_only_counts_subtasks_for_this_event(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event_a = self._create_event(
            db_session,
            active_user,
            event_statuses["Deploying"].id,
            sample_course.id,
        )
        event_b = self._create_event(
            db_session,
            active_user,
            event_statuses["Deploying"].id,
            sample_course.id,
        )
        task_a = self._create_task(
            db_session, active_user, event_a, name="Start Event"
        )
        task_b = self._create_task(
            db_session, active_user, event_b, name="Start Event"
        )
        self._create_subtask(
            db_session, active_user, task_a, status="processing"
        )
        self._create_subtask(db_session, active_user, task_b, status="failed")
        self._create_subtask(db_session, active_user, task_b, status="failed")

        result = self.crud.get_status(db_session, event_a.id)
        assert result.taskStats.total == 1
        assert result.taskStats.processing == 1
        assert result.taskStats.failed == 0

    # ------------------------------------------------------------------
    # events list (task/subtask detail)
    # ------------------------------------------------------------------

    def test_events_list_contains_task_and_subtasks(
        self, db_session, active_user, event_statuses, sample_course
    ):
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Deploying"].id,
            sample_course.id,
        )
        task = self._create_task(
            db_session, active_user, event, name="Start Event"
        )
        st = self._create_subtask(
            db_session, active_user, task, status="processing"
        )

        result = self.crud.get_status(db_session, event.id)
        assert len(result.tasks) == 1
        assert result.tasks[0].id == task.id
        assert result.tasks[0].initiatedBy == active_user.id
        assert len(result.tasks[0].subTasks) == 1
        assert result.tasks[0].subTasks[0].id == st.id
        assert result.tasks[0].subTasks[0].status == "processing"

    def test_events_list_excludes_non_lifecycle_tasks(
        self, db_session, active_user, event_statuses, sample_course
    ):
        """Tasks whose name is not Start/End Event are excluded from the list."""
        event = self._create_event(
            db_session,
            active_user,
            event_statuses["Aktiv"].id,
            sample_course.id,
        )
        # Task attached to the event but not a lifecycle task
        task = self._create_task(
            db_session, active_user, event, name="Reschedule Event"
        )
        self._create_subtask(db_session, active_user, task, status="success")

        result = self.crud.get_status(db_session, event.id)
        assert result.tasks == []
