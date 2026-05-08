from sqlalchemy import UUID, Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import AuditMixin, Base, IDMixin


class EventsUser(IDMixin, AuditMixin, Base):
    __tablename__ = "kvs_events_user"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("sys_users.id"), nullable=False
    )
    event_id = Column(
        UUID(as_uuid=True), ForeignKey("kvs_events.id"), nullable=False
    )
    role_id = Column(
        UUID(as_uuid=True), ForeignKey("sys_roles.id"), nullable=False
    )

    __table_args__ = (UniqueConstraint(user_id, event_id),)
