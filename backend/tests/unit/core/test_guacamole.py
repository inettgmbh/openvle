"""Tests for core/guacamole.py - Guacamole integration functions.

Tests cover:
- guacamole_connect: success and failure
- check_user_exists: user exists, user not found, exception
- check_create_user: user exists, user created, failure
- create_user: success, failure, exception
- create_connection: success returns identifier, error returns error string
- create_user_connection: success and failure
- create_default_sharing_profiles: success returns list of identifiers
- get_or_create_connection_group: existing group, new group
- create_user_connection_group_permission: success, failure, exception
- create_user_sharing_profiles_permissions: success, failure, exception
- delete_connection: success and failure
- delete_user_connection: success, failure, exception
- delete_user: success and failure
- update_user_status: success
- update_user: success, attribute mapping, failure, exception
- update_connection: success, failure, exception
- provision_guacamole: full success flow
- guacamole_delete: success, connection failure, delete error
- guacamole_delete_worker: success flow, guacamole object not found
- provision_guacamole_worker: connection failure, VM not found
- guacamole_hostname_update: success, connection not found
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from models import (
    Guacamole as GuacamoleModel,
    GuacamoleConnectionProfile,
    SubTask,
    Task,
)
from pve.worker_utils import TaskException

from tests.helpers.mock_guacamole import MockGuacamoleClient


@pytest.fixture()
def guacamole_connection_profile(db_session, system_user):
    """Create a GuacamoleConnectionProfile for worker tests."""
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
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(gcp)
    db_session.flush()
    return gcp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task(db, system_user):
    now = datetime.now(timezone.utc)
    task = Task(
        id=uuid.uuid4(),
        name="guac-test-task",
        status="queued",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(task)
    db.flush()
    return task


def _make_subtask(db, system_user, parent_task, action="guac_action"):
    now = datetime.now(timezone.utc)
    subtask = SubTask(
        id=uuid.uuid4(),
        name="guac-test-subtask",
        status="queued",
        object_type="Guacamole",
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


def _make_guacamole(
    db, system_user, connection_profile_id, identifier=123, user_id=None
):
    now = datetime.now(timezone.utc)
    guac = GuacamoleModel(
        id=uuid.uuid4(),
        name="test-guac-connection",
        connection_profile=connection_profile_id,
        identifier=identifier,
        userId=user_id or system_user.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(guac)
    db.flush()
    return guac


# ---------------------------------------------------------------------------
# Tests: guacamole_connect
# ---------------------------------------------------------------------------


class TestGuacamoleConnect:
    """Tests for guacamole_connect()."""

    def test_success(self, monkeypatch):
        """Should return a guacamolelib.session instance on success."""
        mock_client = MockGuacamoleClient()
        monkeypatch.setattr(
            "core.guacamole.guacamolelib.session",
            lambda *args, **kwargs: mock_client,
        )

        from core.guacamole import guacamole_connect

        result = guacamole_connect()
        assert result is mock_client

    def test_failure_returns_false(self, monkeypatch):
        """Should return False when connection fails."""

        def _raise(*args, **kwargs):
            raise ConnectionError("Connection refused")

        monkeypatch.setattr("core.guacamole.guacamolelib.session", _raise)

        from core.guacamole import guacamole_connect

        result = guacamole_connect()
        assert result is False


# ---------------------------------------------------------------------------
# Tests: check_user_exists
# ---------------------------------------------------------------------------


class TestCheckUserExists:
    """Tests for check_user_exists()."""

    def test_user_exists(self):
        """Should return True when user exists."""
        client = MockGuacamoleClient()

        from core.guacamole import check_user_exists

        result = check_user_exists(client, "testuser")
        assert result is True

    def test_user_not_found(self):
        """Should return error string when user not found."""
        client = MockGuacamoleClient()
        client.detail_user = MagicMock(
            return_value={"message": "User not found"}
        )

        from core.guacamole import check_user_exists

        result = check_user_exists(client, "nonexistent")
        assert isinstance(result, str)
        assert "Guacamole Error (4)" in result

    def test_exception_handling(self):
        """Should return error string when exception occurs."""
        client = MockGuacamoleClient()
        client.detail_user = MagicMock(side_effect=Exception("Network error"))

        from core.guacamole import check_user_exists

        result = check_user_exists(client, "testuser")
        assert isinstance(result, str)
        assert "Guacamole Error (4)" in result
        assert "Network error" in result


# ---------------------------------------------------------------------------
# Tests: check_create_user
# ---------------------------------------------------------------------------


class TestCheckCreateUser:
    """Tests for check_create_user()."""

    def test_user_already_exists(self):
        """Should return True if user already exists."""
        client = MockGuacamoleClient()

        from core.guacamole import check_create_user

        result = check_create_user(client, "existinguser")
        assert result is True

    def test_user_created_successfully(self):
        """Should create user and return True when user does not exist."""
        client = MockGuacamoleClient()
        # detail_user returns "not found", then create_user succeeds
        client.detail_user = MagicMock(return_value={"message": "Not found"})
        client.create_user = MagicMock(return_value={"username": "newuser"})

        from core.guacamole import check_create_user

        result = check_create_user(client, "newuser")
        assert result is True
        client.create_user.assert_called_once_with("newuser", password=None)

    def test_user_creation_failure(self):
        """Should return error string when user creation fails."""
        client = MockGuacamoleClient()
        client.detail_user = MagicMock(return_value={"message": "Not found"})
        client.create_user = MagicMock(
            return_value={"message": "Internal error"}
        )

        from core.guacamole import check_create_user

        result = check_create_user(client, "newuser")
        assert isinstance(result, str)
        assert "Guacamole Error (0)" in result


# ---------------------------------------------------------------------------
# Tests: create_connection
# ---------------------------------------------------------------------------


class TestCreateConnection:
    """Tests for create_connection()."""

    def test_success_returns_identifier(self, monkeypatch):
        """Should return connection identifier on success."""
        client = MockGuacamoleClient()
        # manage_connection returns {"identifier": "123"} by default
        # list_connection_groups returns {} (no prefix logic triggered)

        # Disable prefix settings
        from core.guacamole import settings

        monkeypatch.setattr(settings, "guacamole_connections_prefix", "")
        monkeypatch.setattr(
            settings, "guacamole_connections_prefix_events", False
        )

        from core.guacamole import create_connection

        result = create_connection(
            guacamole=client,
            name="test-conn",
            connection_hostname="10.0.0.1",
            connection_username="admin",
            connection_password="pass",
        )
        assert result == "123"

    def test_error_returns_error_string(self, monkeypatch):
        """Should return error string when manage_connection returns error."""
        client = MockGuacamoleClient()
        client.manage_connection = MagicMock(
            return_value={"message": "Connection limit exceeded"}
        )
        client.list_connection_groups = MagicMock(return_value={})

        from core.guacamole import settings

        monkeypatch.setattr(settings, "guacamole_connections_prefix", "")
        monkeypatch.setattr(
            settings, "guacamole_connections_prefix_events", False
        )

        from core.guacamole import create_connection

        result = create_connection(
            guacamole=client,
            name="test-conn",
            connection_hostname="10.0.0.1",
            connection_username="admin",
            connection_password="pass",
        )
        assert isinstance(result, str)
        assert "Guacamole Error (10)" in result

    def test_exception_returns_error_string(self, monkeypatch):
        """Should return error string when an exception occurs."""
        client = MockGuacamoleClient()
        client.manage_connection = MagicMock(side_effect=Exception("Timeout"))
        client.list_connection_groups = MagicMock(return_value={})

        from core.guacamole import settings

        monkeypatch.setattr(settings, "guacamole_connections_prefix", "")
        monkeypatch.setattr(
            settings, "guacamole_connections_prefix_events", False
        )

        from core.guacamole import create_connection

        result = create_connection(
            guacamole=client,
            name="test-conn",
            connection_hostname="10.0.0.1",
            connection_username="admin",
            connection_password="pass",
        )
        assert "Guacamole Error (10)" in result


# ---------------------------------------------------------------------------
# Tests: create_user_connection
# ---------------------------------------------------------------------------


class TestCreateUserConnection:
    """Tests for create_user_connection()."""

    def test_success(self):
        """Should return True on success."""
        client = MockGuacamoleClient()
        # update_connection_permissions returns {} (no 'message' key)

        from core.guacamole import create_user_connection

        result = create_user_connection(client, "testuser", "123")
        assert result is True

    def test_failure(self):
        """Should return error string on failure."""
        client = MockGuacamoleClient()
        client.update_connection_permissions = MagicMock(
            return_value={"message": "Permission denied"}
        )

        from core.guacamole import create_user_connection

        result = create_user_connection(client, "testuser", "123")
        assert isinstance(result, str)
        assert "Guacamole Error (11)" in result


# ---------------------------------------------------------------------------
# Tests: create_default_sharing_profiles
# ---------------------------------------------------------------------------


class TestCreateDefaultSharingProfiles:
    """Tests for create_default_sharing_profiles()."""

    def test_success_returns_identifiers(self):
        """Should return a list of sharing profile identifiers."""
        client = MockGuacamoleClient()
        # create_sharing_profile returns {"identifier": "sp-1"} by default
        call_count = {"n": 0}

        def mock_create(**kwargs):
            call_count["n"] += 1
            return {"identifier": f"sp-{call_count['n']}"}

        client.create_sharing_profile = mock_create

        from core.guacamole import create_default_sharing_profiles

        result = create_default_sharing_profiles(client, "123")
        assert isinstance(result, list)
        assert len(result) == 2
        assert "sp-1" in result
        assert "sp-2" in result

    def test_failure_returns_error_string(self):
        """Should return error string when creation fails."""
        client = MockGuacamoleClient()
        client.create_sharing_profile = MagicMock(
            return_value={"message": "Profile creation failed"}
        )

        from core.guacamole import create_default_sharing_profiles

        result = create_default_sharing_profiles(client, "123")
        assert isinstance(result, str)
        assert "Guacamole Error (77)" in result


# ---------------------------------------------------------------------------
# Tests: delete_connection
# ---------------------------------------------------------------------------


class TestDeleteConnection:
    """Tests for delete_connection()."""

    def test_success(self):
        """Should return True on success."""
        client = MockGuacamoleClient()
        # delete_connection returns {} (no 'message' key)

        from core.guacamole import delete_connection

        result = delete_connection(client, "123")
        assert result is True

    def test_failure(self):
        """Should return error string on failure."""
        client = MockGuacamoleClient()
        client.delete_connection = MagicMock(
            return_value={"message": "Not found"}
        )

        from core.guacamole import delete_connection

        result = delete_connection(client, "999")
        assert isinstance(result, str)
        assert "Guacamole Error (30)" in result


# ---------------------------------------------------------------------------
# Tests: delete_user
# ---------------------------------------------------------------------------


class TestDeleteUser:
    """Tests for delete_user()."""

    def test_success(self):
        """Should return True on success."""
        client = MockGuacamoleClient()

        from core.guacamole import delete_user

        result = delete_user(client, "testuser")
        assert result is True

    def test_failure(self):
        """Should return error string on failure."""
        client = MockGuacamoleClient()
        client.delete_user = MagicMock(
            return_value={"message": "User not found"}
        )

        from core.guacamole import delete_user

        result = delete_user(client, "nonexistent")
        assert isinstance(result, str)
        assert "Guacamole Error (45)" in result


# ---------------------------------------------------------------------------
# Tests: update_user_status
# ---------------------------------------------------------------------------


class TestUpdateUserStatus:
    """Tests for update_user_status()."""

    def test_success_disable(self):
        """Should return True when disabling user."""
        client = MockGuacamoleClient()

        from core.guacamole import update_user_status

        result = update_user_status(client, "testuser", disabled=True)
        assert result is True

    def test_success_enable(self):
        """Should return True when enabling user."""
        client = MockGuacamoleClient()

        from core.guacamole import update_user_status

        result = update_user_status(client, "testuser", disabled=False)
        assert result is True

    def test_failure(self):
        """Should return error string on failure."""
        client = MockGuacamoleClient()
        client.update_user = MagicMock(
            return_value={"message": "Update failed"}
        )

        from core.guacamole import update_user_status

        result = update_user_status(client, "testuser", disabled=True)
        assert isinstance(result, str)
        assert "Guacamole Error (47)" in result


# ---------------------------------------------------------------------------
# Tests: provision_guacamole
# ---------------------------------------------------------------------------


class TestProvisionGuacamole:
    """Tests for provision_guacamole()."""

    def test_full_success_flow(self, monkeypatch):
        """Full success: connect, create user, create connection, permissions, sharing."""
        client = MockGuacamoleClient()
        monkeypatch.setattr(
            "core.guacamole.guacamolelib.session",
            lambda *args, **kwargs: client,
        )

        # Override settings for no prefix
        from core.guacamole import settings

        monkeypatch.setattr(settings, "guacamole_connections_prefix", "")
        monkeypatch.setattr(
            settings, "guacamole_connections_prefix_events", False
        )

        # create_sharing_profile needs to return list-compatible results
        call_count = {"n": 0}

        def mock_create_sp(**kwargs):
            call_count["n"] += 1
            return {"identifier": f"sp-{call_count['n']}"}

        client.create_sharing_profile = mock_create_sp

        from core.guacamole import provision_guacamole

        result = provision_guacamole(
            username="testuser",
            connection_name="test-conn",
            connection_hostname="10.0.0.1",
            connection_port=3389,
            connection_username="admin",
            connection_password="pass",
            connection_protocol="rdp",
        )

        # Should return the connection identifier as int
        assert result == 123

    def test_connection_failure_returns_error_string(self, monkeypatch):
        """Should return error string when guacamole_connect fails."""
        # guacamole_connect() catches exceptions internally and returns False.
        # provision_guacamole() then returns an error string.
        monkeypatch.setattr(
            "core.guacamole.guacamolelib.session",
            MagicMock(side_effect=ConnectionError("Connection refused")),
        )

        from core.guacamole import provision_guacamole

        result = provision_guacamole(
            username="testuser",
            connection_name="test-conn",
            connection_hostname="10.0.0.1",
            connection_port=3389,
            connection_username="admin",
            connection_password="pass",
            connection_protocol="rdp",
        )

        assert result == "Guacamole Error (999): Connection failed"


# ---------------------------------------------------------------------------
# Tests: guacamole_delete_worker
# ---------------------------------------------------------------------------


class TestGuacamoleDeleteWorker:
    """Tests for guacamole_delete_worker()."""

    def _patch_session_local(self, monkeypatch, db_session):
        """Patch SessionLocal in all modules that workers call."""
        monkeypatch.setattr("core.guacamole.SessionLocal", lambda: db_session)
        # Also patch in core.mariadb and controllers.sub_tasks because
        # worker_process_success/fail may call SessionLocal() internally
        import controllers.sub_tasks as sub_tasks_mod
        import core.mariadb as mariadb_mod

        monkeypatch.setattr(mariadb_mod, "SessionLocal", lambda: db_session)
        monkeypatch.setattr(sub_tasks_mod, "SessionLocal", lambda: db_session)
        # Patch mail_automated.SessionLocal too
        import core.mail_automated as mail_auto_mod

        monkeypatch.setattr(mail_auto_mod, "SessionLocal", lambda: db_session)

    def test_guacamole_object_not_found_succeeds(
        self, db_session, system_user, monkeypatch
    ):
        """When guacamole object does not exist in DB, should succeed gracefully."""
        self._patch_session_local(monkeypatch, db_session)

        client = MockGuacamoleClient()
        monkeypatch.setattr(
            "core.guacamole.guacamolelib.session",
            lambda *args, **kwargs: client,
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(
            db_session, system_user, task, action="guac_delete"
        )

        from core.guacamole import guacamole_delete_worker

        # Should succeed (not raise) because when kvs_guacamole is not found,
        # it reports success
        result = guacamole_delete_worker(
            kvs_guacamole_id=uuid.uuid4(),
            kvs_task_object_id=subtask.id,
        )
        assert result is True

    def test_guacamole_connection_failure(
        self, db_session, system_user, monkeypatch
    ):
        """When guacamole connection fails, should fail the worker."""
        self._patch_session_local(monkeypatch, db_session)
        monkeypatch.setattr(
            "core.guacamole.guacamolelib.session",
            MagicMock(side_effect=ConnectionError("refused")),
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(
            db_session, system_user, task, action="guac_delete"
        )

        from core.guacamole import guacamole_delete_worker

        with pytest.raises(
            TaskException, match="Failed to initialize Guacamole"
        ):
            guacamole_delete_worker(
                kvs_guacamole_id=uuid.uuid4(),
                kvs_task_object_id=subtask.id,
            )


# ---------------------------------------------------------------------------
# Tests: guacamole_hostname_update
# ---------------------------------------------------------------------------


class TestGuacamoleHostnameUpdate:
    """Tests for guacamole_hostname_update()."""

    def test_success(self, monkeypatch):
        """Should update hostname and return identifier."""
        client = MockGuacamoleClient()
        # detail_connection returns a valid dict, manage_connection returns no error
        client.manage_connection = MagicMock(return_value={})

        monkeypatch.setattr(
            "core.guacamole.guacamolelib.session",
            lambda *args, **kwargs: client,
        )

        from core.guacamole import guacamole_hostname_update

        result = guacamole_hostname_update(
            identifier="123",
            connection_name="test-conn",
            connection_hostname="10.0.0.99",
            connection_protocol="rdp",
        )
        assert result == "123"

    def test_connection_not_found(self, monkeypatch):
        """Should return error string when connection detail fails."""
        client = MockGuacamoleClient()
        client.detail_connection = MagicMock(return_value="Not found")

        monkeypatch.setattr(
            "core.guacamole.guacamolelib.session",
            lambda *args, **kwargs: client,
        )

        from core.guacamole import guacamole_hostname_update

        result = guacamole_hostname_update(
            identifier="999",
            connection_name="test-conn",
            connection_hostname="10.0.0.99",
            connection_protocol="rdp",
        )
        assert "Guacamole Error (11)" in result

    def test_guacamole_connect_failure(self, monkeypatch):
        """Should return error string when connection to guacamole fails."""
        monkeypatch.setattr(
            "core.guacamole.guacamolelib.session",
            MagicMock(side_effect=Exception("Connection refused")),
        )

        from core.guacamole import guacamole_hostname_update

        result = guacamole_hostname_update(
            identifier="123",
            connection_name="test-conn",
            connection_hostname="10.0.0.99",
            connection_protocol="rdp",
        )
        assert "Guacamole Error (11)" in result

    def test_manage_connection_error_response(self, monkeypatch):
        """Should return error string when manage_connection reports an error."""
        client = MockGuacamoleClient()
        client.manage_connection = MagicMock(
            return_value={"message": "Update failed"}
        )

        monkeypatch.setattr(
            "core.guacamole.guacamolelib.session",
            lambda *args, **kwargs: client,
        )

        from core.guacamole import guacamole_hostname_update

        result = guacamole_hostname_update(
            identifier="123",
            connection_name="test-conn",
            connection_hostname="10.0.0.99",
            connection_protocol="rdp",
        )
        assert "Guacamole Error (11)" in result
        assert "Update failed" in result


# ---------------------------------------------------------------------------
# Tests: create_user
# ---------------------------------------------------------------------------


class TestCreateUser:
    """Tests for create_user()."""

    def test_success(self):
        """Should return True on success."""
        client = MockGuacamoleClient()

        from core.guacamole import create_user

        result = create_user(client, "newuser")
        assert result is True

    def test_failure_returns_error_string(self):
        """Should return error string when creation fails."""
        client = MockGuacamoleClient()
        client.create_user = MagicMock(
            return_value={"message": "User already exists"}
        )

        from core.guacamole import create_user

        result = create_user(client, "existing")
        assert isinstance(result, str)
        assert "Guacamole Error (5)" in result

    def test_exception_returns_error_string(self):
        """Should return error string when an exception occurs."""
        client = MockGuacamoleClient()
        client.create_user = MagicMock(side_effect=Exception("Network error"))

        from core.guacamole import create_user

        result = create_user(client, "testuser")
        assert isinstance(result, str)
        assert "Guacamole Error (5)" in result
        assert "Network error" in result


# ---------------------------------------------------------------------------
# Tests: get_or_create_connection_group
# ---------------------------------------------------------------------------


class TestGetOrCreateConnectionGroup:
    """Tests for get_or_create_connection_group()."""

    def test_existing_group_returned(self):
        """Should return existing group identifier when name matches."""
        client = MockGuacamoleClient()
        connection_groups = {"42": {"name": "MyGroup"}, "99": {"name": "Other"}}

        from core.guacamole import get_or_create_connection_group

        result = get_or_create_connection_group(
            client, connection_groups, "MyGroup"
        )
        assert result == "42"

    def test_creates_new_group_when_not_found(self):
        """Should create new group and return its identifier."""
        client = MockGuacamoleClient()
        connection_groups = {"99": {"name": "Other"}}

        from core.guacamole import get_or_create_connection_group

        result = get_or_create_connection_group(
            client, connection_groups, "NewGroup", group_parent="ROOT"
        )
        # MockGuacamoleClient.create_connection_group returns {"identifier": "456"}
        assert result == "456"


# ---------------------------------------------------------------------------
# Tests: create_user_connection_group_permission
# ---------------------------------------------------------------------------


class TestCreateUserConnectionGroupPermission:
    """Tests for create_user_connection_group_permission()."""

    def test_success(self):
        """Should return True on success."""
        client = MockGuacamoleClient()

        from core.guacamole import create_user_connection_group_permission

        result = create_user_connection_group_permission(
            client, "testuser", "42"
        )
        assert result is True

    def test_failure_returns_error_string(self):
        """Should return error string when permission grant fails."""
        client = MockGuacamoleClient()
        client.update_connection_permissions = MagicMock(
            return_value={"message": "Permission denied"}
        )

        from core.guacamole import create_user_connection_group_permission

        result = create_user_connection_group_permission(
            client, "testuser", "42"
        )
        assert isinstance(result, str)
        assert "Guacamole Error (11G)" in result

    def test_exception_returns_error_string(self):
        """Should return error string when an exception occurs."""
        client = MockGuacamoleClient()
        client.update_connection_permissions = MagicMock(
            side_effect=Exception("Timeout")
        )

        from core.guacamole import create_user_connection_group_permission

        result = create_user_connection_group_permission(
            client, "testuser", "42"
        )
        assert isinstance(result, str)
        assert "Guacamole Error (11G)" in result


# ---------------------------------------------------------------------------
# Tests: create_user_sharing_profiles_permissions
# ---------------------------------------------------------------------------


class TestCreateUserSharingProfilesPermissions:
    """Tests for create_user_sharing_profiles_permissions()."""

    def test_success(self):
        """Should return True on success."""
        client = MockGuacamoleClient()

        from core.guacamole import create_user_sharing_profiles_permissions

        result = create_user_sharing_profiles_permissions(
            client, "testuser", ["sp-1", "sp-2"]
        )
        assert result is True

    def test_failure_returns_error_string(self):
        """Should return error string on failure."""
        client = MockGuacamoleClient()
        client.update_connection_permissions = MagicMock(
            return_value={"message": "Failed"}
        )

        from core.guacamole import create_user_sharing_profiles_permissions

        result = create_user_sharing_profiles_permissions(
            client, "testuser", ["sp-1"]
        )
        assert isinstance(result, str)
        assert "Guacamole Error (66)" in result

    def test_exception_returns_error_string(self):
        """Should return error string when an exception occurs."""
        client = MockGuacamoleClient()
        client.update_connection_permissions = MagicMock(
            side_effect=Exception("Network error")
        )

        from core.guacamole import create_user_sharing_profiles_permissions

        result = create_user_sharing_profiles_permissions(
            client, "testuser", ["sp-1"]
        )
        assert isinstance(result, str)
        assert "Guacamole Error (66)" in result


# ---------------------------------------------------------------------------
# Tests: delete_user_connection
# ---------------------------------------------------------------------------


class TestDeleteUserConnection:
    """Tests for delete_user_connection()."""

    def test_success(self):
        """Should return True on success."""
        client = MockGuacamoleClient()

        from core.guacamole import delete_user_connection

        result = delete_user_connection(client, "testuser", 123)
        assert result is True

    def test_failure_returns_error_string(self):
        """Should return error string on failure."""
        client = MockGuacamoleClient()
        client.update_user_connection = MagicMock(
            return_value={"message": "Connection not found"}
        )

        from core.guacamole import delete_user_connection

        result = delete_user_connection(client, "testuser", 999)
        assert isinstance(result, str)
        assert "Guacamole Error (40)" in result

    def test_exception_returns_error_string(self):
        """Should return error string when an exception occurs."""
        client = MockGuacamoleClient()
        client.update_user_connection = MagicMock(
            side_effect=Exception("Timeout")
        )

        from core.guacamole import delete_user_connection

        result = delete_user_connection(client, "testuser", 123)
        assert isinstance(result, str)
        assert "Guacamole Error (40)" in result


# ---------------------------------------------------------------------------
# Tests: update_user
# ---------------------------------------------------------------------------


class TestUpdateUser:
    """Tests for update_user()."""

    def test_success(self):
        """Should return True on success."""
        client = MockGuacamoleClient()

        from core.guacamole import update_user

        result = update_user(
            client,
            "testuser",
            {
                "guac-email-address": "test@example.com",
                "guac-full-name": "Test User",
            },
        )
        assert result is True

    def test_maps_attributes_correctly(self):
        """Should map only the expected attributes."""
        client = MockGuacamoleClient()
        calls = []
        original_update = client.update_user

        def capturing_update(username, attributes):
            calls.append(attributes)
            return original_update(username, attributes=attributes)

        client.update_user = capturing_update

        from core.guacamole import update_user

        update_user(
            client,
            "testuser",
            {"guac-email-address": "a@b.com", "unknown-attr": "ignored"},
        )
        assert len(calls) == 1
        attrs = calls[0]
        assert attrs["guac-email-address"] == "a@b.com"
        assert "unknown-attr" not in attrs
        # Unset attributes should default to None or ""
        assert attrs["guac-full-name"] is None

    def test_failure_returns_error_string(self):
        """Should return error string on failure."""
        client = MockGuacamoleClient()
        client.update_user = MagicMock(
            return_value={"message": "Update failed"}
        )

        from core.guacamole import update_user

        result = update_user(client, "testuser", {})
        assert isinstance(result, str)
        assert "Guacamole Error (48)" in result

    def test_exception_returns_error_string(self):
        """Should return error string when an exception occurs."""
        client = MockGuacamoleClient()
        client.update_user = MagicMock(side_effect=Exception("Connection lost"))

        from core.guacamole import update_user

        result = update_user(client, "testuser", {})
        assert isinstance(result, str)
        assert "Guacamole Error (48)" in result


# ---------------------------------------------------------------------------
# Tests: update_connection
# ---------------------------------------------------------------------------


class TestUpdateConnection:
    """Tests for update_connection()."""

    def test_success(self):
        """Should return True on success."""
        client = MockGuacamoleClient()
        client.manage_connection = MagicMock(return_value={})

        from core.guacamole import update_connection

        result = update_connection(
            guacamole=client,
            identifier=123,
            name="updated-conn",
            connection_hostname="10.0.0.2",
            connection_username="admin",
            connection_password="newpass",
        )
        assert result is True

    def test_failure_returns_error_string(self):
        """Should return error string when manage_connection reports error."""
        client = MockGuacamoleClient()
        client.manage_connection = MagicMock(
            return_value={"message": "Not found"}
        )

        from core.guacamole import update_connection

        result = update_connection(
            guacamole=client,
            identifier=999,
            name="conn",
            connection_hostname="10.0.0.1",
            connection_username="admin",
            connection_password="pass",
        )
        assert isinstance(result, str)
        assert "Guacamole Error (50)" in result

    def test_exception_returns_error_string(self):
        """Should return error string when an exception occurs."""
        client = MockGuacamoleClient()
        client.manage_connection = MagicMock(side_effect=Exception("Timeout"))

        from core.guacamole import update_connection

        result = update_connection(
            guacamole=client,
            identifier=123,
            name="conn",
            connection_hostname="10.0.0.1",
            connection_username="admin",
            connection_password="pass",
        )
        assert isinstance(result, str)
        assert "Guacamole Error (50)" in result


# ---------------------------------------------------------------------------
# Tests: guacamole_delete
# ---------------------------------------------------------------------------


class TestGuacamoleDelete:
    """Tests for guacamole_delete() (synchronous)."""

    def test_success(self, monkeypatch):
        """Should delete connection and return True."""
        client = MockGuacamoleClient()
        monkeypatch.setattr(
            "core.guacamole.guacamolelib.session",
            lambda *args, **kwargs: client,
        )

        from core.guacamole import guacamole_delete

        result = guacamole_delete(123)
        assert result is True

    def test_connection_failure(self, monkeypatch):
        """Should return error string when guacamole_connect fails."""
        monkeypatch.setattr(
            "core.guacamole.guacamolelib.session",
            MagicMock(side_effect=ConnectionError("refused")),
        )

        from core.guacamole import guacamole_delete

        result = guacamole_delete(123)
        assert result == "Guacamole Error (888): Connection failed"

    def test_delete_error_propagated(self, monkeypatch):
        """Should propagate error string from delete_connection."""
        client = MockGuacamoleClient()
        client.delete_connection = MagicMock(
            return_value={"message": "Not found"}
        )
        monkeypatch.setattr(
            "core.guacamole.guacamolelib.session",
            lambda *args, **kwargs: client,
        )

        from core.guacamole import guacamole_delete

        result = guacamole_delete(999)
        assert isinstance(result, str)
        assert "Guacamole Error (30)" in result


# ---------------------------------------------------------------------------
# Tests: provision_guacamole_worker
# ---------------------------------------------------------------------------


class TestProvisionGuacamoleWorker:
    """Tests for provision_guacamole_worker() (asynchronous)."""

    def _patch_session_local(self, monkeypatch, db_session):
        """Patch SessionLocal in all modules that workers call."""
        monkeypatch.setattr("core.guacamole.SessionLocal", lambda: db_session)
        import controllers.sub_tasks as sub_tasks_mod
        import core.mail_automated as mail_auto_mod
        import core.mariadb as mariadb_mod

        monkeypatch.setattr(mariadb_mod, "SessionLocal", lambda: db_session)
        monkeypatch.setattr(sub_tasks_mod, "SessionLocal", lambda: db_session)
        monkeypatch.setattr(mail_auto_mod, "SessionLocal", lambda: db_session)

    def test_connection_failure(self, db_session, system_user, monkeypatch):
        """Should fail when guacamole connection cannot be established."""
        self._patch_session_local(monkeypatch, db_session)
        monkeypatch.setattr(
            "core.guacamole.guacamolelib.session",
            MagicMock(side_effect=ConnectionError("refused")),
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(
            db_session, system_user, task, action="guac_provision"
        )

        from core.guacamole import provision_guacamole_worker

        with pytest.raises(
            TaskException, match="Failed to initialize Guacamole"
        ):
            provision_guacamole_worker(
                username="testuser",
                connection_name="test-PROV-conn",
                kvs_gcp_id=uuid.uuid4(),
                kvs_task_object_id=subtask.id,
                kvs_guacamole_id=uuid.uuid4(),
                kvs_vm_id=uuid.uuid4(),
            )

    def test_vm_not_found_fails(
        self,
        db_session,
        system_user,
        monkeypatch,
        guacamole_connection_profile,
    ):
        """Should fail when VirtualMachine is not found in DB."""
        self._patch_session_local(monkeypatch, db_session)
        client = MockGuacamoleClient()
        monkeypatch.setattr(
            "core.guacamole.guacamolelib.session",
            lambda *args, **kwargs: client,
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(
            db_session, system_user, task, action="guac_provision"
        )

        from core.guacamole import provision_guacamole_worker

        with pytest.raises(TaskException):
            provision_guacamole_worker(
                username="testuser",
                connection_name="test-PROV-conn",
                kvs_gcp_id=guacamole_connection_profile.id,
                kvs_task_object_id=subtask.id,
                kvs_guacamole_id=uuid.uuid4(),
                kvs_vm_id=uuid.uuid4(),  # non-existent VM
            )
