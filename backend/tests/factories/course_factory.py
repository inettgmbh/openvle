"""Factory for Course model."""

import factory
from models import Course

from .base import BaseFactory


class CourseFactory(BaseFactory):
    class Meta:
        model = Course

    name = factory.Sequence(lambda n: f"Course {n}")
    description = factory.Faker("sentence")
    guacamole = True
