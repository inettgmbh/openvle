from datetime import datetime
from typing import List

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import PaginationPageDetails


# Base DB class for all objects
class Changelog(BaseModel):
    """Audit log entry recording a field-level change on a database object."""

    id: UUID4 = Field(
        ..., description="Unique identifier of the changelog entry"
    )
    timestamp: datetime = Field(
        ..., description="Timestamp when the change was made"
    )
    valueOld: str = Field(
        ..., description="Previous value of the changed field"
    )
    valueNew: str = Field(..., description="New value of the changed field")
    object: str = Field(
        ...,
        description="Type of the object that was changed, e.g. VirtualMachine",
    )
    objectId: UUID4 = Field(
        ..., description="ID of the object that was changed"
    )
    userId: UUID4 = Field(..., description="ID of the user who made the change")

    model_config = ConfigDict(from_attributes=True)


# List object of Event
class ChangelogList(BaseModel):
    """Paginated list of changelog entries."""

    pageDetails: PaginationPageDetails
    items: list[Changelog]
