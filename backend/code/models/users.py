from sqlalchemy import UUID, Column, DateTime, String
from sqlalchemy.orm import relationship

from .associations import (
    user_role_association_table,
    user_vm_association_table,
)
from .base import AuditMixin, Base, DescriptionMixin, IDMixin
from .guacamole import Guacamole
from .os import OS
from .roles import Role
from .templates import Template


class User(IDMixin, AuditMixin, DescriptionMixin, Base):
    __tablename__ = "sys_users"

    username = Column(String(25), unique=True, index=True, nullable=False)
    name = Column(String(256), unique=False, index=False, nullable=True)
    email = Column(String(254), unique=True, index=True, nullable=False)
    hashed_password = Column(
        String(100), unique=False, index=False, nullable=True
    )
    resetToken = Column(
        UUID(as_uuid=True), unique=False, index=False, nullable=True
    )
    resetTokenCreatedAt = Column(
        DateTime, unique=False, index=False, nullable=True
    )
    status = Column(
        String(50),
        unique=False,
        index=False,
        nullable=False,
        server_default="E-Mail-Pending",
    )
    locale = Column(
        String(8),
        unique=False,
        index=False,
        nullable=False,
        server_default="de_DE",
    )
    twoFactorSecret = Column(
        String(100), unique=False, index=False, nullable=True
    )
    mailValidateToken = Column(
        UUID(as_uuid=True), unique=False, index=False, nullable=True
    )
    roles = relationship(
        "Role", secondary=user_role_association_table, back_populates="users"
    )
    rolesCreated = relationship(
        "Role", back_populates="createdBy", foreign_keys=[Role.createdById]
    )
    rolesUpdated = relationship(
        "Role", back_populates="updatedBy", foreign_keys=[Role.updatedById]
    )
    templatesCreated = relationship(
        "Template",
        back_populates="createdBy",
        foreign_keys=[Template.createdById],
    )
    templatesUpdated = relationship(
        "Template",
        back_populates="updatedBy",
        foreign_keys=[Template.updatedById],
    )
    osCreated = relationship(
        "OS", back_populates="createdBy", foreign_keys=[OS.createdById]
    )
    osUpdated = relationship(
        "OS", back_populates="updatedBy", foreign_keys=[OS.updatedById]
    )
    guacamoleConfigs = relationship(
        "Guacamole", back_populates="user", foreign_keys=[Guacamole.userId]
    )
    guacamolesCreated = relationship(
        "Guacamole",
        back_populates="createdBy",
        foreign_keys=[Guacamole.createdById],
    )
    guacamolesUpdated = relationship(
        "Guacamole",
        back_populates="updatedBy",
        foreign_keys=[Guacamole.updatedById],
    )
    vms = relationship(
        "VirtualMachine",
        secondary=user_vm_association_table,
        back_populates="users",
    )

    # TODO: LDAP column KVS-80

    # The following relationships are placeholders as the referenced models/schemas have not yet been implemented
    """
    activitiesCreated = relationship('Activity', back_populates="createdBy", foreign_keys=[Activity.createdById])
    activitiesUpdated = relationship('Activity', back_populates="updatedBy", foreign_keys=[Activity.updatedById])
    sessionsCreated = relationship('Session', back_populates="createdBy", foreign_keys=[Session.createdById])
    sessionsUpdated = relationship('Session', back_populates="updatedBy", foreign_keys=[Session.updatedById])
    vmsCreated = relationship('VM', back_populates="createdBy", foreign_keys=[VM.createdById])
    vmsUpdated = relationship('VM', back_populates="updatedBy", foreign_keys=[VM.updatedById])
    statusUsersCreated = relationship('StatusUser', back_populates="createdBy", foreign_keys=[StatusUser.createdById])
    statusUsersUpdated = relationship('StatusUser', back_populates="updatedBy", foreign_keys=[StatusUser.updatedById])
    statusEventsCreated = relationship('StatusEvent', back_populates="createdBy",
                                       foreign_keys=[StatusEvent.createdById])
    statusEventsUpdated = relationship('StatusEvent', back_populates="updatedBy",
                                       foreign_keys=[StatusEvent.updatedById])
    statusCoursesCreated = relationship('StatusCourse', back_populates="createdBy",
                                        foreign_keys=[StatusCourse.createdById])
    statusCoursesUpdated = relationship('StatusCourse', back_populates="updatedBy",
                                        foreign_keys=[StatusCourse.updatedById])
    
    mailTemplatesCreated = relationship('MailTemplate', back_populates="createdBy",
                                        foreign_keys=[MailTemplate.createdById])
    mailTemplatesUpdated = relationship('MailTemplate', back_populates="updatedBy",
                                        foreign_keys=[MailTemplate.updatedById])
    mailsCreated = relationship('Mail', back_populates="createdBy", foreign_keys=[Mail.createdById])
    mailsUpdated = relationship('Mail', back_populates="updatedBy", foreign_keys=[Mail.updatedById])
    languagesCreated = relationship('Language', back_populates="createdBy", foreign_keys=[Language.createdById])
    languagesUpdated = relationship('Language', back_populates="updatedBy", foreign_keys=[Language.updatedById])

    eventsCreated = relationship('Event', back_populates="createdBy", foreign_keys=[Event.createdById])
    eventsUpdated = relationship('Event', back_populates="updatedBy", foreign_keys=[Event.updatedById])
    coursesCreated = relationship('Course', back_populates="createdBy", foreign_keys=[Course.createdById])
    coursesUpdated = relationship('Course', back_populates="updatedBy", foreign_keys=[Course.updatedById])
    """
