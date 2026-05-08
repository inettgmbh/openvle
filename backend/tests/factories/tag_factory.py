"""Factory for Tag model."""

import uuid

import factory

from models import Tag

from .base import BaseFactory


class TagFactory(BaseFactory):
    class Meta:
        model = Tag

    key = factory.Sequence(lambda n: f"tag_key_{n}")
    value = factory.Sequence(lambda n: f"tag_value_{n}")
    objectId = factory.LazyFunction(uuid.uuid4)
    objectType = "VirtualMachine"
