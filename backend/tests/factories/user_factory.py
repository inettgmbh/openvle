"""Factory for User model."""

import factory
from models import User

from .base import BaseFactory


class UserFactory(BaseFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n:04d}")
    name = factory.Faker("name")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    hashed_password = (
        "$2b$12$LJ3m4ys3Lhyuq1G8s0VjCe0X6R4QqD7vQf5G6Y8pQ9N2jK5mW7xHi"
    )
    status = "Active"
    locale = "de_DE"
