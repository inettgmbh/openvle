from sqlalchemy import Boolean, Column, String, Text

from .base import AuditMixin, Base, DescriptionMixin, IDMixin


class Policy(IDMixin, AuditMixin, DescriptionMixin, Base):
    __tablename__ = "sys_policies"

    name = Column(String(50), unique=True, index=False, nullable=False)
    content = Column(Text, unique=False, index=True, nullable=False)
    active = Column(
        Boolean, unique=False, index=False, nullable=False, default=False
    )
