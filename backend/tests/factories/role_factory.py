"""Factory for Role model."""

import factory

from models import Role

from .base import BaseFactory


class RoleFactory(BaseFactory):
    class Meta:
        model = Role

    name = factory.Sequence(lambda n: f"Role {n}")
    description = factory.Faker("sentence")
    key = factory.Sequence(lambda n: f"role_{n}")
    protected = False
