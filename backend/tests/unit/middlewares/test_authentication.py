"""Tests for middlewares/authentication.py - AuthBackend and SimpleUser."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from jose import jwt

from core.config import Settings

settings = Settings()


class TestSimpleUser:
    def test_simple_user_properties(self):
        """SimpleUser has is_authenticated=True and display_name=username."""
        from middlewares.authentication import SimpleUser

        user = SimpleUser(username="alice", id="some-id", locale="de_DE")
        assert user.is_authenticated is True
        assert user.display_name == "alice"
        assert user.locale == "de_DE"

    def test_simple_user_uuid_conversion(self):
        """String UUID is converted to uuid.UUID."""
        from middlewares.authentication import SimpleUser

        test_uuid = str(uuid.uuid4())
        user = SimpleUser(username="bob", id=test_uuid)
        assert isinstance(user.id, uuid.UUID)
        assert str(user.id) == test_uuid

    def test_simple_user_non_uuid_id(self):
        """Non-UUID string id stays as-is (no crash)."""
        from middlewares.authentication import SimpleUser

        user = SimpleUser(username="", id="")
        # Empty string cannot be converted to UUID, so it stays as-is
        assert user.id == ""


def _make_jwt_token(
    sub=None, exp_delta_minutes=480, audience=None, issuer=None, extra=None
):
    """Helper to create a JWT token for testing."""
    now = datetime.now(timezone.utc)
    payload = {
        "type": "bearer",
        "exp": now + timedelta(minutes=exp_delta_minutes),
        "iat": now,
        "nbf": now,
        "sub": sub or str(uuid.uuid4()),
        "aud": audience or settings.project_name,
        "iss": issuer or settings.project_name,
        "user": {"username": "testuser", "email": "test@example.com", "name": "Test"},
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.auth_secret, algorithm=settings.auth_algorithm)


def _make_mock_request(headers=None, url_path="/v1/test"):
    """Helper to create a mock request for AuthBackend.authenticate."""
    request = MagicMock()
    request.headers = headers or {}
    mock_url = MagicMock()
    mock_url.__str__ = lambda self: f"http://localhost{url_path}"
    request.url = mock_url
    return request


class TestAuthBackendAuthenticate:
    @pytest.mark.anyio
    async def test_no_auth_header(self, monkeypatch):
        """Request without Authorization header returns unauthenticated user."""
        monkeypatch.setattr(
            "middlewares.authentication.SessionLocal", lambda: MagicMock()
        )

        from middlewares.authentication import AuthBackend

        backend = AuthBackend()
        request = _make_mock_request(headers={})

        credentials, user = await backend.authenticate(request)
        assert "unauthenticated" in credentials.scopes
        assert user.username == ""

    @pytest.mark.anyio
    async def test_basic_auth_header(self, monkeypatch):
        """Request with Basic auth header returns unauthenticated user."""
        monkeypatch.setattr(
            "middlewares.authentication.SessionLocal", lambda: MagicMock()
        )

        from middlewares.authentication import AuthBackend

        backend = AuthBackend()
        request = _make_mock_request(headers={"Authorization": "Basic dXNlcjpwYXNz"})

        credentials, user = await backend.authenticate(request)
        assert "unauthenticated" in credentials.scopes

    @pytest.mark.anyio
    async def test_valid_jwt_returns_authenticated_user(
        self, monkeypatch, db_session, active_user
    ):
        """Valid JWT returns authenticated user with correct id."""
        monkeypatch.setattr(
            "middlewares.authentication.SessionLocal", lambda: db_session
        )

        from middlewares.authentication import AuthBackend

        backend = AuthBackend()
        token = _make_jwt_token(sub=str(active_user.id))
        request = _make_mock_request(headers={"Authorization": f"Bearer {token}"})

        credentials, user = await backend.authenticate(request)
        assert "authenticated" in credentials.scopes
        assert user.id == active_user.id
        assert user.username == active_user.username

    @pytest.mark.anyio
    async def test_invalid_jwt_returns_unauthenticated(self, monkeypatch):
        """Invalid/expired JWT returns unauthenticated user."""
        monkeypatch.setattr(
            "middlewares.authentication.SessionLocal", lambda: MagicMock()
        )

        from middlewares.authentication import AuthBackend

        backend = AuthBackend()
        # Token with wrong secret
        bad_token = jwt.encode(
            {
                "sub": str(uuid.uuid4()),
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
                "iat": datetime.now(timezone.utc),
                "nbf": datetime.now(timezone.utc),
                "aud": settings.project_name,
                "iss": settings.project_name,
            },
            "wrong-secret",
            algorithm="HS256",
        )
        request = _make_mock_request(headers={"Authorization": f"Bearer {bad_token}"})

        credentials, user = await backend.authenticate(request)
        assert "unauthenticated" in credentials.scopes

    @pytest.mark.anyio
    async def test_user_not_found_returns_unauthenticated(
        self, monkeypatch, db_session, system_user
    ):
        """JWT valid but user not in DB returns unauthenticated."""
        monkeypatch.setattr(
            "middlewares.authentication.SessionLocal", lambda: db_session
        )

        from middlewares.authentication import AuthBackend

        backend = AuthBackend()
        # Use a UUID that doesn't exist in DB
        nonexistent_id = str(uuid.uuid4())
        token = _make_jwt_token(sub=nonexistent_id)
        request = _make_mock_request(headers={"Authorization": f"Bearer {token}"})

        credentials, user = await backend.authenticate(request)
        assert "unauthenticated" in credentials.scopes

    @pytest.mark.anyio
    async def test_inactive_user_returns_unauthenticated(
        self, monkeypatch, db_session, active_user
    ):
        """User found but status != 'Active' returns unauthenticated."""
        active_user.status = "Inactive"
        db_session.flush()

        monkeypatch.setattr(
            "middlewares.authentication.SessionLocal", lambda: db_session
        )

        from middlewares.authentication import AuthBackend

        backend = AuthBackend()
        token = _make_jwt_token(sub=str(active_user.id))
        request = _make_mock_request(headers={"Authorization": f"Bearer {token}"})

        credentials, user = await backend.authenticate(request)
        assert "unauthenticated" in credentials.scopes

    @pytest.mark.anyio
    async def test_login_endpoint_returns_unauthenticated(self, monkeypatch):
        """Login URL is detected and auth is skipped."""
        monkeypatch.setattr(
            "middlewares.authentication.SessionLocal", lambda: MagicMock()
        )

        from middlewares.authentication import AuthBackend

        backend = AuthBackend()
        # The code checks if url ends with /v{version[0]}/auth/login
        # project_version is "0.99" so version[0] is "0"
        request = _make_mock_request(
            headers={"Authorization": "Bearer sometoken"},
            url_path="/v0/auth/login",
        )

        credentials, user = await backend.authenticate(request)
        assert "unauthenticated" in credentials.scopes

    @pytest.mark.anyio
    async def test_missing_sub_claim(self, monkeypatch):
        """JWT without sub claim returns unauthenticated."""
        monkeypatch.setattr(
            "middlewares.authentication.SessionLocal", lambda: MagicMock()
        )

        from middlewares.authentication import AuthBackend

        backend = AuthBackend()
        # Encode a token WITHOUT required claims -> JWTError
        now = datetime.now(timezone.utc)
        token = jwt.encode(
            {
                "exp": now + timedelta(hours=1),
                "iat": now,
                "nbf": now,
                "aud": settings.project_name,
                "iss": settings.project_name,
                # no "sub" claim
            },
            settings.auth_secret,
            algorithm=settings.auth_algorithm,
        )
        request = _make_mock_request(headers={"Authorization": f"Bearer {token}"})

        credentials, user = await backend.authenticate(request)
        # The JWT options require_sub=True, so JWTError is raised and caught
        assert "unauthenticated" in credentials.scopes
