from sqlalchemy import UUID, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .associations import vm_guac_association_table
from .base import AuditMixin, Base, DescriptionMixin, IDMixin


class Guacamole(IDMixin, AuditMixin, DescriptionMixin, Base):
    __tablename__ = "kvs_guacamole"

    name = Column(String(100), unique=False, index=True, nullable=False)
    guacd_hostname = Column(
        String(50), unique=False, index=False, nullable=True
    )
    guacd_port = Column(Integer, unique=False, index=False, default=4822)
    guacd_encryption = Column(Boolean, default=True)
    connection_hostname = Column(
        String(100), unique=False, index=False, nullable=True
    )
    connection_profile = Column(
        UUID(as_uuid=True),
        ForeignKey("kvs_guacamole_connection_profile.id"),
        nullable=False,
    )
    identifier = Column(Integer, unique=True, index=True, nullable=True)
    userId = Column(UUID, ForeignKey("sys_users.id"), nullable=False)
    eventId = Column(UUID, ForeignKey("kvs_events.id"), nullable=True)

    user = relationship(
        "User", back_populates="guacamoleConfigs", foreign_keys=[userId]
    )
    vms = relationship(
        "VirtualMachine",
        secondary=vm_guac_association_table,
        back_populates="guacamoles",
    )
