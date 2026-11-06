from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base EventStatus class
class EventStatusBase(DBBase):
    """Base schema for event status objects used to categorise events."""

    name: str | None = Field(
        None,
        description="Display name of the event status, e.g. Active, Planned, Archived",
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class EventStatusCreate(DBBaseCreate):
    """Payload for creating a new event status."""

    name: str = Field(
        ...,
        description="Display name of the event status, e.g. Active, Planned, Archived",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Geplant",
            }
        }
    )


# Properties to receive via API on update
class EventStatusUpdate(DBBaseUpdate):
    """Payload for updating an existing event status name."""

    name: str | None = Field(
        None, description="Display name of the event status"
    )
    model_config = ConfigDict(from_attributes=True)


class EventStatusInDBBase(EventStatusBase):
    """Internal event status schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class EventStatus(EventStatusInDBBase):
    """Full event status response schema."""

    name: str

    model_config = ConfigDict(from_attributes=True)


# Class used for when EventStatus is to appear as a nested model and will only display status
class EventStatusNested(DBBaseUpdate):
    """Minimal event status schema for nested references, shows name only."""

    name: str = Field(..., description="Display name of the event status")

    model_config = ConfigDict(from_attributes=True)


# List object of EventStatus
class EventStatusList(BaseModel):
    """Paginated list of event status objects."""

    pageDetails: PaginationPageDetails
    items: list[EventStatus]
