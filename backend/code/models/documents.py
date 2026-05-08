from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from .associations import (
    documents_apps_association_table,
    documents_os_association_table,
)
from .base import AuditMixin, Base, DescriptionMixin, IDMixin


class Document(IDMixin, AuditMixin, DescriptionMixin, Base):
    __tablename__ = "kvs_documents"

    name = Column(String(100), unique=True, index=False, nullable=False)
    path = Column(String(100), unique=True, index=False, nullable=True)

    apps = relationship(
        "Application",
        secondary=documents_apps_association_table,
        back_populates="documents",
    )
    os = relationship(
        "OS",
        secondary=documents_os_association_table,
        back_populates="documents",
    )
