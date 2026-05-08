"""Tests for middlewares/language.py - LanguageMiddleware."""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestLanguageMiddleware:
    @pytest.mark.anyio
    async def test_calls_set_locale(self, monkeypatch):
        """Verifies set_locale is called with the request."""
        mock_set_locale = AsyncMock()
        monkeypatch.setattr("middlewares.language.set_locale", mock_set_locale)

        from middlewares.language import LanguageMiddleware

        middleware = LanguageMiddleware(app=MagicMock())
        request = MagicMock()
        response = MagicMock()

        call_next = AsyncMock(return_value=response)

        await middleware.dispatch(request, call_next)

        mock_set_locale.assert_awaited_once_with(request)

    @pytest.mark.anyio
    async def test_passes_request_to_next(self, monkeypatch):
        """call_next receives the request."""
        mock_set_locale = AsyncMock()
        monkeypatch.setattr("middlewares.language.set_locale", mock_set_locale)

        from middlewares.language import LanguageMiddleware

        middleware = LanguageMiddleware(app=MagicMock())
        request = MagicMock()
        response = MagicMock()

        call_next = AsyncMock(return_value=response)

        await middleware.dispatch(request, call_next)

        call_next.assert_awaited_once_with(request)

    @pytest.mark.anyio
    async def test_returns_response(self, monkeypatch):
        """Returns the response from call_next."""
        mock_set_locale = AsyncMock()
        monkeypatch.setattr("middlewares.language.set_locale", mock_set_locale)

        from middlewares.language import LanguageMiddleware

        middleware = LanguageMiddleware(app=MagicMock())
        request = MagicMock()
        expected_response = MagicMock()

        call_next = AsyncMock(return_value=expected_response)

        result = await middleware.dispatch(request, call_next)

        assert result is expected_response
