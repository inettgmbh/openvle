"""Tests for CORS expose_headers configuration.

Verifies that rate-limit response headers are listed in
Access-Control-Expose-Headers so frontend JavaScript can read them.
"""

import asyncio

import httpx
from core.config import Settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def _request(app, headers=None):
    """Send a GET to / on a minimal ASGI app and return the response."""

    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.get("/", headers=headers or {})

    return asyncio.run(_run())


def _build_app(expose_headers):
    """Build a minimal FastAPI app with CORS configured."""
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=expose_headers,
    )

    @app.get("/")
    def root():
        return {"ok": True}

    return app


class TestCorsExposeHeadersDefaults:
    def test_default_includes_ratelimit_headers(self, monkeypatch):
        """Default cors_expose_headers contains all rate-limit headers."""
        monkeypatch.delenv("cors_expose_headers", raising=False)
        s = Settings()
        assert "Retry-After" in s.cors_expose_headers
        assert "X-RateLimit-Limit" in s.cors_expose_headers
        assert "X-RateLimit-Remaining" in s.cors_expose_headers
        assert "X-RateLimit-Reset" in s.cors_expose_headers

    def test_env_override_comma_separated(self, monkeypatch):
        """Comma-separated env value is parsed into a list."""
        monkeypatch.setenv("cors_expose_headers", "X-Custom,X-Other")
        s = Settings()
        assert s.cors_expose_headers == ["X-Custom", "X-Other"]

    def test_env_override_json_array(self, monkeypatch):
        """JSON-array env value is parsed into a list."""
        monkeypatch.setenv("cors_expose_headers", '["X-Foo", "X-Bar"]')
        s = Settings()
        assert s.cors_expose_headers == ["X-Foo", "X-Bar"]


class TestCorsExposeHeadersResponse:
    def test_emits_access_control_expose_headers(self):
        """CORS middleware emits Access-Control-Expose-Headers when origin is set."""
        s = Settings()
        app = _build_app(s.cors_expose_headers)

        response = _request(app, headers={"Origin": "http://example.com"})

        assert response.status_code == 200
        exposed = response.headers.get("access-control-expose-headers", "")
        for h in s.cors_expose_headers:
            assert h in exposed, (
                f"{h!r} missing from Access-Control-Expose-Headers: {exposed!r}"
            )

    def test_no_expose_header_without_origin(self):
        """Without an Origin request header, CORS adds no expose-headers."""
        s = Settings()
        app = _build_app(s.cors_expose_headers)

        response = _request(app)

        assert response.status_code == 200
        assert "access-control-expose-headers" not in response.headers
