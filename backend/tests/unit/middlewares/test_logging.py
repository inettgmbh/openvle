"""Tests for middlewares/logging.py - activityLogging middleware."""

import uuid
from unittest.mock import MagicMock
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse


def _make_mock_request(
    method="GET",
    headers=None,
    url_path="/v1/test",
    user_id=None,
    query_params=None,
):
    """Create a mock request for activityLogging."""
    request = MagicMock()
    request.method = method
    req_headers = headers or {"content-type": "application/json"}
    request.headers = req_headers
    request.query_params = query_params or {}
    request.client = MagicMock()
    request.client.host = "127.0.0.1"

    mock_url = MagicMock()
    mock_url.path = url_path
    request.url = mock_url

    # body() must be async
    async def mock_body():
        return b""

    request.body = mock_body

    # request.scope needs 'type' and 'client' for Request() re-creation inside activityLogging
    raw_headers = [
        (k.lower().encode(), v.encode()) for k, v in req_headers.items()
    ]
    query_string = urlencode(query_params).encode() if query_params else b""
    request.scope = {
        "type": "http",
        "method": method,
        "path": url_path,
        "query_string": query_string,
        "headers": raw_headers,
        "client": ("127.0.0.1", 12345),
    }

    # User
    if user_id:
        request.user = MagicMock()
        request.user.id = user_id
    else:
        request.user = MagicMock()
        request.user.id = ""

    return request


def _make_call_next(status_code=200, headers=None):
    """Create a mock call_next that returns a response."""
    response = JSONResponse(content={"ok": True}, status_code=status_code)
    if headers:
        for k, v in headers.items():
            response.headers[k] = v

    async def call_next(req):
        return response

    return call_next


class TestActivityLogging:
    @pytest.mark.anyio
    async def test_logs_request_to_mongodb(self, monkeypatch):
        """Verifies collection.insert_one is called with correct structure."""
        mock_collection = MagicMock()
        monkeypatch.setattr("middlewares.logging.collection", mock_collection)
        monkeypatch.setattr(
            "middlewares.logging.settings", MagicMock(contact_name="Test")
        )

        from middlewares.logging import activityLogging

        request = _make_mock_request(method="GET", user_id="user-123")
        call_next = _make_call_next(status_code=200)

        await activityLogging(request, call_next)

        mock_collection.insert_one.assert_called_once()
        logged = mock_collection.insert_one.call_args[0][0]
        assert "timestamp" in logged
        assert logged["requestMethod"] == "GET"
        assert logged["requestUrl"] == "/v1/test"
        assert logged["responseCode"] == 200
        assert logged["requestClientIP"] == "127.0.0.1"

    @pytest.mark.anyio
    async def test_skips_options_requests(self, monkeypatch):
        """OPTIONS request returns response without insert_one call."""
        mock_collection = MagicMock()
        monkeypatch.setattr("middlewares.logging.collection", mock_collection)
        monkeypatch.setattr(
            "middlewares.logging.settings", MagicMock(contact_name="Test")
        )

        from middlewares.logging import activityLogging

        request = _make_mock_request(method="OPTIONS")
        call_next = _make_call_next()

        response = await activityLogging(request, call_next)

        assert response is not None
        mock_collection.insert_one.assert_not_called()

    @pytest.mark.anyio
    async def test_strips_authorization_header(self, monkeypatch):
        """Authorization header is removed from logged data."""
        mock_collection = MagicMock()
        monkeypatch.setattr("middlewares.logging.collection", mock_collection)
        monkeypatch.setattr(
            "middlewares.logging.settings", MagicMock(contact_name="Test")
        )

        from middlewares.logging import activityLogging

        request = _make_mock_request(
            headers={
                "content-type": "application/json",
                "Authorization": "Bearer secret-token",
            }
        )
        call_next = _make_call_next()

        await activityLogging(request, call_next)

        logged = mock_collection.insert_one.call_args[0][0]
        assert "Authorization" not in logged["requestHeaders"]

    @pytest.mark.anyio
    async def test_strips_cookie_header(self, monkeypatch):
        """cookie header is removed from logged data."""
        mock_collection = MagicMock()
        monkeypatch.setattr("middlewares.logging.collection", mock_collection)
        monkeypatch.setattr(
            "middlewares.logging.settings", MagicMock(contact_name="Test")
        )

        from middlewares.logging import activityLogging

        request = _make_mock_request(
            headers={
                "content-type": "application/json",
                "cookie": "session=abc123",
            }
        )
        call_next = _make_call_next()

        await activityLogging(request, call_next)

        logged = mock_collection.insert_one.call_args[0][0]
        assert "cookie" not in logged["requestHeaders"]

    @pytest.mark.anyio
    async def test_adds_process_time_header(self, monkeypatch):
        """X-Process-Time header is added to response."""
        mock_collection = MagicMock()
        monkeypatch.setattr("middlewares.logging.collection", mock_collection)
        monkeypatch.setattr(
            "middlewares.logging.settings", MagicMock(contact_name="Test")
        )

        from middlewares.logging import activityLogging

        request = _make_mock_request()
        call_next = _make_call_next()

        response = await activityLogging(request, call_next)

        assert "x-process-time" in response.headers

    @pytest.mark.anyio
    async def test_handles_http_exception(self, monkeypatch):
        """HTTPException from call_next logs the error status code."""
        mock_collection = MagicMock()
        monkeypatch.setattr("middlewares.logging.collection", mock_collection)
        monkeypatch.setattr(
            "middlewares.logging.settings", MagicMock(contact_name="Test")
        )

        from middlewares.logging import activityLogging

        request = _make_mock_request()

        async def call_next_raises(req):
            raise HTTPException(status_code=403, detail="Forbidden")

        response = await activityLogging(request, call_next_raises)

        assert response.status_code == 403
        logged = mock_collection.insert_one.call_args[0][0]
        assert logged["responseCode"] == 403

    @pytest.mark.anyio
    async def test_handles_generic_exception(self, monkeypatch):
        """Generic Exception from call_next returns 500 response."""
        mock_collection = MagicMock()
        monkeypatch.setattr("middlewares.logging.collection", mock_collection)
        monkeypatch.setattr(
            "middlewares.logging.settings", MagicMock(contact_name="Test")
        )

        from middlewares.logging import activityLogging

        request = _make_mock_request()

        async def call_next_raises(req):
            raise RuntimeError("unexpected crash")

        response = await activityLogging(request, call_next_raises)

        assert response.status_code == 500
        logged = mock_collection.insert_one.call_args[0][0]
        assert logged["responseCode"] == 500


