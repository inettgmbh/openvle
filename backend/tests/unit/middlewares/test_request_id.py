"""Tests for middlewares/request_id.py - request_id_middleware."""

import re
import uuid

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse, Response
from middlewares.request_id import request_id_middleware

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _make_request() -> Request:
    """Create a minimal real Starlette Request with a fresh state."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/v1/test",
        "headers": [],
        "query_string": b"",
        "state": {},
    }
    return Request(scope)


def _call_next_factory(observed: dict, status_code: int = 200):
    """Build a call_next that records the request_id seen on request.state
    and returns a JSONResponse."""

    async def call_next(request: Request) -> Response:
        observed["request_id"] = getattr(request.state, "request_id", None)
        return JSONResponse({"ok": True}, status_code=status_code)

    return call_next


class TestRequestIdMiddleware:
    @pytest.mark.anyio
    async def test_sets_request_id_on_state(self):
        """request.state.request_id is populated before call_next runs."""
        request = _make_request()
        observed = {}

        await request_id_middleware(request, _call_next_factory(observed))

        assert observed["request_id"] is not None
        assert UUID_RE.match(observed["request_id"])

    @pytest.mark.anyio
    async def test_sets_response_header(self):
        """Response carries X-Request-Id matching state value."""
        request = _make_request()
        observed = {}

        response = await request_id_middleware(
            request, _call_next_factory(observed)
        )

        assert response.headers["X-Request-Id"] == observed["request_id"]
        assert UUID_RE.match(response.headers["X-Request-Id"])

    @pytest.mark.anyio
    async def test_each_request_gets_unique_id(self):
        """Two independent requests produce different IDs."""
        ids = set()
        for _ in range(5):
            request = _make_request()
            observed = {}
            response = await request_id_middleware(
                request, _call_next_factory(observed)
            )
            ids.add(response.headers["X-Request-Id"])

        assert len(ids) == 5

    @pytest.mark.anyio
    async def test_generated_id_is_valid_uuid4(self):
        """Generated value parses as a UUID4."""
        request = _make_request()
        observed = {}

        response = await request_id_middleware(
            request, _call_next_factory(observed)
        )

        parsed = uuid.UUID(response.headers["X-Request-Id"])
        assert parsed.version == 4

    @pytest.mark.anyio
    async def test_tags_sentry_scope(self, monkeypatch):
        """sentry_sdk.set_tag is called with the generated request_id."""
        captured = {}

        def fake_set_tag(key, value):
            captured[key] = value

        monkeypatch.setattr(
            "middlewares.request_id.sentry_sdk.set_tag", fake_set_tag
        )

        request = _make_request()
        observed = {}

        await request_id_middleware(request, _call_next_factory(observed))

        assert "request_id" in captured
        assert captured["request_id"] == observed["request_id"]

    @pytest.mark.anyio
    async def test_header_set_even_when_call_next_returns_error_response(self):
        """Header is attached regardless of response status code."""
        request = _make_request()
        observed = {}

        response = await request_id_middleware(
            request, _call_next_factory(observed, status_code=500)
        )

        assert response.status_code == 500
        assert UUID_RE.match(response.headers["X-Request-Id"])

    @pytest.mark.anyio
    async def test_state_id_matches_response_header(self):
        """The value on request.state and the response header are identical."""
        request = _make_request()
        observed = {}

        response = await request_id_middleware(
            request, _call_next_factory(observed)
        )

        assert response.headers["X-Request-Id"] == observed["request_id"]
        assert request.state.request_id == observed["request_id"]
