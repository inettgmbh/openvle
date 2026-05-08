from sqlalchemy import UUID, Column, String

from .base import AuditMixin, Base, DescriptionMixin, IDMixin


class Tag(IDMixin, AuditMixin, DescriptionMixin, Base):
    __tablename__ = "kvs_tags"

    key = Column(String(50), unique=False, index=True, nullable=False)
    value = Column(String(100), unique=False, index=True, nullable=False)
    objectId = Column(UUID(as_uuid=True), nullable=False)
    objectType = Column(String(100), unique=False, index=False, nullable=False)
