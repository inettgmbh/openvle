from pydantic import BaseModel, Field

from .base import PaginationPageDetails


class MoodleCourseSearch(BaseModel):
    """Moodle course data returned by the course search endpoint."""

    id: int = Field(..., description="Moodle internal course ID")
    fullname: str = Field(
        ..., description="Full display name of the Moodle course"
    )
    shortname: str = Field(
        ..., description="Short name/code of the Moodle course"
    )
    categoryname: str = Field(
        ..., description="Name of the category the Moodle course belongs to"
    )
    startdate: int = Field(
        ..., description="Unix timestamp of the course start date"
    )
    enddate: int = Field(
        ..., description="Unix timestamp of the course end date"
    )
    visible: bool = Field(
        ..., description="Whether the course is visible to students in Moodle"
    )


class MoodleCourseSearchList(BaseModel):
    """Paginated list of Moodle course search results."""

    pageDetails: PaginationPageDetails
    items: list[MoodleCourseSearch]
