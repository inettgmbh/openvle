from sqlalchemy import Column, String

from .base import AuditMixin, Base, IDMixin


class Language(IDMixin, AuditMixin, Base):
    __tablename__ = "sys_languages"

    nameEnglish = Column(String(50), unique=True, index=False, nullable=False)
    nameTranslated = Column(
        String(50), unique=True, index=False, nullable=False
    )
    key = Column(String(8), unique=True, index=True, nullable=False)
