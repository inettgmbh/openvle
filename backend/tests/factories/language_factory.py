"""Factory for Language model."""

import factory

from models import Language

from .base import BaseFactory


class LanguageFactory(BaseFactory):
    class Meta:
        model = Language

    nameEnglish = factory.Sequence(lambda n: f"Language {n}")
    nameTranslated = factory.Sequence(lambda n: f"Sprache {n}")
    key = factory.Sequence(lambda n: f"lang_{n:02d}")
