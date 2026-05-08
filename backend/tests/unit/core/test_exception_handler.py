"""Tests for core/exception_handler.py - central HTTP/SQLAlchemy handlers."""

import json

import pytest
from fastapi import HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.exception_handler import (
    http_exception_handler,
    sqlalchemy_exception_handler,
)


def _make_request(state: dict | None = None) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/v1/test",
        "headers": [],
        "query_string": b"",
        "state": state or {},
    }
    return Request(scope)


def _body_json(response):
    return json.loads(response.body.decode())


class TestHttpExceptionHandler:
    @pytest.mark.anyio
    async def test_basic_error_response(self):
        request = _make_request()
        exc = HTTPException(status_code=500, detail="Boom")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 500
        body = _body_json(response)
        assert body["detail"] == "Boom"
        assert body["error_code"] == "UNKNOWN_ERROR"
        assert "request_id" not in body
        assert "x-request-id" not in {k.lower() for k in response.headers.keys()}

    @pytest.mark.anyio
    async def test_404_defaults_to_not_found_error_code(self):
        request = _make_request()
        exc = StarletteHTTPException(status_code=404, detail="Not Found")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 404
        assert _body_json(response)["error_code"] == "NOT_FOUND"

    @pytest.mark.anyio
    async def test_401_defaults_to_not_authenticated_error_code(self):
        request = _make_request()
        exc = HTTPException(status_code=401, detail="Not authenticated")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 401
        assert _body_json(response)["error_code"] == "NOT_AUTHENTICATED"

    @pytest.mark.anyio
    async def test_includes_request_id_in_body_and_header(self):
        rid = "11111111-1111-4111-8111-111111111111"
        request = _make_request(state={"request_id": rid})
        exc = HTTPException(status_code=403, detail="Forbidden")

        response = await http_exception_handler(request, exc)

        body = _body_json(response)
        assert body["request_id"] == rid
        assert response.headers["x-request-id"] == rid

    @pytest.mark.anyio
    async def test_preserves_custom_error_code(self):
        request = _make_request()
        exc = HTTPException(status_code=409, detail="Conflict")
        exc.error_code = "DUPLICATE_FIELD"

        response = await http_exception_handler(request, exc)

        assert _body_json(response)["error_code"] == "DUPLICATE_FIELD"

    @pytest.mark.anyio
    async def test_preserves_existing_exception_headers(self):
        rid = "22222222-2222-4222-8222-222222222222"
        request = _make_request(state={"request_id": rid})
        exc = HTTPException(
            status_code=401,
            detail="Unauthenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

        response = await http_exception_handler(request, exc)

        assert response.headers["www-authenticate"] == "Bearer"
        assert response.headers["x-request-id"] == rid


class TestSqlalchemyExceptionHandler:
    @pytest.mark.anyio
    async def test_returns_503(self):
        request = _make_request()
        exc = SQLAlchemyError("boom")

        response = await sqlalchemy_exception_handler(request, exc)

        assert response.status_code == 503
        body = _body_json(response)
        assert body["error_code"] == "MARIADB_CONNECTION_ERROR"
        assert body["detail"] == "Database temporarily unavailable."

    @pytest.mark.anyio
    async def test_omits_request_id_when_absent(self):
        request = _make_request()
        exc = SQLAlchemyError("boom")

        response = await sqlalchemy_exception_handler(request, exc)

        body = _body_json(response)
        assert "request_id" not in body
        assert "x-request-id" not in {k.lower() for k in response.headers.keys()}

    @pytest.mark.anyio
    async def test_includes_request_id_in_body_and_header(self):
        rid = "33333333-3333-4333-8333-333333333333"
        request = _make_request(state={"request_id": rid})
        exc = SQLAlchemyError("boom")

        response = await sqlalchemy_exception_handler(request, exc)

        body = _body_json(response)
        assert body["request_id"] == rid
        assert response.headers["x-request-id"] == rid
