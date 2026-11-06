"""Factory for SystemSetting model."""

import factory
from models import SystemSetting

from .base import BaseFactory


class SystemSettingFactory(BaseFactory):
    class Meta:
        model = SystemSetting

    key = factory.Sequence(lambda n: f"setting_key_{n}")
    value = factory.Sequence(lambda n: f"value_{n}")
    visibility = "public"
    description = factory.Faker("sentence")
