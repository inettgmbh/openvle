"""Factories for Event and EventStatus models."""

import uuid
from datetime import date, timedelta

import factory

from models import Event, EventStatus

from .base import BaseFactory


class EventStatusFactory(BaseFactory):
    class Meta:
        model = EventStatus

    name = factory.Iterator(
        [
            "Geplant",
            "Deploying",
            "Aktiv",
            "Archiving",
            "Archiviert",
            "Core Fehler",
            "Deployment Fehler",
        ]
    )


class EventFactory(BaseFactory):
    class Meta:
        model = Event

    name = factory.Sequence(lambda n: f"Event {n}")
    slug = factory.Sequence(lambda n: f"evt{n:04d}")
    description = factory.Faker("sentence")
    dateStart = factory.LazyFunction(lambda: date.today() + timedelta(days=14))
    dateEnd = factory.LazyFunction(lambda: date.today() + timedelta(days=21))
    guacamole = True
    status = factory.LazyFunction(uuid.uuid4)  # Must be set to actual EventStatus.id
    course = factory.LazyFunction(uuid.uuid4)  # Must be set to actual Course.id
