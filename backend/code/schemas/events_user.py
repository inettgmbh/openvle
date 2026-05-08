from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base EventsUser class
class EventsUserBase(DBBase):
    user_id: UUID4
    role_id: UUID4
    event_id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class EventsUserCreate(DBBaseCreate):
    user_id: UUID4
    role_id: UUID4


class EventsUserInDBBase(EventsUserBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class EventsUser(EventsUserInDBBase):
    model_config = ConfigDict(from_attributes=True)


# List object of EventsUser
class EventsUserList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[EventsUser]
