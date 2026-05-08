import uuid

from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import as_declarative, declared_attr, relationship

class_registry: dict = {}


@as_declarative(class_registry=class_registry)
class Base:
    pass


# Backward-compatible alias — callers importing DBBaseModel still work
DBBaseModel = Base


class IDMixin:
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )


class AuditMixin:
    createdAt = Column(DateTime, nullable=False)
    updatedAt = Column(DateTime, nullable=False)
    createdById = Column(
        UUID(as_uuid=True), ForeignKey("sys_users.id"), nullable=True
    )
    updatedById = Column(
        UUID(as_uuid=True), ForeignKey("sys_users.id"), nullable=True
    )

    @declared_attr
    def createdBy(cls):
        return relationship(
            "User", foreign_keys=[cls.createdById], post_update=True
        )

    @declared_attr
    def updatedBy(cls):
        return relationship(
            "User", foreign_keys=[cls.updatedById], post_update=True
        )


class DescriptionMixin:
    description = Column(String(1000), nullable=True)


class ProxmoxResourceMixin:
    proxmoxId = Column(Integer, unique=False, index=False, nullable=True)
    proxmoxNode = Column(String(50), unique=False, index=False, nullable=True)
    cpu = Column(Integer, unique=False, index=False, nullable=False)
    ram = Column(Integer, unique=False, index=False, nullable=False)
    disk = Column(Integer, unique=False, index=False, nullable=False)
    os = Column(UUID(as_uuid=True), ForeignKey("kvs_os.id"), nullable=True)
    prevent_delete = Column(
        Boolean, unique=False, index=False, nullable=False, default=False
    )


class MoodleMixin:
    moodleCourseId = Column(Integer, unique=True, index=True, nullable=True)
    guacamole = Column(
        Boolean, unique=False, index=False, nullable=False, default=True
    )


class VendoredSoftwareMixin:
    patch_level = Column(String(255), unique=False, index=False, nullable=True)
    vendor = Column(
        UUID(as_uuid=True), ForeignKey("kvs_vendors.id"), nullable=False
    )
