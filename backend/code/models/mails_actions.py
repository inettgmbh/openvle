from sqlalchemy import Column, String

from .base import AuditMixin, Base, DescriptionMixin, IDMixin


class MailAction(IDMixin, AuditMixin, DescriptionMixin, Base):
    __tablename__ = "sys_mails_actions"

    name = Column(String(100), unique=False, index=True, nullable=False)
    slug = Column(String(50), unique=True, index=True, nullable=False)
