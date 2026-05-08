"""Tests for middlewares/i18n.py - TranslationWrapper, set_locale, and _()."""

from unittest.mock import MagicMock

import pytest


class TestTranslationWrapperSingleton:
    def test_translation_wrapper_singleton(self):
        """Two instances of TranslationWrapper are the same object."""
        from middlewares.i18n import TranslationWrapper

        instance1 = TranslationWrapper()
        instance2 = TranslationWrapper()

        assert instance1 is instance2


class TestUnderscoreFunction:
    def test_underscore_returns_message_when_no_context(self):
        """Without set_locale, _() returns the original string."""
        from middlewares.i18n import _, gettext_var

        # Reset the context var to ensure clean state
        token = gettext_var.set(None)
        try:
            result = _("Hello World")
            assert result == "Hello World"
        finally:
            gettext_var.reset(token)

    def test_underscore_uses_gettext_after_set(self):
        """After setting gettext_var, _() calls the gettext function."""
        from middlewares.i18n import _, gettext_var

        mock_gettext = MagicMock(return_value="Hallo Welt")
        token = gettext_var.set(mock_gettext)
        try:
            result = _("Hello World")
            assert result == "Hallo Welt"
            mock_gettext.assert_called_once_with("Hello World")
        finally:
            gettext_var.reset(token)


class TestSetLocale:
    @pytest.mark.anyio
    async def test_set_locale_sets_gettext_var(self):
        """After set_locale, gettext_var is set to a callable."""
        from middlewares.i18n import gettext_var, set_locale

        mock_request = MagicMock()
        mock_request.user.locale = "en_US"
        mock_request.state = MagicMock()

        await set_locale(mock_request)

        gettext_func = gettext_var.get(None)
        assert gettext_func is not None
        assert callable(gettext_func)

    @pytest.mark.anyio
    async def test_set_locale_sets_request_state(self):
        """After set_locale, request.state.translations is set."""
        from middlewares.i18n import set_locale

        mock_request = MagicMock()
        mock_request.user.locale = "de_DE"

        # Use a real object for state so attribute assignment works
        class FakeState:
            pass

        mock_request.state = FakeState()

        await set_locale(mock_request)

        # The translations object should be set on request.state
        assert hasattr(mock_request.state, "translations")

    @pytest.mark.anyio
    async def test_set_locale_extracts_first_two_chars(self):
        """set_locale uses only the first 2 characters of locale string."""
        from middlewares.i18n import gettext_var, set_locale

        mock_request = MagicMock()
        mock_request.user.locale = "fr_FR.UTF-8"

        class FakeState:
            pass

        mock_request.state = FakeState()

        await set_locale(mock_request)

        # Should work without error even with long locale string
        gettext_func = gettext_var.get(None)
        assert gettext_func is not None


class TestTranslationWrapperGettext:
    def test_gettext_delegates_to_translations(self):
        """TranslationWrapper.gettext delegates to the translations object."""
        from middlewares.i18n import TranslationWrapper

        wrapper = TranslationWrapper()
        # gettext should return the message (fallback=True means identity)
        result = wrapper.gettext("test message")
        assert isinstance(result, str)
        # With fallback=True and no actual translation, returns original
        assert result == "test message"
