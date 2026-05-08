from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from .associations import documents_os_association_table
from .base import (
    AuditMixin,
    Base,
    DescriptionMixin,
    IDMixin,
    VendoredSoftwareMixin,
)


class OS(IDMixin, AuditMixin, DescriptionMixin, VendoredSoftwareMixin, Base):
    __tablename__ = "kvs_os"

    name = Column(String(100), unique=False, index=False, nullable=False)
    key = Column(String(255), unique=True, index=True, nullable=False)
    version = Column(String(100), unique=False, index=False, nullable=False)
    documents = relationship(
        "Document",
        secondary=documents_os_association_table,
        back_populates="os",
    )
