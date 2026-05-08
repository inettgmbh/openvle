from sqlalchemy import TEXT, UUID, Column, ForeignKey, String

from .base import AuditMixin, Base, IDMixin


class Mail(IDMixin, AuditMixin, Base):
    __tablename__ = "sys_mails"

    subject = Column(String(150), unique=False, index=False, nullable=False)
    fromName = Column(String(50), unique=False, index=False, nullable=False)
    fromMail = Column(String(254), unique=False, index=False, nullable=False)
    toMail = Column(String(254), unique=False, index=False, nullable=False)
    sendStatus = Column(String(25), unique=False, index=False, nullable=False)
    templateId = Column(
        UUID(as_uuid=True), ForeignKey("sys_mails_templates.id"), nullable=False
    )
    replyTo = Column(String(254), unique=False, index=False, nullable=False)
    content_rendered = Column(TEXT, unique=False, index=False, nullable=True)
    event = Column(
        UUID(as_uuid=True), ForeignKey("kvs_events.id"), nullable=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("sys_users.id"), nullable=True
    )
