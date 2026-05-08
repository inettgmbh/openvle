"""Factories for Guacamole and GuacamoleConnectionProfile models."""

import uuid

import factory

from models import Guacamole, GuacamoleConnectionProfile

from .base import BaseFactory


class GuacamoleConnectionProfileFactory(BaseFactory):
    class Meta:
        model = GuacamoleConnectionProfile

    port = 3389
    protocol = "RDP"
    username = "admin"
    password = "password"
    objectId = factory.LazyFunction(uuid.uuid4)
    objectType = "VirtualMachine"


class GuacamoleFactory(BaseFactory):
    class Meta:
        model = Guacamole

    name = factory.Sequence(lambda n: f"Guacamole Connection {n}")
    guacd_hostname = "guacd.local"
    guacd_port = 4822
    guacd_encryption = True
    connection_hostname = factory.Sequence(lambda n: f"10.0.1.{n + 10}")
    connection_profile = factory.LazyFunction(
        uuid.uuid4
    )  # Must be set to actual GCP.id
    identifier = factory.Sequence(lambda n: 100 + n)
    userId = factory.LazyFunction(uuid.uuid4)  # Must be set to actual User.id
    eventId = None
