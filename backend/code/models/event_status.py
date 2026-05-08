from sqlalchemy import Column, String

from .base import AuditMixin, Base, IDMixin


class EventStatus(IDMixin, AuditMixin, Base):
    __tablename__ = "kvs_events_status"

    name = Column(String(100), unique=True, index=False, nullable=False)
