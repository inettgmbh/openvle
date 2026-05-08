from sqlalchemy import UUID, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from .associations import (
    user_vm_association_table,
    vm_app_association_table,
    vm_guac_association_table,
)
from .base import (
    AuditMixin,
    Base,
    DescriptionMixin,
    IDMixin,
    ProxmoxResourceMixin,
)


class VirtualMachine(
    IDMixin, AuditMixin, DescriptionMixin, ProxmoxResourceMixin, Base
):
    __tablename__ = "kvs_vms"

    name = Column(String(100), unique=False, index=True, nullable=False)
    status = Column(String(100), unique=False, index=False, nullable=True)
    template = Column(
        UUID(as_uuid=True), ForeignKey("kvs_templates.id"), nullable=True
    )
    event = Column(
        UUID(as_uuid=True), ForeignKey("kvs_events.id"), nullable=True
    )
    ipv4 = Column(String(50), unique=False, index=False, nullable=True)

    apps = relationship(
        "Application", secondary=vm_app_association_table, back_populates="vms"
    )
    guacamoles = relationship(
        "Guacamole", secondary=vm_guac_association_table, back_populates="vms"
    )
    users = relationship(
        "User", secondary=user_vm_association_table, back_populates="vms"
    )
