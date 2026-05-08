from sqlalchemy import Boolean, String
from sqlalchemy.orm import relationship

from .associations import *
from .base import AuditMixin, Base, DescriptionMixin, IDMixin


class Role(IDMixin, AuditMixin, DescriptionMixin, Base):
    __tablename__ = "sys_roles"

    name = Column(String(255), unique=False, index=False, nullable=False)
    key = Column(String(255), unique=True, index=True, nullable=False)
    protected = Column(Boolean, unique=False, index=False, nullable=False)
    users = relationship(
        "User", secondary=user_role_association_table, back_populates="roles"
    )
