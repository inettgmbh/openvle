"""Tests for core/periodic_tasks.py - Scheduled/periodic task functions."""

import uuid
from datetime import date, datetime, timedelta, timezone
from models import (
    Event,
    EventStatus,
    Language,
    Mail,
    MailAction,
    MailTemplate,
    SubTask,
    Task,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_task(db, system_user, name="test-task", event_id=None):
    now = datetime.now(timezone.utc)
    task = Task(
        id=uuid.uuid4(),
        name=name,
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


def _make_subtask(db, system_user, parent_task, action="test_action", job_id=None):
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
        job_id=job_id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(subtask)
    db.flush()
    return subtask


def _make_event(
    db, system_user, event_statuses, sample_course, status_name, date_start, date_end
):
    now = datetime.now(timezone.utc)
    event = Event(
        id=uuid.uuid4(),
        name=f"test-event-{uuid.uuid4().hex[:6]}",
        slug=uuid.uuid4().hex[:8],
        dateStart=date_start,
        dateEnd=date_end,
        guacamole=True,
        status=event_statuses[status_name].id,
        course=sample_course.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(event)
    db.flush()
    return event


def _make_mail_objects(db, system_user, event_id, action_slug):
    """Create Language, MailAction, MailTemplate, and Mail for event-mail checks."""
    now = datetime.now(timezone.utc)

    # Use the seeded German language
    lang = db.query(Language).filter_by(key="de_DE").one()

    # MailAction
    action = db.query(MailAction).filter(MailAction.slug == action_slug).first()
    if not action:
        action = MailAction(
            id=uuid.uuid4(),
            name=f"Action {action_slug}",
            description=f"Action for {action_slug}",
            slug=action_slug,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db.add(action)
        db.flush()

    # MailTemplate — reuse seeded one if it exists
    tpl = (
        db.query(MailTemplate)
        .filter_by(language=lang.id, mail_action=action.id)
        .first()
    )
    if not tpl:
        tpl = MailTemplate(
            id=uuid.uuid4(),
            name=f"Template {action_slug} {uuid.uuid4().hex[:4]}",
            subject=f"Subject {action_slug}",
            contentHTML="<p>html</p>",
            contentPlain="plain",
            language=lang.id,
            mail_action=action.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db.add(tpl)
        db.flush()

    # Mail
    mail = Mail(
        id=uuid.uuid4(),
        subject=f"Subject {action_slug}",
        fromName="KVS",
        fromMail="kvs@example.com",
        toMail="user@example.com",
        sendStatus="sent",
        templateId=tpl.id,
        replyTo="kvs@example.com",
        event=event_id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(mail)
    db.flush()
    return mail, tpl, action


def _patch_periodic_session(monkeypatch, db_session):
    """Patch SessionLocal in periodic_tasks and related modules."""
    monkeypatch.setattr("core.periodic_tasks.SessionLocal", lambda: db_session)
    import core.mariadb as m
    import controllers.sub_tasks as st
    import core.mail_automated as ma

    monkeypatch.setattr(m, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(st, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(ma, "SessionLocal", lambda: db_session)


# ---------------------------------------------------------------------------
# Tests: check_for_event_mail_simple
# ---------------------------------------------------------------------------
class TestCheckForEventMailSimple:
    def test_returns_true_when_mail_exists(
        self, db_session, system_user, event_statuses, sample_course
    ):
        """Returns True when a matching mail exists for the event and slug."""
        event = _make_event(
            db_session,
            system_user,
            event_statuses,
            sample_course,
            "Geplant",
            date.today(),
            date.today(),
        )
        _make_mail_objects(db_session, system_user, event.id, "events_pre_start")

        from core.periodic_tasks import check_for_event_mail_simple

        result = check_for_event_mail_simple(db_session, event.id, "events_pre_start")
        assert result is True

    def test_returns_false_when_no_mail(
        self, db_session, system_user, event_statuses, sample_course
    ):
        """Returns False when no matching mail exists."""
        event = _make_event(
            db_session,
            system_user,
            event_statuses,
            sample_course,
            "Geplant",
            date.today(),
            date.today(),
        )

        from core.periodic_tasks import check_for_event_mail_simple

        result = check_for_event_mail_simple(db_session, event.id, "events_pre_start")
        assert result is False


# ---------------------------------------------------------------------------
# Tests: events_periodic
# ---------------------------------------------------------------------------
class TestEventsPeriodic:
    def test_no_events(self, db_session, system_user, monkeypatch):
        """No events in DB -> success message about no Events found."""
        _patch_periodic_session(monkeypatch, db_session)

        task = _make_task(db_session, system_user)
        _make_subtask(
            db_session,
            system_user,
            task,
            action="periodic_update",
            job_id="core_events_periodic",
        )

        from core.periodic_tasks import events_periodic

        result = events_periodic()
        assert result is True

    def test_geplant_too_early(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """Geplant event with dateStart far in future -> no action triggered."""
        _patch_periodic_session(monkeypatch, db_session)

        task = _make_task(db_session, system_user)
        _make_subtask(
            db_session,
            system_user,
            task,
            action="periodic_update",
            job_id="core_events_periodic",
        )

        # Event starts 60 days from now (well beyond prep time of 7 days)
        future_start = date.today() + timedelta(days=60)
        future_end = future_start + timedelta(days=30)
        _make_event(
            db_session,
            system_user,
            event_statuses,
            sample_course,
            "Geplant",
            future_start,
            future_end,
        )

        from core.periodic_tasks import events_periodic

        result = events_periodic()
        # Should succeed without triggering any actions
        assert result is True

    def test_geplant_due_to_start(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """Geplant event past prep time -> calls actions_start."""
        _patch_periodic_session(monkeypatch, db_session)

        task = _make_task(db_session, system_user)
        _make_subtask(
            db_session,
            system_user,
            task,
            action="periodic_update",
            job_id="core_events_periodic",
        )

        # Event dateStart is 14 days ago (past the 7-day prep time)
        past_start = date.today() - timedelta(days=14)
        future_end = date.today() + timedelta(days=30)
        event = _make_event(
            db_session,
            system_user,
            event_statuses,
            sample_course,
            "Geplant",
            past_start,
            future_end,
        )

        # Mock actions_start to record it was called
        started_events = []

        from controllers.events import CRUDEvent

        def mock_actions_start(self, db, request, id):
            started_events.append(id)

        monkeypatch.setattr(CRUDEvent, "actions_start", mock_actions_start)

        from core.periodic_tasks import events_periodic

        result = events_periodic()
        assert result is True
        assert event.id in started_events

    def test_aktiv_too_early(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """Aktiv event with dateEnd far in future -> no end action triggered."""
        _patch_periodic_session(monkeypatch, db_session)

        task = _make_task(db_session, system_user)
        _make_subtask(
            db_session,
            system_user,
            task,
            action="periodic_update",
            job_id="core_events_periodic",
        )

        past_start = date.today() - timedelta(days=10)
        future_end = date.today() + timedelta(days=60)
        _make_event(
            db_session,
            system_user,
            event_statuses,
            sample_course,
            "Aktiv",
            past_start,
            future_end,
        )

        ended_events = []

        from controllers.events import CRUDEvent

        monkeypatch.setattr(
            CRUDEvent,
            "actions_stop",
            lambda self, db, request, id: ended_events.append(id),
        )

        from core.periodic_tasks import events_periodic

        result = events_periodic()
        assert result is True
        assert len(ended_events) == 0

    def test_aktiv_due_to_end(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """Aktiv event past dateEnd + prep time -> calls actions_stop."""
        _patch_periodic_session(monkeypatch, db_session)

        task = _make_task(db_session, system_user)
        _make_subtask(
            db_session,
            system_user,
            task,
            action="periodic_update",
            job_id="core_events_periodic",
        )

        past_start = date.today() - timedelta(days=60)
        past_end = date.today() - timedelta(days=14)  # Well past the 7-day prep
        event = _make_event(
            db_session,
            system_user,
            event_statuses,
            sample_course,
            "Aktiv",
            past_start,
            past_end,
        )

        ended_events = []

        from controllers.events import CRUDEvent

        monkeypatch.setattr(
            CRUDEvent,
            "actions_stop",
            lambda self, db, request, id: ended_events.append(id),
        )

        from core.periodic_tasks import events_periodic

        result = events_periodic()
        assert result is True
        assert event.id in ended_events

    def test_start_error_sets_core_fehler(
        self, db_session, system_user, event_statuses, sample_course, monkeypatch
    ):
        """actions_start raising exception sets event status to 'Core Fehler'."""
        _patch_periodic_session(monkeypatch, db_session)

        task = _make_task(db_session, system_user)
        _make_subtask(
            db_session,
            system_user,
            task,
            action="periodic_update",
            job_id="core_events_periodic",
        )

        past_start = date.today() - timedelta(days=14)
        future_end = date.today() + timedelta(days=30)
        event = _make_event(
            db_session,
            system_user,
            event_statuses,
            sample_course,
            "Geplant",
            past_start,
            future_end,
        )

        from controllers.events import CRUDEvent
        from core.exceptions import BadRequestError

        def failing_start(self, db, request, id):
            raise BadRequestError(message="Start failed")

        monkeypatch.setattr(CRUDEvent, "actions_start", failing_start)

        from core.periodic_tasks import events_periodic

        result = events_periodic()
        assert result is True

        db_session.expire_all()
        refreshed_event = db_session.get(Event, event.id)
        error_status = db_session.get(EventStatus, refreshed_event.status)
        assert error_status.name == "Core Fehler"

    def test_session_local_failure(self, monkeypatch):
        """When SessionLocal() raises, returns error string."""

        def raise_connection_error():
            raise Exception("DB connection failed")

        monkeypatch.setattr("core.periodic_tasks.SessionLocal", raise_connection_error)

        from core.periodic_tasks import events_periodic

        result = events_periodic()
        assert result == "Unable to connect to MariaDB"


# ---------------------------------------------------------------------------
# Tests: mail_periodic_delete
# ---------------------------------------------------------------------------
class TestMailPeriodicDelete:
    def test_no_old_mails(self, db_session, system_user, monkeypatch):
        """No expired mails -> success message."""
        _patch_periodic_session(monkeypatch, db_session)

        task = _make_task(db_session, system_user)
        _make_subtask(
            db_session,
            system_user,
            task,
            action="periodic_delete",
            job_id="core_mail_periodic_delete",
        )

        from core.periodic_tasks import mail_periodic_delete

        result = mail_periodic_delete()
        assert result is True

    def test_removes_old_mails(self, db_session, system_user, monkeypatch):
        """Old mails (beyond max_age_weeks) are deleted."""
        _patch_periodic_session(monkeypatch, db_session)

        task = _make_task(db_session, system_user)
        _make_subtask(
            db_session,
            system_user,
            task,
            action="periodic_delete",
            job_id="core_mail_periodic_delete",
        )

        # Re-use the seeded language
        now = datetime.now(timezone.utc)
        lang = db_session.query(Language).filter_by(key="de_DE").one()

        action = MailAction(
            id=uuid.uuid4(),
            name="Delete Test",
            description="test",
            slug="delete_test",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(action)
        db_session.flush()

        tpl = MailTemplate(
            id=uuid.uuid4(),
            name="Delete Tpl",
            subject="Del",
            contentHTML="html",
            contentPlain="plain",
            language=lang.id,
            mail_action=action.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(tpl)
        db_session.flush()

        # Create an old mail (10 weeks ago, beyond the default 4-week cutoff)
        old_time = now - timedelta(weeks=10)
        old_mail = Mail(
            id=uuid.uuid4(),
            subject="Old Mail",
            fromName="KVS",
            fromMail="kvs@example.com",
            toMail="user@example.com",
            sendStatus="sent",
            templateId=tpl.id,
            replyTo="kvs@example.com",
            createdAt=old_time,
            updatedAt=old_time,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(old_mail)
        db_session.flush()

        old_mail_id = old_mail.id

        from core.periodic_tasks import mail_periodic_delete

        mail_periodic_delete()

        db_session.expire_all()
        deleted_mail = db_session.get(Mail, old_mail_id)
        assert deleted_mail is None


# ---------------------------------------------------------------------------
# Tests: tasks_enqueue
# ---------------------------------------------------------------------------
class TestTasksEnqueue:
    def test_creates_tasks_and_subtasks(self, db_session, system_user, monkeypatch):
        """tasks_enqueue creates Task/SubTask pairs in the database."""
        _patch_periodic_session(monkeypatch, db_session)

        from core.periodic_tasks import tasks_enqueue

        tasks_enqueue()

        # Verify tasks were created
        tasks = db_session.query(Task).all()
        task_names = [t.name for t in tasks]
        assert "Periodic: proxmox_node_info_periodic" in task_names
        assert "Periodic: core_events_periodic" in task_names
        assert "Periodic: core_mail_periodic_delete" in task_names

        # Verify subtasks were created
        subtasks = db_session.query(SubTask).all()
        subtask_job_ids = [st.job_id for st in subtasks]
        assert "proxmox_node_info_periodic" in subtask_job_ids
        assert "core_events_periodic" in subtask_job_ids
        assert "core_mail_periodic_delete" in subtask_job_ids

    def test_does_not_duplicate(self, db_session, system_user, monkeypatch):
        """Running tasks_enqueue twice doesn't create duplicate tasks."""
        _patch_periodic_session(monkeypatch, db_session)

        from core.periodic_tasks import tasks_enqueue

        tasks_enqueue()
        count_first = db_session.query(Task).count()

        tasks_enqueue()
        count_second = db_session.query(Task).count()

        assert count_first == count_second
