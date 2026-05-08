from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from .associations import (
    course_template_association_table,
    template_app_association_table,
    template_event_association_table,
)
from .base import (
    AuditMixin,
    Base,
    DescriptionMixin,
    IDMixin,
    ProxmoxResourceMixin,
)


class Template(
    IDMixin, AuditMixin, DescriptionMixin, ProxmoxResourceMixin, Base
):
    __tablename__ = "kvs_templates"

    name = Column(String(100), unique=False, index=True, nullable=False)
    status = Column(String(25), unique=False, index=False, nullable=True)

    apps = relationship(
        "Application",
        secondary=template_app_association_table,
        back_populates="templates",
    )
    courses = relationship(
        "Course",
        secondary=course_template_association_table,
        back_populates="templates",
    )
    events = relationship(
        "Event",
        secondary=template_event_association_table,
        back_populates="templates",
    )
