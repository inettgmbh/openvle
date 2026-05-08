from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails
from .documents import Document, DocumentNested


# Applications base
class ApplicationBase(DBBase):
    name: str | None = None
    patch_level: str | None = None
    description: str | None = None
    vendor: UUID4 | None = ""

    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class ApplicationCreate(DBBaseCreate):
    name: str
    patch_level: str | None = None
    key: str
    description: str | None = None
    vendor: UUID4 = ""


# Properties to receive via API on update
class ApplicationUpdate(DBBaseUpdate):
    name: str | None = None
    description: str | None = None
    vendor: UUID4 | None = None


# Properties to receive via API to update documents
class ApplicationUpdateDocuments(DBBaseUpdate):
    documents: list[DocumentNested] | None = None


class ApplicationInDBBase(ApplicationBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Application(ApplicationInDBBase):
    key: str
    documents: list[Document]

    model_config = ConfigDict(from_attributes=True)


# Class used for when Application is to appear as a nested model and will only display key
class ApplicationNested(DBBaseUpdate):
    key: str

    model_config = ConfigDict(from_attributes=True)


# List object of Apps
class ApplicationList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Application]
