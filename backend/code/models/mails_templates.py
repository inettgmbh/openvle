from sqlalchemy import (
    TEXT,
    UUID,
    Boolean,
    Column,
    ForeignKey,
    String,
    UniqueConstraint,
)

from .base import AuditMixin, Base, DescriptionMixin, IDMixin


class MailTemplate(IDMixin, AuditMixin, DescriptionMixin, Base):
    __tablename__ = "sys_mails_templates"

    name = Column(String(100), unique=True, index=False, nullable=False)
    subject = Column(String(150), unique=False, index=False, nullable=False)
    fromName = Column(String(255), unique=False, index=False, nullable=True)
    fromMail = Column(String(254), unique=False, index=False, nullable=True)
    contentHTML = Column(TEXT, unique=False, index=False, nullable=False)
    contentPlain = Column(TEXT, unique=False, index=False, nullable=False)
    language = Column(
        UUID(as_uuid=True), ForeignKey("sys_languages.id"), nullable=False
    )
    protected = Column(Boolean, nullable=False, default=True)
    replyTo = Column(String(254), unique=False, index=False, nullable=True)
    mail_action = Column(
        UUID(as_uuid=True), ForeignKey("sys_mails_actions.id"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(language, mail_action, name="uq_language_mail_action"),
    )
