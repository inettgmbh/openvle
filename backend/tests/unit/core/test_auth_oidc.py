"""Tests for core/auth_oidc.py - OIDC authentication and callback handling."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.exceptions import (
    CSRFMismatch,
    IncorrectCredentials,
    InvalidRedirectURL,
    SystemUserLoginException,
    UserNotActiveError,
)
from models import User


# Restrict anyio to asyncio backend only (trio is not installed)
@pytest.fixture(params=["asyncio"])
def anyio_backend(request):
    return request.param


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_user_info(username="oidcuser", name="OIDC User", email="oidc@example.com"):
    """Build a fake OIDC userinfo dict using default attribute names."""
    return {
        "sub": username,
        "name": name,
        "email": email,
    }


def _make_oidc_settings(**overrides):
    """Create a mock settings object for OIDC tests."""
    s = MagicMock()
    s.app_env = overrides.get("app_env", "prod")
    s.oidc_attr_username = "sub"
    s.oidc_attr_name = "name"
    s.oidc_attr_email = "email"
    s.oidc_enroll_users = overrides.get("oidc_enroll_users", True)
    s.oidc_allowed_redirect_urls = overrides.get("oidc_allowed_redirect_urls", [])
    s.project_name = "test_openvle"
    s.auth_secret = "test-secret-key-for-jwt-testing-only"
    s.auth_algorithm = "HS256"
    s.auth_access_token_expire_minutes = 480
    return s


class MockSession(dict):
    """A dict subclass that allows .pop() to work normally (unlike MagicMock overrides)."""

    pass


# ---------------------------------------------------------------------------
# Tests: authenticate_oidc
# ---------------------------------------------------------------------------
class TestAuthenticateOidc:
    def test_authenticate_existing_user(
        self, db_session, system_user, active_user, monkeypatch
    ):
        """Existing user returns a token response."""
        mock_settings = _make_oidc_settings()
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        user_info = _make_user_info(
            username=active_user.username,
            name=active_user.name,
            email=active_user.email,
        )

        # Mock create_access_token to return a simple string
        monkeypatch.setattr(
            "core.auth_oidc.create_access_token",
            lambda user, type: "mock-jwt-token",
        )
        # Mock CRUDPolicy to return no outstanding policies
        from controllers.policies import CRUDPolicy

        monkeypatch.setattr(CRUDPolicy, "get_outstanding", lambda self, db, user_id: [])

        from core.auth_oidc import authenticate_oidc

        result = authenticate_oidc(user_in=user_info, db=db_session)

        assert result["token_type"] == "bearer"
        assert result["access_token"] == "mock-jwt-token"
        assert result["outstanding_policies"] is None

    def test_authenticate_new_user_enrollment(
        self, db_session, system_user, monkeypatch
    ):
        """Non-existent user with enrollment enabled creates user and returns token."""
        mock_settings = _make_oidc_settings(oidc_enroll_users=True)
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        user_info = _make_user_info(
            username="newoidcuser", name="New OIDC User", email="newoidc@example.com"
        )

        monkeypatch.setattr(
            "core.auth_oidc.create_access_token",
            lambda user, type: "mock-jwt-token",
        )
        from controllers.policies import CRUDPolicy

        monkeypatch.setattr(CRUDPolicy, "get_outstanding", lambda self, db, user_id: [])

        from core.auth_oidc import authenticate_oidc

        result = authenticate_oidc(user_in=user_info, db=db_session)

        assert result["access_token"] == "mock-jwt-token"
        # Verify user was created in DB
        created = db_session.query(User).filter(User.username == "newoidcuser").first()
        assert created is not None
        assert created.email == "newoidc@example.com"

    def test_authenticate_enrollment_disabled(
        self, db_session, system_user, monkeypatch
    ):
        """Non-existent user with enrollment disabled raises IncorrectCredentials."""
        mock_settings = _make_oidc_settings(oidc_enroll_users=False)
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        user_info = _make_user_info(username="nobody")

        from core.auth_oidc import authenticate_oidc

        with pytest.raises(IncorrectCredentials):
            authenticate_oidc(user_in=user_info, db=db_session)

    def test_authenticate_syncs_name_email(
        self, db_session, system_user, active_user, monkeypatch
    ):
        """When OIDC data differs from DB, user is updated."""
        mock_settings = _make_oidc_settings()
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        # Patch get_system_user which calls SessionLocal() when no db is passed
        monkeypatch.setattr(
            "core.auth_oidc.get_system_user",
            lambda db=None: system_user,
        )

        user_info = _make_user_info(
            username=active_user.username,
            name="Updated Name",
            email="updated@example.com",
        )

        monkeypatch.setattr(
            "core.auth_oidc.create_access_token",
            lambda user, type: "mock-jwt-token",
        )
        from controllers.policies import CRUDPolicy

        monkeypatch.setattr(CRUDPolicy, "get_outstanding", lambda self, db, user_id: [])

        from core.auth_oidc import authenticate_oidc

        authenticate_oidc(user_in=user_info, db=db_session)

        db_session.expire_all()
        refreshed = db_session.get(User, active_user.id)
        assert refreshed.name == "Updated Name"
        assert refreshed.email == "updated@example.com"

    def test_authenticate_inactive_user(self, db_session, system_user, monkeypatch):
        """Inactive user raises UserNotActiveError."""
        mock_settings = _make_oidc_settings()
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        now = datetime.now(timezone.utc)
        inactive = User(
            id=uuid.uuid4(),
            username="inactiveoidc",
            name="Inactive OIDC",
            email="inactive_oidc@example.com",
            status="Deactivated",
            locale="de_DE",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(inactive)
        db_session.flush()

        user_info = _make_user_info(
            username="inactiveoidc",
            name="Inactive OIDC",
            email="inactive_oidc@example.com",
        )

        from core.auth_oidc import authenticate_oidc

        with pytest.raises(UserNotActiveError):
            authenticate_oidc(user_in=user_info, db=db_session)

    def test_authenticate_system_user_blocked_in_prod(
        self, db_session, system_user, monkeypatch
    ):
        """Login as 'system' in production raises SystemUserLoginException."""
        mock_settings = _make_oidc_settings(app_env="prod")
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        user_info = _make_user_info(username="system")

        from core.auth_oidc import authenticate_oidc

        with pytest.raises(SystemUserLoginException):
            authenticate_oidc(user_in=user_info, db=db_session)

    def test_authenticate_outstanding_policies(
        self, db_session, system_user, active_user, monkeypatch
    ):
        """Outstanding policies result in token_type='policy_required'."""
        mock_settings = _make_oidc_settings()
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        user_info = _make_user_info(
            username=active_user.username,
            name=active_user.name,
            email=active_user.email,
        )

        captured_type = {}

        def mock_create_token(user, type):
            captured_type["type"] = type
            return "mock-policy-token"

        monkeypatch.setattr("core.auth_oidc.create_access_token", mock_create_token)

        # Return some outstanding policies
        from controllers.policies import CRUDPolicy

        monkeypatch.setattr(
            CRUDPolicy,
            "get_outstanding",
            lambda self, db, user_id: [{"id": str(uuid.uuid4()), "name": "TOS"}],
        )

        from core.auth_oidc import authenticate_oidc

        result = authenticate_oidc(user_in=user_info, db=db_session)

        assert captured_type["type"] == "policy_required"
        assert "outstanding_policies" in result


# ---------------------------------------------------------------------------
# Tests: handle_oidc_login (async)
# ---------------------------------------------------------------------------
class TestHandleOidcLogin:
    @pytest.mark.anyio
    async def test_handle_oidc_login_valid_redirect(self, monkeypatch):
        """Valid redirect URL calls authorize_redirect."""
        mock_settings = _make_oidc_settings(
            oidc_allowed_redirect_urls=["https://app.example.com/callback"]
        )
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        mock_request = MagicMock()
        mock_request.query_params = {"redirect": "https://app.example.com/callback"}
        mock_request.session = MockSession()
        mock_request.url_for.return_value = (
            "https://api.example.com/v1/auth/oidc/callback"
        )

        mock_oauth = MagicMock()
        mock_oauth.oidc00.authorize_redirect = AsyncMock(
            return_value="redirect_response"
        )
        monkeypatch.setattr("core.auth_oidc.oauth", mock_oauth)

        from core.auth_oidc import handle_oidc_login

        result = await handle_oidc_login(mock_request)

        assert result == "redirect_response"
        mock_oauth.oidc00.authorize_redirect.assert_awaited_once()

    @pytest.mark.anyio
    async def test_handle_oidc_login_invalid_redirect(self, monkeypatch):
        """Invalid redirect URL raises InvalidRedirectURL."""
        mock_settings = _make_oidc_settings(oidc_allowed_redirect_urls=[])
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        mock_request = MagicMock()
        mock_request.query_params = {"redirect": "not-a-url"}
        mock_request.session = MockSession()

        from core.auth_oidc import handle_oidc_login

        with pytest.raises(InvalidRedirectURL):
            await handle_oidc_login(mock_request)

    @pytest.mark.anyio
    async def test_handle_oidc_login_no_redirect(self, monkeypatch):
        """redirect=None is always allowed."""
        mock_settings = _make_oidc_settings(oidc_allowed_redirect_urls=[])
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        # Use a real dict-like object for query_params so .get() returns None for missing keys
        mock_request = MagicMock()
        mock_request.query_params = {}  # No "redirect" key -> .get("redirect", None) returns None
        mock_request.session = MockSession()
        mock_request.url_for.return_value = (
            "https://api.example.com/v1/auth/oidc/callback"
        )

        mock_oauth = MagicMock()
        mock_oauth.oidc00.authorize_redirect = AsyncMock(
            return_value="redirect_response"
        )
        monkeypatch.setattr("core.auth_oidc.oauth", mock_oauth)

        from core.auth_oidc import handle_oidc_login

        result = await handle_oidc_login(mock_request)
        assert result == "redirect_response"


# ---------------------------------------------------------------------------
# Tests: handle_oidc_callback (async)
# ---------------------------------------------------------------------------
class TestHandleOidcCallback:
    @pytest.mark.anyio
    async def test_callback_success_no_redirect(
        self, db_session, system_user, active_user, monkeypatch
    ):
        """Successful callback without redirect returns payload dict."""
        mock_settings = _make_oidc_settings()
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        mock_request = MagicMock()
        mock_request.session = MockSession({"oidc00_post_auth_redirect": None})

        token_data = {
            "userinfo": _make_user_info(
                username=active_user.username,
                name=active_user.name,
                email=active_user.email,
            )
        }
        mock_oauth = MagicMock()
        mock_oauth.oidc00.authorize_access_token = AsyncMock(return_value=token_data)
        monkeypatch.setattr("core.auth_oidc.oauth", mock_oauth)

        monkeypatch.setattr(
            "core.auth_oidc.create_access_token",
            lambda user, type: "mock-jwt-token",
        )
        from controllers.policies import CRUDPolicy

        monkeypatch.setattr(CRUDPolicy, "get_outstanding", lambda self, db, user_id: [])

        from core.auth_oidc import handle_oidc_callback

        result = await handle_oidc_callback(mock_request, db_session)

        assert isinstance(result, dict)
        assert result["access_token"] == "mock-jwt-token"
        assert result["token_type"] == "bearer"
        assert result["outstanding_policies"] is None

    @pytest.mark.anyio
    async def test_callback_success_with_redirect(
        self, db_session, system_user, active_user, monkeypatch
    ):
        """Successful callback with redirect returns RedirectResponse."""
        from fastapi.responses import RedirectResponse

        redirect_url = "https://app.example.com/callback"
        mock_settings = _make_oidc_settings(oidc_allowed_redirect_urls=[redirect_url])
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        mock_request = MagicMock()
        mock_request.session = MockSession({"oidc00_post_auth_redirect": redirect_url})

        token_data = {
            "userinfo": _make_user_info(
                username=active_user.username,
                name=active_user.name,
                email=active_user.email,
            )
        }
        mock_oauth = MagicMock()
        mock_oauth.oidc00.authorize_access_token = AsyncMock(return_value=token_data)
        monkeypatch.setattr("core.auth_oidc.oauth", mock_oauth)

        monkeypatch.setattr(
            "core.auth_oidc.create_access_token",
            lambda user, type: "mock-jwt-token",
        )
        from controllers.policies import CRUDPolicy

        monkeypatch.setattr(CRUDPolicy, "get_outstanding", lambda self, db, user_id: [])

        from core.auth_oidc import handle_oidc_callback

        result = await handle_oidc_callback(mock_request, db_session)

        assert isinstance(result, RedirectResponse)
        assert result.status_code == 302

    @pytest.mark.anyio
    async def test_callback_csrf_mismatch_no_redirect(self, monkeypatch):
        """Token auth fails without redirect -> raises CSRFMismatch."""
        mock_settings = _make_oidc_settings()
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        mock_request = MagicMock()
        mock_request.session = MockSession({"oidc00_post_auth_redirect": None})

        mock_oauth = MagicMock()
        mock_oauth.oidc00.authorize_access_token = AsyncMock(
            side_effect=Exception("CSRF mismatch")
        )
        monkeypatch.setattr("core.auth_oidc.oauth", mock_oauth)

        from core.auth_oidc import handle_oidc_callback

        with pytest.raises(CSRFMismatch):
            await handle_oidc_callback(mock_request, MagicMock())

    @pytest.mark.anyio
    async def test_callback_inactive_user_no_redirect(
        self, db_session, system_user, monkeypatch
    ):
        """Inactive user without redirect raises UserNotActiveError."""
        mock_settings = _make_oidc_settings()
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        now = datetime.now(timezone.utc)
        inactive = User(
            id=uuid.uuid4(),
            username="inactiveoidc_cb",
            name="Inactive OIDC CB",
            email="inactive_oidc_cb@example.com",
            status="Deactivated",
            locale="de_DE",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(inactive)
        db_session.flush()

        mock_request = MagicMock()
        mock_request.session = MockSession({"oidc00_post_auth_redirect": None})

        token_data = {
            "userinfo": _make_user_info(
                username="inactiveoidc_cb",
                name="Inactive OIDC CB",
                email="inactive_oidc_cb@example.com",
            )
        }
        mock_oauth = MagicMock()
        mock_oauth.oidc00.authorize_access_token = AsyncMock(return_value=token_data)
        monkeypatch.setattr("core.auth_oidc.oauth", mock_oauth)

        from core.auth_oidc import handle_oidc_callback

        with pytest.raises(UserNotActiveError):
            await handle_oidc_callback(mock_request, db_session)

    @pytest.mark.anyio
    async def test_callback_inactive_user_with_redirect(
        self, db_session, system_user, monkeypatch
    ):
        """Inactive user with redirect returns RedirectResponse with error param."""
        from fastapi.responses import RedirectResponse

        redirect_url = "https://app.example.com/callback"
        mock_settings = _make_oidc_settings(oidc_allowed_redirect_urls=[redirect_url])
        monkeypatch.setattr("core.auth_oidc.settings", mock_settings)

        now = datetime.now(timezone.utc)
        inactive = User(
            id=uuid.uuid4(),
            username="inactiveoidc_redir",
            name="Inactive OIDC Redir",
            email="inactive_oidc_redir@example.com",
            status="Deactivated",
            locale="de_DE",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(inactive)
        db_session.flush()

        mock_request = MagicMock()
        mock_request.session = MockSession({"oidc00_post_auth_redirect": redirect_url})

        token_data = {
            "userinfo": _make_user_info(
                username="inactiveoidc_redir",
                name="Inactive OIDC Redir",
                email="inactive_oidc_redir@example.com",
            )
        }
        mock_oauth = MagicMock()
        mock_oauth.oidc00.authorize_access_token = AsyncMock(return_value=token_data)
        monkeypatch.setattr("core.auth_oidc.oauth", mock_oauth)

        from core.auth_oidc import handle_oidc_callback

        result = await handle_oidc_callback(mock_request, db_session)

        assert isinstance(result, RedirectResponse)
        assert result.status_code == 302
        assert "error=user_not_active" in result.headers["location"]