class TestLoginPathLogging:
    """Tests for login-specific username extraction in activityLogging."""

    @pytest.mark.anyio
    async def test_login_json_body_extracts_username(self, monkeypatch):
        """Login path with JSON body extracts username into log data."""
        import json

        mock_collection = MagicMock()
        monkeypatch.setattr("middlewares.logging.collection", mock_collection)
        monkeypatch.setattr(
            "middlewares.logging.settings", MagicMock(contact_name="Test")
        )
        # Mock SessionLocal to avoid DB calls
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        monkeypatch.setattr(
            "middlewares.logging.SessionLocal", lambda: mock_session
        )

        from middlewares.logging import activityLogging

        body = json.dumps(
            {"username": "testuser", "password": "secret"}
        ).encode()
        request = _make_mock_request(
            method="POST",
            url_path="/v1/auth/login",
            headers={"content-type": "application/json"},
        )

        # Override body() to return login JSON
        async def mock_body():
            return body

        request.body = mock_body
        request.scope["path"] = "/v1/auth/login"

        call_next = _make_call_next(status_code=401)
        await activityLogging(request, call_next)

        logged = mock_collection.insert_one.call_args[0][0]
        assert logged["requestUser"]["username"] == "testuser"

    @pytest.mark.anyio
    async def test_login_form_body_extracts_username(self, monkeypatch):
        """Login path with form-urlencoded body extracts username."""
        mock_collection = MagicMock()
        monkeypatch.setattr("middlewares.logging.collection", mock_collection)
        monkeypatch.setattr(
            "middlewares.logging.settings", MagicMock(contact_name="Test")
        )
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        monkeypatch.setattr(
            "middlewares.logging.SessionLocal", lambda: mock_session
        )

        from middlewares.logging import activityLogging

        body = b"username=formuser&password=secret"
        request = _make_mock_request(
            method="POST",
            url_path="/v1/auth/login",
            headers={"content-type": "application/x-www-form-urlencoded"},
        )

        async def mock_body():
            return body

        request.body = mock_body
        request.scope["path"] = "/v1/auth/login"

        call_next = _make_call_next(status_code=401)
        await activityLogging(request, call_next)

        logged = mock_collection.insert_one.call_args[0][0]
        assert logged["requestUser"]["username"] == "formuser"

    @pytest.mark.anyio
    async def test_login_success_looks_up_user_id(self, monkeypatch):
        """On successful login (200), user ID is looked up from the database."""
        import json

        mock_collection = MagicMock()
        monkeypatch.setattr("middlewares.logging.collection", mock_collection)
        monkeypatch.setattr(
            "middlewares.logging.settings", MagicMock(contact_name="Test")
        )

        # Mock SessionLocal to return a mock user
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user
        monkeypatch.setattr(
            "middlewares.logging.SessionLocal", lambda: mock_session
        )

        from middlewares.logging import activityLogging

        body = json.dumps(
            {"username": "loginuser", "password": "pass"}
        ).encode()
        request = _make_mock_request(
            method="POST",
            url_path="/v1/auth/login",
            headers={"content-type": "application/json"},
        )

        async def mock_body():
            return body

        request.body = mock_body
        request.scope["path"] = "/v1/auth/login"

        call_next = _make_call_next(status_code=200)
        await activityLogging(request, call_next)

        logged = mock_collection.insert_one.call_args[0][0]
        assert logged["requestUser"]["id"] == str(mock_user.id)


