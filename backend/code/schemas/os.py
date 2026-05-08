from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails
from .documents import Document, DocumentNested


# Base OS class
class OSBase(DBBase):
    name: str | None = None
    patch_level: str | None = None
    description: str | None = None
    vendor: UUID4 | None = ""
    version: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class OSCreate(DBBaseCreate):
    name: str
    patch_level: str | None = None
    key: str
    description: str | None = None
    version: str
    vendor: UUID4 = ""


# Properties to receive via API on update
class OSUpdate(DBBaseUpdate):
    name: str | None = None
    description: str | None = None
    version: str | None = None
    vendor: UUID4 | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API to update documents
class OSUpdateDocuments(DBBaseUpdate):
    documents: list[DocumentNested] | None = None


class OSInDBBase(OSBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class OS(OSInDBBase):
    key: str
    documents: list[Document]

    model_config = ConfigDict(from_attributes=True)


# Class used for when OS is to appear as a nested model and will only display Title
class OSNested(DBBaseUpdate):
    key: str

    model_config = ConfigDict(from_attributes=True)


# List object of OS
class OSList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[OS]
