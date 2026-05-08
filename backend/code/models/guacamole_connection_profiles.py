from sqlalchemy import UUID, Column, Integer, String

from .base import AuditMixin, Base, IDMixin


class GuacamoleConnectionProfile(IDMixin, AuditMixin, Base):
    __tablename__ = "kvs_guacamole_connection_profile"

    port = Column(Integer, unique=False, index=False, default=3389)
    protocol = Column(String(3), default="RDP")
    username = Column(String(50), nullable=True)
    password = Column(String(50), nullable=True)
    objectId = Column(UUID(as_uuid=True), nullable=False, index=True)
    objectType = Column(String(100), unique=False, index=False, nullable=False)
