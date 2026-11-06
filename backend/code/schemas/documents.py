from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base Document class
class DocumentBase(DBBase):
    """Base schema for document/file objects uploaded to the system."""

    name: str | None = Field(None, description="Display name of the document")
    description: str | None = Field(
        None, description="Optional description of the document"
    )
    path: str | None = Field(
        None, description="Storage path of the uploaded file"
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class DocumentCreate(DBBaseCreate):
    """Payload for uploading and creating a new document."""

    name: str = Field(..., description="Display name of the document")
    description: str | None = Field(
        None, description="Optional description of the document"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Installationsanleitung",
                "description": "Installationsanleitung für das System",
            }
        }
    )


# Properties to receive via API on UPDATE
class DocumentUpdate(DBBaseCreate):
    """Payload for updating an existing document's description."""

    description: str | None = Field(
        None, description="Updated description of the document"
    )


class DocumentInDBBase(DocumentBase):
    """Internal document schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Document(DocumentInDBBase):
    """Full document response schema including storage path."""

    name: str
    description: str | None = None
    path: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Class used for when Document is to appear as a nested model and will only display ID
class DocumentNested(DBBaseUpdate):
    """Minimal document schema for nested references, shows ID only."""

    id: UUID4 = Field(..., description="Unique identifier of the document")

    model_config = ConfigDict(from_attributes=True)


# List object of Document
class DocumentList(BaseModel):
    """Paginated list of document objects."""

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
