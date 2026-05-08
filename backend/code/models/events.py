from sqlalchemy import (
    UUID,
    Column,
    Date,
    ForeignKey,
    String,
    Time,
)
from sqlalchemy.orm import relationship

from .associations import template_event_association_table
from .base import AuditMixin, Base, DescriptionMixin, IDMixin, MoodleMixin


class Event(IDMixin, AuditMixin, DescriptionMixin, MoodleMixin, Base):
    __tablename__ = "kvs_events"

    name = Column(String(50), unique=True, index=True, nullable=False)
    slug = Column(String(8), unique=True, index=True, nullable=False)
    dateStart = Column(Date, index=False, nullable=False)
    dateEnd = Column(Date, index=False, nullable=True)
    timeStart = Column(Time(timezone=True), index=False, nullable=True)
    timeEnd = Column(Time(timezone=True), index=False, nullable=True)
    status = Column(
        UUID(as_uuid=True), ForeignKey("kvs_events_status.id"), nullable=False
    )
    course = Column(
        UUID(as_uuid=True), ForeignKey("kvs_courses.id"), nullable=False
    )
    deployment_status = Column(
        String(500), unique=False, index=False, nullable=True
    )

    templates = relationship(
        "Template",
        secondary=template_event_association_table,
        back_populates="events",
        cascade="all, delete",
        passive_deletes=True,
    )
