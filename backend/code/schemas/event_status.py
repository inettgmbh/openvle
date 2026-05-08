from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base EventStatus class
class EventStatusBase(DBBase):
    name: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class EventStatusCreate(DBBaseCreate):
    name: str


# Properties to receive via API on update
class EventStatusUpdate(DBBaseUpdate):
    name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class EventStatusInDBBase(EventStatusBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class EventStatus(EventStatusInDBBase):
    name: str

    model_config = ConfigDict(from_attributes=True)


# Class used for when EventStatus is to appear as a nested model and will only display status
class EventStatusNested(DBBaseUpdate):
    name: str

    model_config = ConfigDict(from_attributes=True)


# List object of EventStatus
class EventStatusList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[EventStatus]
