"""Tests for controllers/mails.py - CRUDMail operations."""

import uuid
from datetime import datetime, timezone

import pytest

from controllers.mails import CRUDMail
from core.exceptions import MailSubjectSlugRenderError, ObjectNotFound
from models import Event, Language, Mail, MailAction, MailTemplate, SubTask, Task, User
from schemas.mails import MailCreate
from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def sample_language(db_session, system_user):
    return db_session.query(Language).filter_by(key="de_DE").one()


@pytest.fixture()
def sample_mail_action(db_session, system_user):
    now = datetime.now(timezone.utc)
    action = MailAction(
        id=uuid.uuid4(),
        name="Password Reset",
        description="Password reset action",
        slug="password_reset",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(action)
    db_session.flush()
    return action


@pytest.fixture()
def sample_mail_template(db_session, system_user, sample_language, sample_mail_action):
    now = datetime.now(timezone.utc)
    tpl = MailTemplate(
        id=uuid.uuid4(),
        name="Password Reset Template",
        subject="Reset your password",
        contentHTML="<p>Reset</p>",
        contentPlain="Reset",
        language=sample_language.id,
        mail_action=sample_mail_action.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(tpl)
    db_session.flush()
    return tpl


@pytest.fixture()
def sample_mail_template_with_slug(
    db_session, system_user, sample_language, sample_mail_action
):
    now = datetime.now(timezone.utc)
    tpl = MailTemplate(
        id=uuid.uuid4(),
        name="Event Deployment Template",
        subject="Deine Veranstaltung {{event.slug}} wurde erfolgreich ausgerollt.",
        contentHTML="<p>Deployed</p>",
        contentPlain="Deployed",
        language=sample_language.id,
        mail_action=sample_mail_action.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(tpl)
    db_session.flush()
    return tpl


@pytest.fixture()
def sample_event(db_session, system_user, event_statuses, sample_course):
    now = datetime.now(timezone.utc)
    event = Event(
        id=uuid.uuid4(),
        name="Test Event",
        slug="testevt",
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
    db_session.add(event)
    db_session.flush()
    return event


class TestCRUDMailCreate:
    def setup_method(self):
        self.crud = CRUDMail(Mail)

    def test_create_mail(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        sample_mail_template,
    ):
        request = create_mock_request(active_user)
        obj_in = MailCreate(
            toMail="recipient@example.com",
            subject="Test Mail",
            fromName="Sender",
            fromMail="sender@example.com",
            replyTo="sender@example.com",
            templateId=str(sample_mail_template.id),
            user_id=active_user.id,
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.toMail == "recipient@example.com"
        assert result.sendStatus == "queued"
        assert result.templateId == sample_mail_template.id

    def test_create_creates_task_and_subtask(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        sample_mail_template,
    ):
        request = create_mock_request(active_user)
        obj_in = MailCreate(
            toMail="recipient@example.com",
            subject="Task Mail",
            fromName="Sender",
            fromMail="sender@example.com",
            replyTo="sender@example.com",
            templateId=str(sample_mail_template.id),
            user_id=active_user.id,
        )
        self.crud.create(db_session, request, obj_in=obj_in)

        tasks = db_session.query(Task).all()
        assert any("Send mail" in t.name for t in tasks)

        subtasks = db_session.query(SubTask).all()
        assert any(st.action == "mails_send" for st in subtasks)

    def test_create_enqueues_job(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        sample_mail_template,
    ):
        request = create_mock_request(active_user)
        obj_in = MailCreate(
            toMail="recipient@example.com",
            subject="Queue Mail",
            fromName="Sender",
            fromMail="sender@example.com",
            replyTo="sender@example.com",
            templateId=str(sample_mail_template.id),
            user_id=active_user.id,
        )
        self.crud.create(db_session, request, obj_in=obj_in)

        assert len(mock_redis_queues) > 0
        mail_jobs = [j for j in mock_redis_queues if j["queue"] == "queue_mails"]
        assert len(mail_jobs) >= 1


class TestCRUDMailCreateSystemMail:
    def setup_method(self):
        self.crud = CRUDMail(Mail)

    def test_create_system_mail(
        self,
        db_session,
        system_user,
        active_user,
        mock_redis_queues,
        sample_language,
        sample_mail_action,
        sample_mail_template,
    ):
        result = self.crud.create_system_mail(
            db_session,
            mail_action_slug="password_reset",
            user=active_user,
        )
        assert result is not None
        assert result.sendStatus == "queued"
        assert result.templateId == sample_mail_template.id

    def test_create_system_mail_nonexistent_action(
        self, db_session, active_user, mock_redis_queues
    ):
        with pytest.raises(ObjectNotFound):
            self.crud.create_system_mail(
                db_session,
                mail_action_slug="nonexistent_slug",
                user=active_user,
            )

    def test_system_mail_language_fallback(
        self,
        db_session,
        system_user,
        mock_redis_queues,
        sample_language,
        sample_mail_action,
        sample_mail_template,
    ):
        """When user locale has no template, falls back to German."""
        now = datetime.now(timezone.utc)
        french_user = User(
            id=uuid.uuid4(),
            username="frenchuser",
            name="French User",
            email="french@example.com",
            hashed_password="$2b$12$dummyhash",
            status="Active",
            locale="fr_FR",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(french_user)
        db_session.flush()

        result = self.crud.create_system_mail(
            db_session,
            mail_action_slug="password_reset",
            user=french_user,
        )
        # Should fall back to German template
        assert result is not None
        assert result.templateId == sample_mail_template.id


class TestCRUDMailResend:
    def setup_method(self):
        self.crud = CRUDMail(Mail)

    def test_resend_requeues(
        self,
        db_session,
        active_user,
        mock_redis_queues,
        sample_mail_template,
    ):
        request = create_mock_request(active_user)
        # First create a mail
        obj_in = MailCreate(
            toMail="recipient@example.com",
            subject="Resend Mail",
            fromName="Sender",
            fromMail="sender@example.com",
            replyTo="sender@example.com",
            templateId=str(sample_mail_template.id),
            user_id=active_user.id,
        )
        mail = self.crud.create(db_session, request, obj_in=obj_in)

        # Get the subtask
        subtask = (
            db_session.query(SubTask).filter(SubTask.object_id == str(mail.id)).first()
        )
        assert subtask is not None

        # Mark as failed
        subtask.status = "failed"
        db_session.flush()

        initial_count = len(mock_redis_queues)
        result = self.crud.resend(db_session, request, kvs_subtask_object_id=subtask.id)
        assert result.status == "queued"
        assert result.attempt == "0"
        assert len(mock_redis_queues) > initial_count


class TestCRUDMailSlugRendering:
    """Tests for event.slug placeholder rendering in system mails."""

    def setup_method(self):
        self.crud = CRUDMail(Mail)

    def test_slug_rendered_in_subject(
        self,
        db_session,
        system_user,
        active_user,
        mock_redis_queues,
        sample_language,
        sample_mail_action,
        sample_mail_template_with_slug,
        sample_event,
    ):
        """Template subject with {{event.slug}} gets the slug substituted."""
        result = self.crud.create_system_mail(
            db_session,
            mail_action_slug="password_reset",
            user=active_user,
            event_id=sample_event.id,
        )
        assert result is not None
        mail = db_session.get(Mail, result.id)
        assert sample_event.slug in mail.subject

    def test_slug_whitespace_variant_rendered_in_subject(
        self,
        db_session,
        system_user,
        active_user,
        mock_redis_queues,
        sample_language,
        sample_mail_action,
        sample_event,
    ):
        """Template subject with {{ event.slug }} (spaces) is also rendered correctly."""
        now = datetime.now(timezone.utc)
        tpl = MailTemplate(
            id=uuid.uuid4(),
            name="Whitespace Slug Template",
            subject="Veranstaltung {{ event.slug }} ist fertig.",
            contentHTML="<p>Done</p>",
            contentPlain="Done",
            language=sample_language.id,
            mail_action=sample_mail_action.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(tpl)
        db_session.flush()

        result = self.crud.create_system_mail(
            db_session,
            mail_action_slug="password_reset",
            user=active_user,
            event_id=sample_event.id,
        )
        assert result is not None
        mail = db_session.get(Mail, result.id)
        assert sample_event.slug in mail.subject

    def test_slug_placeholder_without_event_raises(
        self,
        db_session,
        system_user,
        active_user,
        mock_redis_queues,
        sample_language,
        sample_mail_action,
        sample_mail_template_with_slug,
    ):
        """Template has {{event.slug}} but no event_id provided → MailSubjectSlugRenderError."""
        with pytest.raises(MailSubjectSlugRenderError):
            self.crud.create_system_mail(
                db_session,
                mail_action_slug="password_reset",
                user=active_user,
                event_id=None,
            )

    def test_slug_placeholder_with_nonexistent_event_raises(
        self,
        db_session,
        system_user,
        active_user,
        mock_redis_queues,
        sample_language,
        sample_mail_action,
        sample_mail_template_with_slug,
    ):
        """Template has {{event.slug}} but event_id points to nothing → MailSubjectSlugRenderError."""
        with pytest.raises(MailSubjectSlugRenderError):
            self.crud.create_system_mail(
                db_session,
                mail_action_slug="password_reset",
                user=active_user,
                event_id=uuid.uuid4(),
            )
