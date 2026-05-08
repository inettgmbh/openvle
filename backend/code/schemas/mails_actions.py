from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base MailAction class
class MailActionBase(DBBase):
    name: str | None = None
    description: str | None = None
    slug: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class MailActionCreate(DBBaseCreate):
    name: str
    description: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class MailActionInDBBase(MailActionBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class MailAction(MailActionInDBBase):
    model_config = ConfigDict(from_attributes=True)


# Class used for when MailAction is to appear as a nested model and will only display ID
class MailActionNested(DBBaseUpdate):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# List object of MailAction
class MailActionList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[MailAction]
