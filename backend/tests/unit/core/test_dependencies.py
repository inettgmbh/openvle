"""Tests for core/dependencies.py - get_db, get_current_user, PermissionChecker, _decode_and_load_user."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from models import ObjectPermission, Role, User
from models.associations import (
    user_role_association_table,
)
from tests.helpers.mock_request import create_mock_request


# ===========================================================================
# TestGetDb
# ===========================================================================


class TestGetDb:
    """Test get_db() generator."""

    def test_yields_session_and_closes(self, monkeypatch):
        """get_db should yield a session and close it afterwards."""
        from unittest.mock import MagicMock

        mock_session = MagicMock()
        monkeypatch.setattr("core.dependencies.SessionLocal", lambda: mock_session)

        from core.dependencies import get_db

        gen = get_db()
        db = next(gen)
        assert db is mock_session
        assert db.current_user_id is None

        # Exhaust generator (triggers finally block)
        try:
            next(gen)
        except StopIteration:
            pass
        mock_session.close.assert_called_once()

    def test_closes_on_exception(self, monkeypatch):
        """get_db should close the session even when an exception occurs."""
        from unittest.mock import MagicMock

        mock_session = MagicMock()
        monkeypatch.setattr("core.dependencies.SessionLocal", lambda: mock_session)

        from core.dependencies import get_db

        gen = get_db()
        next(gen)

        # Simulate an exception in the caller
        try:
            gen.throw(RuntimeError("test error"))
        except RuntimeError:
            pass
        mock_session.close.assert_called_once()


# ===========================================================================
# TestGetCurrentUser
# ===========================================================================


def _run_async(coro):
    """Run an async coroutine in a fresh event loop (avoids loop-reuse issues)."""
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestGetCurrentUser:
    """Test get_current_user() async wrapper."""

    def test_returns_user_on_valid_token(self, db_session, active_user):
        """Should return user when token is valid."""
        from core.dependencies import get_current_user

        token = _make_jwt({"sub": str(active_user.id)})
        result = _run_async(get_current_user(db=db_session, token=token))
        assert result.id == active_user.id

    def test_raises_on_policy_required_token(self, db_session, active_user):
        """Should raise OutstandingPoliciesException for policy_required token."""
        from core.dependencies import get_current_user
        from core.exceptions import OutstandingPoliciesException

        token = _make_jwt({"sub": str(active_user.id), "type": "policy_required"})
        with pytest.raises(OutstandingPoliciesException):
            _run_async(get_current_user(db=db_session, token=token))

    def test_raises_on_invalid_token(self, db_session, system_user):
        """Should raise on malformed token."""
        from core.dependencies import get_current_user
        from core.exceptions import InvalidAuthToken

        with pytest.raises(InvalidAuthToken):
            _run_async(get_current_user(db=db_session, token="bad-token"))


# ===========================================================================
# TestGetCurrentUserOptional
# ===========================================================================


class TestGetCurrentUserOptional:
    """Test get_current_user_optional() async wrapper."""

    def test_returns_user_on_valid_token(self, db_session, active_user):
        """Should return user when token is valid."""
        from core.dependencies import get_current_user_optional

        token = _make_jwt({"sub": str(active_user.id)})
        result = _run_async(get_current_user_optional(db=db_session, token=token))
        assert result.id == active_user.id

    def test_returns_false_on_invalid_token(self, db_session, system_user):
        """Should return False when token is invalid."""
        from core.dependencies import get_current_user_optional

        result = _run_async(get_current_user_optional(db=db_session, token="bad-token"))
        assert result is False

    def test_returns_false_on_expired_token(self, db_session, active_user):
        """Should return False when token is expired."""
        from core.dependencies import get_current_user_optional

        expired = datetime.now(timezone.utc) - timedelta(hours=1)
        token = _make_jwt({"sub": str(active_user.id), "exp": expired})
        result = _run_async(get_current_user_optional(db=db_session, token=token))
        assert result is False


# ===========================================================================
# TestGetCurrentUserReauth
# ===========================================================================


class TestGetCurrentUserReauth:
    """Test get_current_user_reauth() async wrapper."""

    def test_allows_policy_required_token(self, db_session, active_user):
        """Should return user even with policy_required token."""
        from core.dependencies import get_current_user_reauth

        token = _make_jwt({"sub": str(active_user.id), "type": "policy_required"})
        result = _run_async(get_current_user_reauth(db=db_session, token=token))
        assert result.id == active_user.id

    def test_raises_on_invalid_token(self, db_session, system_user):
        """Should raise on malformed token."""
        from core.dependencies import get_current_user_reauth
        from core.exceptions import InvalidAuthToken

        with pytest.raises(InvalidAuthToken):
            _run_async(get_current_user_reauth(db=db_session, token="bad-token"))

    def test_rejects_bearer_token(self, db_session, active_user):
        """Should reject regular bearer tokens (only policy_required allowed)."""
        from core.dependencies import get_current_user_reauth
        from core.exceptions import CredentialsNotValid

        token = _make_jwt({"sub": str(active_user.id), "type": "bearer"})
        with pytest.raises(CredentialsNotValid):
            _run_async(get_current_user_reauth(db=db_session, token=token))


# ===========================================================================
# TestPermissionCheckerCall
# ===========================================================================


class TestPermissionCheckerCall:
    """Test PermissionChecker.__call__() dependency injection."""

    def test_call_sets_user(self, active_user):
        """__call__ should set self.user to the provided user."""
        from core.dependencies import PermissionChecker

        request = create_mock_request(active_user)
        checker = PermissionChecker(permissions_required="events_read", request=request)
        checker(user=active_user)
        assert checker.user is active_user


class TestPermissionChecker:
    """Test PermissionChecker.has_permission() logic.

    We pass db=db_session to PermissionChecker so it uses the test
    database instead of production.
    """

    @pytest.fixture(autouse=True)
    def _inject_db(self, db_session):
        """Store db_session for use in PermissionChecker(db=...)."""
        self._db_session = db_session

    def _create_role(self, db, key, system_user):
        now = datetime.now(timezone.utc)
        role = Role(
            id=uuid.uuid4(),
            name=key,
            key=key,
            protected=False,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db.add(role)
        db.flush()
        return role

    def _create_obj_permission(
        self, db, entity_id, entity_type, object_type, object_id, perm_key, system_user
    ):
        now = datetime.now(timezone.utc)
        op = ObjectPermission(
            id=uuid.uuid4(),
            entity_id=entity_id,
            entity_type=entity_type,
            object_type=object_type,
            object_id=object_id,
            permission_key=perm_key,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db.add(op)
        db.flush()
        return op

    def test_no_required_permissions_returns_true(self, active_user):
        from core.dependencies import PermissionChecker

        request = create_mock_request(active_user)
        checker = PermissionChecker(permissions_required=None, request=request)
        assert checker.has_permission() is True

    def test_empty_list_returns_true(self, active_user):
        from core.dependencies import PermissionChecker

        request = create_mock_request(active_user)
        checker = PermissionChecker(permissions_required=[], request=request)
        assert checker.has_permission() is True

    def test_user_without_any_permission_fails(
        self, db_session, active_user, system_user
    ):
        from core.dependencies import PermissionChecker

        request = create_mock_request(active_user)
        checker = PermissionChecker(
            permissions_required="events_read",
            request=request,
            db=self._db_session,
        )
        assert checker.has_permission() is False

    def test_user_with_global_object_full_grants_all(
        self, db_session, active_user, system_user
    ):
        from core.dependencies import PermissionChecker

        # Create a global (object_id=None) object_full permission for user on events
        self._create_obj_permission(
            db_session,
            entity_id=active_user.id,
            entity_type="User",
            object_type="events",
            object_id=None,
            perm_key="object_full",
            system_user=system_user,
        )

        request = create_mock_request(active_user)
        checker = PermissionChecker(
            permissions_required="events_read",
            request=request,
            db=self._db_session,
        )
        assert checker.has_permission() is True

    def test_object_read_does_not_grant_update(
        self, db_session, active_user, system_user
    ):
        from core.dependencies import PermissionChecker

        self._create_obj_permission(
            db_session,
            entity_id=active_user.id,
            entity_type="User",
            object_type="events",
            object_id=None,
            perm_key="object_read",
            system_user=system_user,
        )

        request = create_mock_request(active_user)
        checker = PermissionChecker(
            permissions_required="events_update",
            request=request,
            db=self._db_session,
        )
        assert checker.has_permission() is False

    def test_object_delete_grants_update_and_read(
        self, db_session, active_user, system_user
    ):
        from core.dependencies import PermissionChecker

        self._create_obj_permission(
            db_session,
            entity_id=active_user.id,
            entity_type="User",
            object_type="events",
            object_id=None,
            perm_key="object_delete",
            system_user=system_user,
        )

        request = create_mock_request(active_user)

        # object_delete grants update
        checker_update = PermissionChecker(
            permissions_required="events_update",
            request=request,
            db=self._db_session,
        )
        assert checker_update.has_permission() is True

        # object_delete grants read
        checker_read = PermissionChecker(
            permissions_required="events_read",
            request=request,
            db=self._db_session,
        )
        assert checker_read.has_permission() is True

    def test_object_update_grants_read(self, db_session, active_user, system_user):
        from core.dependencies import PermissionChecker

        self._create_obj_permission(
            db_session,
            entity_id=active_user.id,
            entity_type="User",
            object_type="events",
            object_id=None,
            perm_key="object_update",
            system_user=system_user,
        )

        request = create_mock_request(active_user)
        checker = PermissionChecker(
            permissions_required="events_read",
            request=request,
            db=self._db_session,
        )
        assert checker.has_permission() is True

    def test_object_specific_permission_only_for_that_object(
        self, db_session, active_user, system_user
    ):
        from core.dependencies import PermissionChecker

        target_object_id = uuid.uuid4()
        other_object_id = uuid.uuid4()

        self._create_obj_permission(
            db_session,
            entity_id=active_user.id,
            entity_type="User",
            object_type="events",
            object_id=target_object_id,
            perm_key="object_full",
            system_user=system_user,
        )

        request = create_mock_request(active_user)

        # Has permission on target object
        checker1 = PermissionChecker(
            permissions_required="events_read",
            request=request,
            object_id=target_object_id,
            db=self._db_session,
        )
        assert checker1.has_permission() is True

        # Does NOT have permission on a different object
        checker2 = PermissionChecker(
            permissions_required="events_read",
            request=request,
            object_id=other_object_id,
            db=self._db_session,
        )
        assert checker2.has_permission() is False

    def test_role_object_permission_grants_access(
        self, db_session, active_user, system_user
    ):
        from core.dependencies import PermissionChecker

        # Use the seeded admin_full role
        role = db_session.query(Role).filter_by(key="admin_full").one()

        # Assign user to role
        db_session.execute(
            user_role_association_table.insert().values(
                user_id=active_user.id, role_id=role.id
            )
        )
        db_session.flush()

        # Create ObjectPermission for the role
        self._create_obj_permission(
            db_session,
            entity_id=role.id,
            entity_type="Role",
            object_type="events",
            object_id=None,
            perm_key="object_full",
            system_user=system_user,
        )

        request = create_mock_request(active_user)
        checker = PermissionChecker(
            permissions_required="events_read",
            request=request,
            db=self._db_session,
        )
        assert checker.has_permission() is True


# ===========================================================================
# TestDecodeAndLoadUser
# ===========================================================================


def _make_jwt(payload_overrides=None, secret="test-secret-key-for-jwt-testing-only"):
    """Create a valid JWT for testing."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(uuid.uuid4()),
        "type": "bearer",
        "aud": "test_openvle",
        "iss": "test_openvle",
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(hours=8),
    }
    if payload_overrides:
        payload.update(payload_overrides)
    return jwt.encode(payload, secret, algorithm="HS256")


