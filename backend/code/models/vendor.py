from sqlalchemy import Column, String

from .base import AuditMixin, Base, DescriptionMixin, IDMixin


class Vendor(IDMixin, AuditMixin, DescriptionMixin, Base):
    __tablename__ = "kvs_vendors"

    name = Column(String(100), unique=True, index=False, nullable=False)
