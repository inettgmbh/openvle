"""Tests for core/moodle.py - Moodle business logic + worker functions."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from core.moodlelib import MoodleAPIError
from models import Event, EventsUser, Role, SubTask, Task, User
from pve.worker_utils import TaskException
from tests.helpers.mock_moodle import MockMoodleClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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


def _make_subtask(db, system_user, parent_task, action="moodle_deploy"):
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


def _make_event(db, system_user, course, event_statuses, moodle_course_id=None):
    now = datetime.now(timezone.utc)
    event = Event(
        id=uuid.uuid4(),
        name=f"Test Event {uuid.uuid4().hex[:6]}",
        slug=uuid.uuid4().hex[:8],
        dateStart=now.date(),
        status=event_statuses["Geplant"].id,
        course=course.id,
        moodleCourseId=moodle_course_id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(event)
    db.flush()
    return event


def _make_user(db, system_user, username, email, name=None):
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        username=username,
        name=name or username.title(),
        email=email,
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


def _make_events_user(db, system_user, event, user, role):
    now = datetime.now(timezone.utc)
    eu = EventsUser(
        id=uuid.uuid4(),
        event_id=event.id,
        user_id=user.id,
        role_id=role.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(eu)
    db.flush()
    return eu


def _patch_moodle_worker(monkeypatch, db_session, mock_moodle, **settings_overrides):
    """Patch SessionLocal + moodle_connect + settings for worker tests."""
    monkeypatch.setattr("core.moodle.SessionLocal", lambda: db_session)

    import controllers.sub_tasks as st

    monkeypatch.setattr(st, "SessionLocal", lambda: db_session)

    monkeypatch.setattr(
        "core.moodle.moodle_connect",
        lambda **kw: mock_moodle,
    )

    mock_settings = MagicMock()
    mock_settings.moodle_enabled = True
    mock_settings.moodle_url = "https://moodle.test"
    mock_settings.moodle_token = "test-token"
    mock_settings.moodle_verify_ssl = False
    mock_settings.moodle_timeout = 30
    mock_settings.moodle_sync_timeout = 10
    mock_settings.moodle_user_auth = "ldap"
    mock_settings.moodle_user_match_field = "email"
    mock_settings.moodle_course_visible = True
    mock_settings.moodle_delete_course_on_event_delete = False

    for key, value in settings_overrides.items():
        setattr(mock_settings, key, value)

    monkeypatch.setattr("core.moodle.settings", mock_settings)
    return mock_settings


# ---------------------------------------------------------------------------
# TestMoodleConnect
# ---------------------------------------------------------------------------
class TestMoodleConnect:
    def test_success_returns_client(self, monkeypatch):
        mock_client = MockMoodleClient()
        monkeypatch.setattr(
            "core.moodle.MoodleClient",
            lambda **kw: mock_client,
        )
        mock_settings = MagicMock()
        mock_settings.moodle_url = "https://moodle.test"
        mock_settings.moodle_token = "test-token"
        mock_settings.moodle_verify_ssl = False
        mock_settings.moodle_timeout = 30
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        from core.moodle import moodle_connect

        result = moodle_connect()
        assert result is mock_client

    def test_failure_returns_false(self, monkeypatch):
        def failing_client(**kw):
            raise ConnectionError("no connection")

        monkeypatch.setattr("core.moodle.MoodleClient", failing_client)
        mock_settings = MagicMock()
        mock_settings.moodle_url = "https://moodle.test"
        mock_settings.moodle_token = "test-token"
        mock_settings.moodle_verify_ssl = False
        mock_settings.moodle_timeout = 30
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        from core.moodle import moodle_connect

        result = moodle_connect()
        assert result is False

    def test_custom_timeout_passed(self, monkeypatch):
        captured = {}

        def capturing_client(**kw):
            captured.update(kw)
            mock = MockMoodleClient()
            return mock

        monkeypatch.setattr("core.moodle.MoodleClient", capturing_client)
        mock_settings = MagicMock()
        mock_settings.moodle_url = "https://moodle.test"
        mock_settings.moodle_token = "test-token"
        mock_settings.moodle_verify_ssl = False
        mock_settings.moodle_timeout = 30
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        from core.moodle import moodle_connect

        moodle_connect(timeout=60)
        assert captured["timeout"] == 60


# ---------------------------------------------------------------------------
# TestResolveMoodleUser
# ---------------------------------------------------------------------------
class TestResolveMoodleUser:
    def test_found_by_email(self):
        mock = MockMoodleClient()
        mock.returns["get_users_by_field"] = [{"id": 42}]

        from core.moodle import resolve_moodle_user

        result = resolve_moodle_user(mock, "test@example.com", "testuser")
        assert result == 42

    def test_found_by_username(self):
        mock = MockMoodleClient()
        mock.returns["get_users_by_field"] = [{"id": 99}]

        from core.moodle import resolve_moodle_user

        result = resolve_moodle_user(
            mock, "test@example.com", "testuser", match_field="username"
        )
        assert result == 99
        call = mock.calls[0]
        assert call["field"] == "username"
        assert call["values"] == ["testuser"]

    def test_not_found_returns_none(self):
        mock = MockMoodleClient()
        mock.returns["get_users_by_field"] = []

        from core.moodle import resolve_moodle_user

        result = resolve_moodle_user(mock, "test@example.com", "testuser")
        assert result is None

    def test_api_error_returns_none(self):
        mock = MockMoodleClient()
        mock._errors["get_users_by_field"] = MoodleAPIError("invalidparam", "Bad param")

        from core.moodle import resolve_moodle_user

        result = resolve_moodle_user(mock, "test@example.com", "testuser")
        assert result is None


# ---------------------------------------------------------------------------
# TestEnsureMoodleUser
# ---------------------------------------------------------------------------
class TestEnsureMoodleUser:
    def _make_kvs_user(
        self, username="jdoe", email="jdoe@example.com", name="John Doe"
    ):
        user = MagicMock(spec=User)
        user.username = username
        user.email = email
        user.name = name
        return user

    def test_existing_user_returns_id(self, monkeypatch):
        mock = MockMoodleClient()
        mock.returns["get_users_by_field"] = [{"id": 42}]

        mock_settings = MagicMock()
        mock_settings.moodle_user_match_field = "email"
        mock_settings.moodle_user_auth = "ldap"
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        from core.moodle import ensure_moodle_user

        user = self._make_kvs_user()
        result = ensure_moodle_user(mock, user)
        assert result == 42
        # _call should NOT have been called (no user creation)
        assert not any(c["method"] == "_call" for c in mock.calls)

    def test_new_user_created(self, monkeypatch):
        mock = MockMoodleClient()
        mock.returns["get_users_by_field"] = []
        mock.returns["_call"] = [{"id": 100, "username": "jdoe"}]

        mock_settings = MagicMock()
        mock_settings.moodle_user_match_field = "email"
        mock_settings.moodle_user_auth = "ldap"
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        from core.moodle import ensure_moodle_user

        user = self._make_kvs_user()
        result = ensure_moodle_user(mock, user)
        assert result == 100

    def test_name_splitting_two_parts(self, monkeypatch):
        mock = MockMoodleClient()
        mock.returns["get_users_by_field"] = []
        mock.returns["_call"] = [{"id": 101}]

        mock_settings = MagicMock()
        mock_settings.moodle_user_match_field = "email"
        mock_settings.moodle_user_auth = "ldap"
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        from core.moodle import ensure_moodle_user

        user = self._make_kvs_user(name="Max Mustermann")
        ensure_moodle_user(mock, user)

        call = next(c for c in mock.calls if c["method"] == "_call")
        assert call["params"]["users[0][firstname]"] == "Max"
        assert call["params"]["users[0][lastname]"] == "Mustermann"

    def test_name_splitting_single_name(self, monkeypatch):
        mock = MockMoodleClient()
        mock.returns["get_users_by_field"] = []
        mock.returns["_call"] = [{"id": 102}]

        mock_settings = MagicMock()
        mock_settings.moodle_user_match_field = "email"
        mock_settings.moodle_user_auth = "ldap"
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        from core.moodle import ensure_moodle_user

        user = self._make_kvs_user(username="madonna", name="Madonna")
        ensure_moodle_user(mock, user)

        call = next(c for c in mock.calls if c["method"] == "_call")
        assert call["params"]["users[0][firstname]"] == "Madonna"
        assert call["params"]["users[0][lastname]"] == "madonna"

    def test_name_splitting_three_parts(self, monkeypatch):
        mock = MockMoodleClient()
        mock.returns["get_users_by_field"] = []
        mock.returns["_call"] = [{"id": 103}]

        mock_settings = MagicMock()
        mock_settings.moodle_user_match_field = "email"
        mock_settings.moodle_user_auth = "ldap"
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        from core.moodle import ensure_moodle_user

        user = self._make_kvs_user(name="Jan van der Berg")
        ensure_moodle_user(mock, user)

        call = next(c for c in mock.calls if c["method"] == "_call")
        assert call["params"]["users[0][firstname]"] == "Jan"
        assert call["params"]["users[0][lastname]"] == "van der Berg"

    def test_name_none_uses_username(self, monkeypatch):
        mock = MockMoodleClient()
        mock.returns["get_users_by_field"] = []
        mock.returns["_call"] = [{"id": 104}]

        mock_settings = MagicMock()
        mock_settings.moodle_user_match_field = "email"
        mock_settings.moodle_user_auth = "ldap"
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        from core.moodle import ensure_moodle_user

        user = self._make_kvs_user(name=None)
        ensure_moodle_user(mock, user)

        call = next(c for c in mock.calls if c["method"] == "_call")
        assert call["params"]["users[0][firstname]"] == "jdoe"
        assert call["params"]["users[0][lastname]"] == "jdoe"

    def test_create_failed_raises(self, monkeypatch):
        mock = MockMoodleClient()
        mock.returns["get_users_by_field"] = []
        mock.returns["_call"] = []  # empty = creation failed

        mock_settings = MagicMock()
        mock_settings.moodle_user_match_field = "email"
        mock_settings.moodle_user_auth = "ldap"
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        from core.moodle import ensure_moodle_user

        user = self._make_kvs_user()
        with pytest.raises(MoodleAPIError, match="user_create_failed"):
            ensure_moodle_user(mock, user)

    def test_match_field_username(self, monkeypatch):
        mock = MockMoodleClient()
        mock.returns["get_users_by_field"] = [{"id": 55}]

        mock_settings = MagicMock()
        mock_settings.moodle_user_match_field = "username"
        mock_settings.moodle_user_auth = "ldap"
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        from core.moodle import ensure_moodle_user

        user = self._make_kvs_user()
        result = ensure_moodle_user(mock, user)
        assert result == 55
        call = mock.calls[0]
        assert call["field"] == "username"
        assert call["values"] == ["jdoe"]


# ---------------------------------------------------------------------------
# TestMoodleDeployCourseWorker
# ---------------------------------------------------------------------------
class TestMoodleDeployCourseWorker:
    def test_happy_path(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
        role_teacher,
        role_student,
    ):
        sample_course.moodleCourseId = 100
        db_session.flush()

        event = _make_event(db_session, system_user, sample_course, event_statuses)
        teacher = _make_user(
            db_session, system_user, "teacher1", "teacher1@example.com", "Teacher One"
        )
        student = _make_user(
            db_session, system_user, "student1", "student1@example.com", "Student One"
        )
        _make_events_user(db_session, system_user, event, teacher, role_teacher)
        _make_events_user(db_session, system_user, event, student, role_student)

        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_courses"] = [{"id": 100, "categoryid": 2}]
        mock_moodle.returns["duplicate_course"] = {"id": 200, "shortname": "DUP"}
        mock_moodle.returns["get_users_by_field"] = [{"id": 42}]

        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_deploy_course_worker

        moodle_deploy_course_worker(event.id, subtask.id)

        db_session.expire_all()
        refreshed_event = db_session.get(Event, event.id)
        assert refreshed_event.moodleCourseId == 200

        enrol_calls = [c for c in mock_moodle.calls if c["method"] == "enrol_users"]
        assert len(enrol_calls) == 1
        assert len(enrol_calls[0]["enrolments"]) == 2

    def test_connection_error_returns_502(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(db_session, system_user, sample_course, event_statuses)
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        monkeypatch.setattr("core.moodle.SessionLocal", lambda: db_session)
        import controllers.sub_tasks as st

        monkeypatch.setattr(st, "SessionLocal", lambda: db_session)
        monkeypatch.setattr("core.moodle.moodle_connect", lambda **kw: False)

        from core.moodle import moodle_deploy_course_worker

        with pytest.raises(TaskException):
            moodle_deploy_course_worker(event.id, subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_event_not_found_returns_404(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_deploy_course_worker

        with pytest.raises(TaskException, match="Event not found"):
            moodle_deploy_course_worker(uuid.uuid4(), subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_course_without_moodle_id_returns_400(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        # sample_course.moodleCourseId is None by default
        event = _make_event(db_session, system_user, sample_course, event_statuses)
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_deploy_course_worker

        with pytest.raises(TaskException, match="moodleCourseId"):
            moodle_deploy_course_worker(event.id, subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_api_error_on_duplicate_returns_400(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        sample_course.moodleCourseId = 100
        db_session.flush()

        event = _make_event(db_session, system_user, sample_course, event_statuses)
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_courses"] = [{"id": 100, "categoryid": 2}]
        mock_moodle._errors["duplicate_course"] = MoodleAPIError(
            "shortnametaken", "Short name already exists"
        )
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_deploy_course_worker

        with pytest.raises(TaskException):
            moodle_deploy_course_worker(event.id, subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_unexpected_error_returns_500(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        sample_course.moodleCourseId = 100
        db_session.flush()

        event = _make_event(db_session, system_user, sample_course, event_statuses)
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_courses"] = [{"id": 100, "categoryid": 2}]
        mock_moodle._errors["duplicate_course"] = RuntimeError("boom")
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_deploy_course_worker

        with pytest.raises(TaskException):
            moodle_deploy_course_worker(event.id, subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_one_user_ensure_fails_others_enrolled(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
        role_student,
    ):
        sample_course.moodleCourseId = 100
        db_session.flush()

        event = _make_event(db_session, system_user, sample_course, event_statuses)
        user_ok = _make_user(
            db_session, system_user, "user_ok", "ok@example.com", "Ok User"
        )
        user_fail = _make_user(
            db_session, system_user, "user_fail", "fail@example.com", "Fail User"
        )
        _make_events_user(db_session, system_user, event, user_ok, role_student)
        _make_events_user(db_session, system_user, event, user_fail, role_student)

        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        call_count = {"n": 0}

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_courses"] = [{"id": 100, "categoryid": 2}]
        mock_moodle.returns["duplicate_course"] = {"id": 200, "shortname": "DUP"}

        # First call succeeds, second raises
        def alternating_get_users(field, values):
            call_count["n"] += 1
            if call_count["n"] % 2 == 0:
                raise MoodleAPIError("error", "fail")
            return [{"id": 42}]

        mock_moodle.get_users_by_field = alternating_get_users

        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_deploy_course_worker

        moodle_deploy_course_worker(event.id, subtask.id)

        # Should still succeed with 1 enrolment
        enrol_calls = [c for c in mock_moodle.calls if c["method"] == "enrol_users"]
        assert len(enrol_calls) == 1
        assert len(enrol_calls[0]["enrolments"]) == 1

    def test_no_events_users_still_success(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        sample_course.moodleCourseId = 100
        db_session.flush()

        event = _make_event(db_session, system_user, sample_course, event_statuses)
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_courses"] = [{"id": 100, "categoryid": 2}]
        mock_moodle.returns["duplicate_course"] = {"id": 200, "shortname": "DUP"}
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_deploy_course_worker

        moodle_deploy_course_worker(event.id, subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "success"
        # No enrol_users call
        enrol_calls = [c for c in mock_moodle.calls if c["method"] == "enrol_users"]
        assert len(enrol_calls) == 0

    def test_unknown_role_uses_default_5(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        sample_course.moodleCourseId = 100
        db_session.flush()

        # Create a custom role not in ROLE_MAP
        now = datetime.now(timezone.utc)
        custom_role = Role(
            id=uuid.uuid4(),
            name="Gasthoerer",
            key="gasthoerer",
            protected=False,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(custom_role)
        db_session.flush()

        event = _make_event(db_session, system_user, sample_course, event_statuses)
        user = _make_user(
            db_session, system_user, "guest1", "guest@example.com", "Guest User"
        )
        _make_events_user(db_session, system_user, event, user, custom_role)

        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_courses"] = [{"id": 100, "categoryid": 2}]
        mock_moodle.returns["duplicate_course"] = {"id": 200, "shortname": "DUP"}
        mock_moodle.returns["get_users_by_field"] = [{"id": 42}]
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_deploy_course_worker

        moodle_deploy_course_worker(event.id, subtask.id)

        enrol_calls = [c for c in mock_moodle.calls if c["method"] == "enrol_users"]
        assert enrol_calls[0]["enrolments"][0]["roleid"] == 5


# ---------------------------------------------------------------------------
# TestMoodleEnrolUserWorker
# ---------------------------------------------------------------------------
class TestMoodleEnrolUserWorker:
    def test_happy_path(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        user = _make_user(
            db_session, system_user, "enrol_user", "eu@example.com", "Enrol User"
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_users_by_field"] = [{"id": 42}]
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_enrol_user_worker

        moodle_enrol_user_worker(event.id, user.id, "studierende", subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "success"

    def test_connection_error_returns_502(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        monkeypatch.setattr("core.moodle.SessionLocal", lambda: db_session)
        import controllers.sub_tasks as st

        monkeypatch.setattr(st, "SessionLocal", lambda: db_session)
        monkeypatch.setattr("core.moodle.moodle_connect", lambda **kw: False)

        from core.moodle import moodle_enrol_user_worker

        with pytest.raises(TaskException):
            moodle_enrol_user_worker(event.id, uuid.uuid4(), "studierende", subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_event_without_moodle_id_returns_400(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
        )  # no moodleCourseId
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_enrol_user_worker

        with pytest.raises(TaskException):
            moodle_enrol_user_worker(event.id, uuid.uuid4(), "studierende", subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_user_not_found_returns_404(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_enrol_user_worker

        with pytest.raises(TaskException, match="User not found"):
            moodle_enrol_user_worker(event.id, uuid.uuid4(), "studierende", subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_api_error_returns_400(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        user = _make_user(
            db_session, system_user, "enrol_err", "err@example.com", "Err User"
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_users_by_field"] = [{"id": 42}]
        mock_moodle._errors["enrol_users"] = MoodleAPIError("err", "enrol failed")
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_enrol_user_worker

        with pytest.raises(TaskException):
            moodle_enrol_user_worker(event.id, user.id, "studierende", subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_role_lehrende_maps_to_3(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        user = _make_user(
            db_session, system_user, "teacher_e", "te@example.com", "Teacher E"
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_users_by_field"] = [{"id": 42}]
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_enrol_user_worker

        moodle_enrol_user_worker(event.id, user.id, "lehrende", subtask.id)

        enrol_calls = [c for c in mock_moodle.calls if c["method"] == "enrol_users"]
        assert enrol_calls[0]["enrolments"][0]["roleid"] == 3

    def test_role_studierende_maps_to_5(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        user = _make_user(db_session, system_user, "stud_e", "se@example.com", "Stud E")
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_users_by_field"] = [{"id": 42}]
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_enrol_user_worker

        moodle_enrol_user_worker(event.id, user.id, "studierende", subtask.id)

        enrol_calls = [c for c in mock_moodle.calls if c["method"] == "enrol_users"]
        assert enrol_calls[0]["enrolments"][0]["roleid"] == 5


# ---------------------------------------------------------------------------
# TestMoodleUnenrolUserWorker
# ---------------------------------------------------------------------------
class TestMoodleUnenrolUserWorker:
    def test_happy_path(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        user = _make_user(
            db_session, system_user, "unenrol1", "ue1@example.com", "Unenrol User"
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_users_by_field"] = [{"id": 42}]
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_unenrol_user_worker

        moodle_unenrol_user_worker(event.id, user.id, "studierende", subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "success"

    def test_connection_error_returns_502(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        monkeypatch.setattr("core.moodle.SessionLocal", lambda: db_session)
        import controllers.sub_tasks as st

        monkeypatch.setattr(st, "SessionLocal", lambda: db_session)
        monkeypatch.setattr("core.moodle.moodle_connect", lambda **kw: False)

        from core.moodle import moodle_unenrol_user_worker

        with pytest.raises(TaskException):
            moodle_unenrol_user_worker(
                event.id, uuid.uuid4(), "studierende", subtask.id
            )

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_event_without_moodle_id_returns_400(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_unenrol_user_worker

        with pytest.raises(TaskException):
            moodle_unenrol_user_worker(
                event.id, uuid.uuid4(), "studierende", subtask.id
            )

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_user_not_in_db_returns_404(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_unenrol_user_worker

        with pytest.raises(TaskException, match="User not found"):
            moodle_unenrol_user_worker(
                event.id, uuid.uuid4(), "studierende", subtask.id
            )

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_moodle_user_not_found_returns_404(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        user = _make_user(
            db_session, system_user, "unenrol2", "ue2@example.com", "Unenrol Two"
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_users_by_field"] = []  # not found
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_unenrol_user_worker

        with pytest.raises(TaskException, match="Moodle user not found"):
            moodle_unenrol_user_worker(event.id, user.id, "studierende", subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_api_error_returns_400(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        user = _make_user(
            db_session, system_user, "unenrol3", "ue3@example.com", "Unenrol Three"
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_users_by_field"] = [{"id": 42}]
        mock_moodle._errors["unenrol_users"] = MoodleAPIError("err", "unenrol failed")
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_unenrol_user_worker

        with pytest.raises(TaskException):
            moodle_unenrol_user_worker(event.id, user.id, "studierende", subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"


# ---------------------------------------------------------------------------
# TestMoodleEndEventWorker
# ---------------------------------------------------------------------------
class TestMoodleEndEventWorker:
    def test_happy_path_students_unenrolled_course_hidden(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
        role_teacher,
        role_student,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        teacher = _make_user(
            db_session, system_user, "end_teacher", "et@example.com", "End Teacher"
        )
        student = _make_user(
            db_session, system_user, "end_student", "es@example.com", "End Student"
        )
        _make_events_user(db_session, system_user, event, teacher, role_teacher)
        _make_events_user(db_session, system_user, event, student, role_student)

        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_users_by_field"] = [{"id": 42}]
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_end_event_worker

        moodle_end_event_worker(event.id, subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "success"

        # Only students unenrolled (1 student), teacher not touched
        unenrol_calls = [c for c in mock_moodle.calls if c["method"] == "unenrol_users"]
        assert len(unenrol_calls) == 1

        # Course hidden
        update_calls = [c for c in mock_moodle.calls if c["method"] == "update_courses"]
        assert len(update_calls) == 1
        assert update_calls[0]["courses"][0]["visible"] == 0

    def test_connection_error_returns_502(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        monkeypatch.setattr("core.moodle.SessionLocal", lambda: db_session)
        import controllers.sub_tasks as st

        monkeypatch.setattr(st, "SessionLocal", lambda: db_session)
        monkeypatch.setattr("core.moodle.moodle_connect", lambda **kw: False)

        from core.moodle import moodle_end_event_worker

        with pytest.raises(TaskException):
            moodle_end_event_worker(event.id, subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_event_without_moodle_id_returns_400(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_end_event_worker

        with pytest.raises(TaskException, match="moodleCourseId"):
            moodle_end_event_worker(event.id, subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "failed"

    def test_student_resolve_failed_continues(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
        role_student,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        student = _make_user(
            db_session, system_user, "fail_res", "fr@example.com", "Fail Res"
        )
        _make_events_user(db_session, system_user, event, student, role_student)

        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_users_by_field"] = []  # resolve fails
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_end_event_worker

        moodle_end_event_worker(event.id, subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "success"
        # No unenrol calls, but course still hidden
        unenrol_calls = [c for c in mock_moodle.calls if c["method"] == "unenrol_users"]
        assert len(unenrol_calls) == 0
        update_calls = [c for c in mock_moodle.calls if c["method"] == "update_courses"]
        assert len(update_calls) == 1

    def test_student_unenrol_api_error_continues(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
        role_student,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        student = _make_user(
            db_session, system_user, "unerr_s", "us@example.com", "UErr Student"
        )
        _make_events_user(db_session, system_user, event, student, role_student)

        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        mock_moodle.returns["get_users_by_field"] = [{"id": 42}]
        mock_moodle._errors["unenrol_users"] = MoodleAPIError("err", "unenrol fail")
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_end_event_worker

        moodle_end_event_worker(event.id, subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "success"
        # Course still hidden despite unenrol error
        update_calls = [c for c in mock_moodle.calls if c["method"] == "update_courses"]
        assert len(update_calls) == 1

    def test_no_student_role_zero_unenrols(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
    ):
        # No role_student fixture → no "studierende" role in DB
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_end_event_worker

        moodle_end_event_worker(event.id, subtask.id)

        db_session.expire_all()
        refreshed = db_session.get(SubTask, subtask.id)
        assert refreshed.status == "success"
        # Course still hidden
        update_calls = [c for c in mock_moodle.calls if c["method"] == "update_courses"]
        assert len(update_calls) == 1

    def test_teacher_not_unenrolled(
        self,
        db_session,
        system_user,
        monkeypatch,
        sample_course,
        event_statuses,
        role_teacher,
    ):
        event = _make_event(
            db_session,
            system_user,
            sample_course,
            event_statuses,
            moodle_course_id=200,
        )
        teacher = _make_user(
            db_session, system_user, "keep_teach", "kt@example.com", "Keep Teacher"
        )
        _make_events_user(db_session, system_user, event, teacher, role_teacher)

        task = _make_task(db_session, system_user, event.id)
        subtask = _make_subtask(db_session, system_user, task)

        mock_moodle = MockMoodleClient()
        _patch_moodle_worker(monkeypatch, db_session, mock_moodle)

        from core.moodle import moodle_end_event_worker

        moodle_end_event_worker(event.id, subtask.id)

        # No unenrol calls for teacher
        unenrol_calls = [c for c in mock_moodle.calls if c["method"] == "unenrol_users"]
        assert len(unenrol_calls) == 0


# ---------------------------------------------------------------------------
# TestMoodleDeleteCourse
# ---------------------------------------------------------------------------
class TestMoodleDeleteCourse:
    def test_deletes_when_enabled(self, monkeypatch):
        mock_moodle = MockMoodleClient()
        monkeypatch.setattr(
            "core.moodle.moodle_connect",
            lambda **kw: mock_moodle,
        )

        mock_settings = MagicMock()
        mock_settings.moodle_enabled = True
        mock_settings.moodle_delete_course_on_event_delete = True
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        from core.moodle import moodle_delete_course

        moodle_delete_course(42)

        delete_calls = [c for c in mock_moodle.calls if c["method"] == "delete_courses"]
        assert len(delete_calls) == 1
        assert delete_calls[0]["ids"] == [42]

    def test_noop_when_moodle_disabled(self, monkeypatch):
        mock_settings = MagicMock()
        mock_settings.moodle_enabled = False
        mock_settings.moodle_delete_course_on_event_delete = True
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        connect_called = {"called": False}

        def track_connect(**kw):
            connect_called["called"] = True

        monkeypatch.setattr("core.moodle.moodle_connect", track_connect)

        from core.moodle import moodle_delete_course

        moodle_delete_course(42)
        assert connect_called["called"] is False

    def test_noop_when_delete_disabled(self, monkeypatch):
        mock_settings = MagicMock()
        mock_settings.moodle_enabled = True
        mock_settings.moodle_delete_course_on_event_delete = False
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        connect_called = {"called": False}

        def track_connect(**kw):
            connect_called["called"] = True

        monkeypatch.setattr("core.moodle.moodle_connect", track_connect)

        from core.moodle import moodle_delete_course

        moodle_delete_course(42)
        assert connect_called["called"] is False

    def test_connection_error_no_crash(self, monkeypatch):
        mock_settings = MagicMock()
        mock_settings.moodle_enabled = True
        mock_settings.moodle_delete_course_on_event_delete = True
        monkeypatch.setattr("core.moodle.settings", mock_settings)
        monkeypatch.setattr("core.moodle.moodle_connect", lambda **kw: False)

        from core.moodle import moodle_delete_course

        # Should not raise
        moodle_delete_course(42)

    def test_api_error_no_crash(self, monkeypatch):
        mock_moodle = MockMoodleClient()
        mock_moodle._errors["delete_courses"] = MoodleAPIError("err", "fail")
        monkeypatch.setattr(
            "core.moodle.moodle_connect",
            lambda **kw: mock_moodle,
        )

        mock_settings = MagicMock()
        mock_settings.moodle_enabled = True
        mock_settings.moodle_delete_course_on_event_delete = True
        monkeypatch.setattr("core.moodle.settings", mock_settings)

        from core.moodle import moodle_delete_course

        # Should not raise
        moodle_delete_course(42)