class TestDecodeAndLoadUser:
    """Test _decode_and_load_user JWT validation and user loading."""

    def test_valid_token_returns_user(self, db_session, active_user, monkeypatch):
        """A valid JWT with matching user returns the User object."""
        from core.dependencies import _decode_and_load_user

        token = _make_jwt({"sub": str(active_user.id)})

        result = _decode_and_load_user(
            token, db_session, allow_policy_required=False, optional=False
        )

        assert result is not None
        assert result.id == active_user.id

    def test_invalid_format_non_optional_raises(self, db_session, system_user):
        """A token without 3 dot-separated parts raises InvalidAuthToken."""
        from core.dependencies import _decode_and_load_user
        from core.exceptions import InvalidAuthToken

        with pytest.raises(InvalidAuthToken):
            _decode_and_load_user(
                "not-a-jwt", db_session, allow_policy_required=False, optional=False
            )

    def test_invalid_format_optional_returns_false(self, db_session, system_user):
        """A malformed token with optional=True returns False."""
        from core.dependencies import _decode_and_load_user

        result = _decode_and_load_user(
            "not-a-jwt", db_session, allow_policy_required=False, optional=True
        )
        assert result is False

    def test_expired_token_non_optional_raises(self, db_session, active_user):
        """An expired JWT raises CredentialsNotValid."""
        from core.dependencies import _decode_and_load_user
        from core.exceptions import CredentialsNotValid

        expired = datetime.now(timezone.utc) - timedelta(hours=1)
        token = _make_jwt(
            {
                "sub": str(active_user.id),
                "exp": expired,
            }
        )

        with pytest.raises(CredentialsNotValid):
            _decode_and_load_user(
                token, db_session, allow_policy_required=False, optional=False
            )

    def test_expired_token_optional_returns_false(self, db_session, active_user):
        """An expired JWT with optional=True returns False."""
        from core.dependencies import _decode_and_load_user

        expired = datetime.now(timezone.utc) - timedelta(hours=1)
        token = _make_jwt(
            {
                "sub": str(active_user.id),
                "exp": expired,
            }
        )

        result = _decode_and_load_user(
            token, db_session, allow_policy_required=False, optional=True
        )
        assert result is False

    def test_policy_required_token_blocked(self, db_session, active_user):
        """A policy_required token without allow_policy_required returns exception."""
        from core.dependencies import _decode_and_load_user
        from core.exceptions import OutstandingPoliciesException

        token = _make_jwt(
            {
                "sub": str(active_user.id),
                "type": "policy_required",
            }
        )

        result = _decode_and_load_user(
            token, db_session, allow_policy_required=False, optional=False
        )

        assert isinstance(result, OutstandingPoliciesException)

    def test_policy_required_token_allowed(self, db_session, active_user):
        """A policy_required token with allow_policy_required=True succeeds."""
        from core.dependencies import _decode_and_load_user

        token = _make_jwt(
            {
                "sub": str(active_user.id),
                "type": "policy_required",
            }
        )

        result = _decode_and_load_user(
            token, db_session, allow_policy_required=True, optional=False
        )

        assert result.id == active_user.id

    def test_require_policy_required_rejects_bearer(self, db_session, active_user):
        """require_policy_required=True rejects bearer tokens."""
        from core.dependencies import _decode_and_load_user
        from core.exceptions import CredentialsNotValid

        token = _make_jwt({"sub": str(active_user.id), "type": "bearer"})

        with pytest.raises(CredentialsNotValid):
            _decode_and_load_user(
                token,
                db_session,
                allow_policy_required=True,
                require_policy_required=True,
                optional=False,
            )

    def test_require_policy_required_accepts_policy_token(
        self, db_session, active_user
    ):
        """require_policy_required=True accepts policy_required tokens."""
        from core.dependencies import _decode_and_load_user

        token = _make_jwt({"sub": str(active_user.id), "type": "policy_required"})

        result = _decode_and_load_user(
            token,
            db_session,
            allow_policy_required=True,
            require_policy_required=True,
            optional=False,
        )
        assert result.id == active_user.id

    def test_missing_sub_claim_raises(self, db_session, system_user):
        """A token with empty 'sub' claim raises CredentialsNotValid."""
        from core.dependencies import _decode_and_load_user
        from core.exceptions import CredentialsNotValid

        token = _make_jwt({"sub": ""})

        with pytest.raises(CredentialsNotValid):
            _decode_and_load_user(
                token, db_session, allow_policy_required=False, optional=False
            )

    def test_invalid_uuid_sub_raises(self, db_session, system_user):
        """A token with invalid UUID in 'sub' raises CredentialsNotValid."""
        from core.dependencies import _decode_and_load_user
        from core.exceptions import CredentialsNotValid

        token = _make_jwt({"sub": "not-a-uuid"})

        with pytest.raises(CredentialsNotValid):
            _decode_and_load_user(
                token, db_session, allow_policy_required=False, optional=False
            )

    def test_user_not_in_db_raises(self, db_session, system_user):
        """A token with valid UUID but no matching user raises CredentialsNotValid."""
        from core.dependencies import _decode_and_load_user
        from core.exceptions import CredentialsNotValid

        token = _make_jwt({"sub": str(uuid.uuid4())})

        with pytest.raises(CredentialsNotValid):
            _decode_and_load_user(
                token, db_session, allow_policy_required=False, optional=False
            )

    def test_inactive_user_raises(self, db_session, system_user):
        """A token for an inactive user raises UserNotActiveError."""
        from core.dependencies import _decode_and_load_user
        from core.exceptions import UserNotActiveError

        now = datetime.now(timezone.utc)
        inactive = User(
            id=uuid.uuid4(),
            username="inactive",
            name="Inactive User",
            email="inactive@example.com",
            hashed_password="$2b$12$dummy",
            status="Inactive",
            locale="en_US",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(inactive)
        db_session.flush()

        token = _make_jwt({"sub": str(inactive.id)})

        with pytest.raises(UserNotActiveError):
            _decode_and_load_user(
                token, db_session, allow_policy_required=False, optional=False
            )


# ===========================================================================
# TestParsePermission
# ===========================================================================
class TestParsePermission:
    """Test permission parsing via PermissionChecker.has_permission."""

    @pytest.fixture(autouse=True)
    def _inject_db(self, db_session):
        self._db_session = db_session

    def _grant(self, db_session, user, object_type, perm_key, system_user):
        now = datetime.now(timezone.utc)
        op = ObjectPermission(
            id=uuid.uuid4(),
            entity_id=user.id,
            entity_type="User",
            object_type=object_type,
            object_id=None,
            permission_key=perm_key,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(op)
        db_session.flush()

    def test_known_type_vms_actions_start(self, db_session, active_user, system_user):
        """'vms_actions_start' is parsed as type='vms'."""
        from core.dependencies import PermissionChecker

        self._grant(db_session, active_user, "vms", "object_full", system_user)

        request = create_mock_request(active_user)
        checker = PermissionChecker(
            permissions_required="vms_actions_start",
            request=request,
            db=self._db_session,
        )
        assert checker.has_permission() is True

    def test_multi_word_type_guacamole_connection_profiles(
        self, db_session, active_user, system_user
    ):
        """'guacamole_connection_profiles_read' parses with multi-word type."""
        from core.dependencies import PermissionChecker

        self._grant(
            db_session,
            active_user,
            "guacamole_connection_profiles",
            "object_read",
            system_user,
        )

        request = create_mock_request(active_user)
        checker = PermissionChecker(
            permissions_required="guacamole_connection_profiles_read",
            request=request,
            db=self._db_session,
        )
        assert checker.has_permission() is True

    def test_fallback_type_parsing(self, db_session, active_user, system_user):
        """Unknown type falls back to first part as type, rest as action."""
        from core.dependencies import PermissionChecker

        self._grant(db_session, active_user, "templates", "object_full", system_user)

        request = create_mock_request(active_user)
        checker = PermissionChecker(
            permissions_required="templates_update",
            request=request,
            db=self._db_session,
        )
        assert checker.has_permission() is True

    def test_action_stop_granted_by_delete(self, db_session, active_user, system_user):
        """'vms_stop' (maps to object_update) is granted by object_delete via hierarchy."""
        from core.dependencies import PermissionChecker

        self._grant(db_session, active_user, "vms", "object_delete", system_user)

        request = create_mock_request(active_user)
        checker = PermissionChecker(
            permissions_required="vms_stop",
            request=request,
            db=self._db_session,
        )
        assert checker.has_permission() is True


# ===========================================================================
# TestCheckPermissionHierarchy
# ===========================================================================
class TestCheckPermissionHierarchy:
    """Test permission hierarchy: full > delete > update > read."""

    @pytest.fixture(autouse=True)
    def _inject_db(self, db_session):
        self._db_session = db_session

    def _grant(self, db_session, user, object_type, perm_key, system_user):
        now = datetime.now(timezone.utc)
        op = ObjectPermission(
            id=uuid.uuid4(),
            entity_id=user.id,
            entity_type="User",
            object_type=object_type,
            object_id=None,
            permission_key=perm_key,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(op)
        db_session.flush()

    def test_object_delete_grants_read_and_update(
        self, db_session, active_user, system_user
    ):
        """object_delete should grant read and update access."""
        from core.dependencies import PermissionChecker

        self._grant(db_session, active_user, "events", "object_delete", system_user)

        request = create_mock_request(active_user)

        checker_read = PermissionChecker(
            permissions_required="events_read",
            request=request,
            db=self._db_session,
        )
        assert checker_read.has_permission() is True

        checker_update = PermissionChecker(
            permissions_required="events_update",
            request=request,
            db=self._db_session,
        )
        assert checker_update.has_permission() is True

    def test_object_update_grants_read_not_delete(
        self, db_session, active_user, system_user
    ):
        """object_update should grant read but NOT delete."""
        from core.dependencies import PermissionChecker

        self._grant(db_session, active_user, "events", "object_update", system_user)

        request = create_mock_request(active_user)

        checker_read = PermissionChecker(
            permissions_required="events_read",
            request=request,
            db=self._db_session,
        )
        assert checker_read.has_permission() is True

        checker_delete = PermissionChecker(
            permissions_required="events_delete",
            request=request,
            db=self._db_session,
        )
        assert checker_delete.has_permission() is False
