from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails
from .templates import TemplateIdOnly, TemplateNested


# Courses base
class CourseBase(DBBase):
    """Base schema for course objects with common fields."""

    name: str | None = Field(None, description="Display name of the course")
    description: str | None = Field(
        None, description="Optional description of the course"
    )
    guacamole: bool | None = Field(
        False,
        description="Whether Guacamole remote access is enabled for the course",
    )
    moodleCourseId: int | None = Field(
        None, description="Associated Moodle course ID, if any"
    )

    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class CourseCreate(DBBaseCreate):
    """Payload for creating a new course."""

    name: str = Field(..., description="Display name of the course")
    description: str | None = Field(
        None, description="Optional description of the course"
    )
    guacamole: bool = Field(
        False,
        description="Whether Guacamole remote access is enabled for the course",
    )
    moodleCourseId: int | None = Field(
        None, description="Associated Moodle course ID, if any"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Grundlagen der Informatik",
                "description": "Einführung in die Grundlagen der Informatik",
                "guacamole": False,
                "moodleCourseId": None,
            }
        }
    )


# Properties to receive via API on update
class CourseUpdate(DBBaseUpdate):
    """Payload for updating an existing course."""

    name: str | None = Field(None, description="Display name of the course")
    description: str | None = Field(
        None, description="Optional description of the course"
    )
    guacamole: bool | None = Field(
        False,
        description="Whether Guacamole remote access is enabled for the course",
    )
    moodleCourseId: int | None = Field(
        None, description="Associated Moodle course ID, if any"
    )


# Properties to receive via API on updateTemplate
class CourseUpdateTemplate(DBBaseUpdate):
    """Payload for replacing the templates assigned to a course."""

    templates: list[TemplateIdOnly] | None = Field(
        None, description="List of template IDs to assign to the course"
    )


class CourseInDBBase(CourseBase):
    """Internal course schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Course(CourseInDBBase):
    """Full course response schema including associated templates."""

    templates: list[TemplateNested] | None = None
    model_config = ConfigDict(from_attributes=True)


# Class used for when Course is to appear as a nested model and will display key and name
class CourseNested(DBBaseUpdate):
    """Minimal course schema for nested references, shows name only."""

    name: str = Field(..., description="Display name of the course")

    model_config = ConfigDict(from_attributes=True)


# List object of Course
class CourseList(BaseModel):
    """Paginated list of course objects."""

    pageDetails: PaginationPageDetails
    items: list[Course]
