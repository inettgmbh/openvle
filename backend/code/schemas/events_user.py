from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base EventsUser class
class EventsUserBase(DBBase):
    """Base schema for the event-user enrollment association."""

    user_id: UUID4 = Field(..., description="ID of the enrolled user")
    role_id: UUID4 = Field(
        ..., description="ID of the role assigned to the user within this event"
    )
    event_id: UUID4 = Field(
        ..., description="ID of the event the user is enrolled in"
    )

    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class EventsUserCreate(DBBaseCreate):
    """Payload for enrolling a user in an event with a specific role."""

    user_id: UUID4 = Field(..., description="ID of the user to enroll")
    role_id: UUID4 = Field(
        ..., description="ID of the role to assign to the user in this event"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "00000000-0000-0000-0000-000000000001",
                "role_id": "00000000-0000-0000-0000-000000000002",
            }
        }
    )


class EventsUserInDBBase(EventsUserBase):
    """Internal event-user schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class EventsUser(EventsUserInDBBase):
    """Full event-user enrollment response schema."""

    model_config = ConfigDict(from_attributes=True)


# List object of EventsUser
class EventsUserList(BaseModel):
    """Paginated list of event-user enrollment objects."""

    pageDetails: PaginationPageDetails
    items: list[EventsUser]
