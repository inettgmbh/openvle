"""Base factory with common fields for all DBBaseModel entities."""

import uuid
from datetime import datetime, timezone

import factory
from factory.alchemy import SQLAlchemyModelFactory


class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = None  # Set per test via autouse fixture
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(uuid.uuid4)
    createdAt = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updatedAt = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    createdById = None
    updatedById = None
