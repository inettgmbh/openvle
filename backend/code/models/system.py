import json

from sqlalchemy import Column, String

from schemas.system import SystemSettingValueType

from .base import AuditMixin, Base, IDMixin


class SystemSetting(IDMixin, AuditMixin, Base):
    __tablename__ = "sys_settings"

    key = Column(String(250), unique=True, index=True, nullable=False)
    value = Column(String(250), unique=False, index=False, nullable=False)
    visibility = Column(String(20), unique=False, index=True, nullable=False)
    description = Column(
        String(1000), unique=False, index=False, nullable=False
    )

    @property
    def type(self) -> str:
        """Return the JSON type of the value field."""
        try:
            parsed = json.loads(self.value)  # type: ignore
        except (ValueError, TypeError):
            parsed = self.value

        if parsed is None:
            return SystemSettingValueType.null
        elif isinstance(parsed, bool):
            return SystemSettingValueType.boolean
        elif isinstance(parsed, int):
            return SystemSettingValueType.integer
        elif isinstance(parsed, float):
            return SystemSettingValueType.float
        elif isinstance(parsed, dict):
            return SystemSettingValueType.object
        elif isinstance(parsed, list):
            return SystemSettingValueType.array
        else:
            return SystemSettingValueType.string
