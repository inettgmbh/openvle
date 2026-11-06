"""Factory for Policy model."""

import factory
from models import Policy

from .base import BaseFactory


class PolicyFactory(BaseFactory):
    class Meta:
        model = Policy

    name = factory.Sequence(lambda n: f"Policy {n}")
    description = factory.Faker("sentence")
    content = factory.Faker("paragraph")
    active = False
