"""Factory for ObjectPermission model."""

import uuid

import factory

from models import ObjectPermission

from .base import BaseFactory


class ObjectPermissionFactory(BaseFactory):
    class Meta:
        model = ObjectPermission

    object_type = "Course"
    object_id = factory.LazyFunction(uuid.uuid4)
    entity_id = factory.LazyFunction(uuid.uuid4)
    entity_type = "User"
    permission_key = "object_full"
