import uuid

from sqlalchemy import UUID, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import as_declarative, declarative_base, relationship

from .users import User

Base = declarative_base()


class Changelog(Base):
    __tablename__ = "sys_changelogs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    timestamp = Column(DateTime, nullable=False)
    valueOld = Column(String(2000), unique=False, index=False, nullable=True)
    valueNew = Column(String(2000), unique=False, index=False, nullable=True)
    object = Column(String(255), unique=False, index=False, nullable=True)
    objectId = Column(UUID(as_uuid=True), nullable=False)
    userId = Column(UUID(as_uuid=True), ForeignKey(User.id), nullable=False)
