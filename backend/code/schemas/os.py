from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails
from .documents import Document, DocumentNested


# Base OS class
class OSBase(DBBase):
    """Base schema for operating system objects tracked in the system."""

    name: str | None = Field(
        None, description="Display name of the operating system"
    )
    patch_level: str | None = Field(
        None, description="Current patch level or service pack of the OS"
    )
    description: str | None = Field(
        None, description="Optional description of the operating system"
    )
    vendor: UUID4 | None = Field(
        "", description="ID of the vendor that publishes this OS"
    )
    version: str | None = Field(
        None, description="Version string of the operating system, e.g. 22.04"
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class OSCreate(DBBaseCreate):
    """Payload for creating a new operating system entry."""

    name: str = Field(..., description="Display name of the operating system")
    patch_level: str | None = Field(
        None, description="Current patch level or service pack of the OS"
    )
    key: str = Field(..., description="Unique machine-readable key for the OS")
    description: str | None = Field(
        None, description="Optional description of the operating system"
    )
    version: str = Field(
        ..., description="Version string of the operating system, e.g. 22.04"
    )
    vendor: UUID4 = Field(
        "", description="ID of the vendor that publishes this OS"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Ubuntu 22.04 LTS",
                "patch_level": "22.04.3",
                "key": "ubuntu-22-04",
                "description": "Ubuntu 22.04 LTS Server",
                "version": "22.04",
                "vendor": "00000000-0000-0000-0000-000000000001",
            }
        }
    )


# Properties to receive via API on update
class OSUpdate(DBBaseUpdate):
    """Payload for updating an existing operating system entry."""

    name: str | None = Field(
        None, description="Display name of the operating system"
    )
    description: str | None = Field(
        None, description="Optional description of the operating system"
    )
    version: str | None = Field(
        None, description="Version string of the operating system, e.g. 22.04"
    )
    vendor: UUID4 | None = Field(
        None, description="ID of the vendor that publishes this OS"
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API to update documents
class OSUpdateDocuments(DBBaseUpdate):
    """Payload for replacing the documents linked to an OS."""

    documents: list[DocumentNested] | None = Field(
        None, description="List of document IDs to assign to the OS"
    )


class OSInDBBase(OSBase):
    """Internal OS schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class OS(OSInDBBase):
    """Full operating system response schema including key and linked documents."""

    key: str = Field(..., description="Unique machine-readable key for the OS")
    documents: list[Document]

    model_config = ConfigDict(from_attributes=True)


# Class used for when OS is to appear as a nested model and will only display Title
class OSNested(DBBaseUpdate):
    """Minimal OS schema for nested references, shows key only."""

    key: str = Field(..., description="Unique machine-readable key for the OS")

    model_config = ConfigDict(from_attributes=True)


# List object of OS
class OSList(BaseModel):
    """Paginated list of operating system objects."""

    pageDetails: PaginationPageDetails
    items: list[OS]
