"""Factory for Document model."""

import factory

from models import Document

from .base import BaseFactory


class DocumentFactory(BaseFactory):
    class Meta:
        model = Document

    name = factory.Sequence(lambda n: f"Document {n}")
    description = factory.Faker("sentence")
    path = factory.Sequence(lambda n: f"/docs/document_{n}.pdf")
