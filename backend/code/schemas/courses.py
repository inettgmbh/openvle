from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails
from .templates import TemplateIdOnly, TemplateNested


# Courses base
class CourseBase(DBBase):
    name: str | None = None
    description: str | None = None
    guacamole: bool | None = False
    moodleCourseId: int | None = None

    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class CourseCreate(DBBaseCreate):
    name: str
    description: str | None = None
    guacamole: bool = False
    moodleCourseId: int | None = None


# Properties to receive via API on update
class CourseUpdate(DBBaseUpdate):
    name: str | None = None
    description: str | None = None
    guacamole: bool | None = False
    moodleCourseId: int | None = None


# Properties to receive via API on updateTemplate
class CourseUpdateTemplate(DBBaseUpdate):
    templates: list[TemplateIdOnly] | None = None


class CourseInDBBase(CourseBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Course(CourseInDBBase):
    templates: list[TemplateNested] | None = None
    model_config = ConfigDict(from_attributes=True)


# Class used for when Course is to appear as a nested model and will display key and name
class CourseNested(DBBaseUpdate):
    name: str

    model_config = ConfigDict(from_attributes=True)


# List object of Course
class CourseList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Course]
