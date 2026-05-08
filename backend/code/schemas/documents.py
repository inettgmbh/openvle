from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base Document class
class DocumentBase(DBBase):
    name: str | None = None
    description: str | None = None
    path: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class DocumentCreate(DBBaseCreate):
    name: str
    description: str | None = None


# Properties to receive via API on UPDATE
class DocumentUpdate(DBBaseCreate):
    description: str | None = None


class DocumentInDBBase(DocumentBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Document(DocumentInDBBase):
    name: str
    description: str | None = None
    path: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Class used for when Document is to appear as a nested model and will only display ID
class DocumentNested(DBBaseUpdate):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# List object of Document
class DocumentList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Document]


# Allowed MIME/Media types
allowed_mime_types = [
    "application/pdf",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/epub+zip",
    "image/jpeg",
    "image/png",
    "image/x-png",
    "application/vnd.oasis.opendocument.text",
    "application/vnd.oasis.opendocument.spreadsheet",
    "application/vnd.oasis.opendocument.presentation",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/rtf",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
    "application/vnd.openxmlformats-officedocument.presentationml.template",
    "application/vnd.ms-access",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
]
