from sqlalchemy import UUID, Column, String
from sqlalchemy.orm import relationship

from .base import AuditMixin, Base, IDMixin


class ObjectPermission(IDMixin, AuditMixin, Base):
    __tablename__ = "sys_object_permissions"

    object_type = Column(String(50), unique=False, index=False, nullable=False)
    object_id = Column(
        UUID(as_uuid=True), unique=False, index=False, nullable=True
    )
    entity_id = Column(
        UUID(as_uuid=True), unique=False, index=False, nullable=False
    )
    entity_type = Column(String(50), unique=False, index=False, nullable=False)
    permission_key = Column(
        String(25), unique=False, index=False, nullable=False
    )