class TestOidcParameterStripping:
    """Sensitive OIDC query params must never be persisted."""

    @pytest.mark.anyio
    async def test_strips_oidc_params_from_callback(self, monkeypatch):
        """code, state, and id_token are removed from logged params."""
        mock_collection = MagicMock()
        monkeypatch.setattr("middlewares.logging.collection", mock_collection)
        monkeypatch.setattr(
            "middlewares.logging.settings", MagicMock(contact_name="Test")
        )

        from middlewares.logging import activityLogging

        request = _make_mock_request(
            method="GET",
            url_path="/v1/auth/oidc/callback",
            query_params={
                "code": "secret-auth-code",
                "state": "csrf-state-value",
                "id_token": "eyJhbGciOi.jwt.token",
            },
        )
        call_next = _make_call_next(status_code=200)

        await activityLogging(request, call_next)

        logged = mock_collection.insert_one.call_args[0][0]
        assert "code" not in logged["requestParameter"]
        assert "state" not in logged["requestParameter"]
        assert "id_token" not in logged["requestParameter"]

    @pytest.mark.anyio
    async def test_preserves_non_sensitive_params(self, monkeypatch):
        """Non-sensitive query params are still logged."""
        mock_collection = MagicMock()
        monkeypatch.setattr("middlewares.logging.collection", mock_collection)
        monkeypatch.setattr(
            "middlewares.logging.settings", MagicMock(contact_name="Test")
        )

        from middlewares.logging import activityLogging

        request = _make_mock_request(
            method="GET",
            url_path="/v1/users/",
            query_params={"page": "1", "limit": "10"},
        )
        call_next = _make_call_next(status_code=200)

        await activityLogging(request, call_next)

        logged = mock_collection.insert_one.call_args[0][0]
        assert logged["requestParameter"]["page"] == "1"
        assert logged["requestParameter"]["limit"] == "10"

    @pytest.mark.anyio
    async def test_strips_query_params_from_location_header(self, monkeypatch):
        """Location header keeps base URL but query params with JWT are stripped."""
        mock_collection = MagicMock()
        monkeypatch.setattr("middlewares.logging.collection", mock_collection)
        monkeypatch.setattr(
            "middlewares.logging.settings", MagicMock(contact_name="Test")
        )

        from middlewares.logging import activityLogging

        request = _make_mock_request(
            method="GET",
            url_path="/v1/auth/oidc/callback",
            query_params={"code": "auth-code", "state": "csrf"},
        )
        redirect_url = (
            "https://frontend.example.com/callback"
            "?access_token=eyJhbGciOi.jwt.secret&token_type=bearer"
        )
        call_next = _make_call_next(
            status_code=302,
            headers={"location": redirect_url},
        )

        await activityLogging(request, call_next)

        logged = mock_collection.insert_one.call_args[0][0]
        location = logged["responseHeaders"]["location"]
        assert location == "https://frontend.example.com/callback"
        assert "access_token" not in location
        assert "jwt" not in location
