from collections.abc import Callable
from contextvars import ContextVar
from gettext import translation
from pathlib import Path

from fastapi import Request


class TranslationWrapper:
    _instance = None

    def __new__(cls):
        """
        Create a new instance of the class if it doesn't
        exist, otherwise return the existing instance.
        Returns: TranslationWrapper: The instance of the class.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init_translation()
        return cls._instance

    def init_translation(self) -> None:
        locales_dir = (Path(__file__).parent.parent / "translations").resolve()
        lang = "en"
        self.translations = translation(
            "messages", localedir=locales_dir, languages=[lang], fallback=True
        )
        self.translations.install()

    def gettext(self, message: str) -> str:
        """
        Get the translated string for the specified message.
        Args: message (str): The message to be translated.
        Returns: str: The translated string.
        """
        return self.translations.gettext(message)


async def set_locale(request: Request):
    """
    Set the locale based on the request.user.locale value set in Authentication middleware.
    Args: request (Request): The incoming request object.
    """
    translation_wrapper = TranslationWrapper()
    lang = request.user.locale[:2]
    locales_dir = (Path(__file__).parent.parent / "translations").resolve()
    translation_wrapper.translations = translation(
        "messages", localedir=locales_dir, languages=[lang], fallback=True
    )
    translation_wrapper.translations.install()
    translation_wrapper.request = request
    request.state.translations = translation_wrapper.translations
    gettext_var.set(translation_wrapper.translations.gettext)


# Create ContextVar with getttext to be set in set_locale
gettext_var: ContextVar[Callable[[str], str]] = ContextVar("gettext_var")


def _(message: str) -> str:
    # Get ContextVar for gettext with language of request.user
    gettext = gettext_var.get(None)
    if gettext is not None:
        return gettext(message)
    return message
