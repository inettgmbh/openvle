from sqlalchemy import String
from sqlalchemy.orm import relationship

from .associations import *
from .base import (
    AuditMixin,
    Base,
    DescriptionMixin,
    IDMixin,
    VendoredSoftwareMixin,
)


class Application(
    IDMixin, AuditMixin, DescriptionMixin, VendoredSoftwareMixin, Base
):
    __tablename__ = "kvs_apps"

    key = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), unique=False, index=False, nullable=False)

    templates = relationship(
        "Template",
        secondary=template_app_association_table,
        back_populates="apps",
    )
    vms = relationship(
        "VirtualMachine",
        secondary=vm_app_association_table,
        back_populates="apps",
    )
    documents = relationship(
        "Document",
        secondary=documents_apps_association_table,
        back_populates="apps",
    )
