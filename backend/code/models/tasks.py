from sqlalchemy import UUID, Column, ForeignKey, String

from .base import AuditMixin, Base, DescriptionMixin, IDMixin


class Task(IDMixin, AuditMixin, DescriptionMixin, Base):
    __tablename__ = "kvs_tasks"

    name = Column(String(250), unique=False, index=False, nullable=False)
    status = Column(String(50), unique=False, index=False, nullable=False)
    event_id = Column(
        UUID(as_uuid=True), ForeignKey("kvs_events.id"), nullable=True
    )
