from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from .associations import course_template_association_table
from .base import AuditMixin, Base, DescriptionMixin, IDMixin, MoodleMixin


class Course(IDMixin, AuditMixin, DescriptionMixin, MoodleMixin, Base):
    __tablename__ = "kvs_courses"

    name = Column(String(255), unique=True, index=True, nullable=False)
    templates = relationship(
        "Template",
        secondary=course_template_association_table,
        back_populates="courses",
    )
