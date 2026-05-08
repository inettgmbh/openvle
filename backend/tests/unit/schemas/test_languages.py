"""Tests for schemas/languages.py - Language schema validation."""

import uuid

from schemas.languages import Language


class TestLanguage:
    def test_valid_language(self):
        lang = Language(
            id=uuid.uuid4(),
            nameEnglish="German",
            nameTranslated="Deutsch",
            key="de_DE",
        )
        assert lang.nameEnglish == "German"
        assert lang.nameTranslated == "Deutsch"
        assert lang.key == "de_DE"
