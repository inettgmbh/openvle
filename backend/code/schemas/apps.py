from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails
from .documents import Document, DocumentNested


# Applications base
class ApplicationBase(DBBase):
    """Base schema for software application objects tracked in the system."""

    name: str | None = Field(
        None, description="Display name of the application"
    )
    patch_level: str | None = Field(
        None,
        description="Current patch level or version string of the application",
    )
    description: str | None = Field(
        None, description="Optional description of the application"
    )
    vendor: UUID4 | None = Field(
        "", description="ID of the vendor that supplies this application"
    )

    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class ApplicationCreate(DBBaseCreate):
    """Payload for creating a new application entry."""

    name: str = Field(..., description="Display name of the application")
    patch_level: str | None = Field(
        None,
        description="Current patch level or version string of the application",
    )
    key: str = Field(
        ..., description="Unique machine-readable key for the application"
    )
    description: str | None = Field(
        None, description="Optional description of the application"
    )
    vendor: UUID4 = Field(
        "", description="ID of the vendor that supplies this application"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Visual Studio Code",
                "patch_level": "1.85.0",
                "key": "vscode",
                "description": "Visual Studio Code Editor",
                "vendor": "00000000-0000-0000-0000-000000000001",
            }
        }
    )


# Properties to receive via API on update
class ApplicationUpdate(DBBaseUpdate):
    """Payload for updating an existing application's details."""

    name: str | None = Field(
        None, description="Display name of the application"
    )
    description: str | None = Field(
        None, description="Optional description of the application"
    )
    vendor: UUID4 | None = Field(
        None, description="ID of the vendor that supplies this application"
    )


# Properties to receive via API to update documents
class ApplicationUpdateDocuments(DBBaseUpdate):
    """Payload for replacing the documents linked to an application."""

    documents: list[DocumentNested] | None = Field(
        None, description="List of document IDs to assign to the application"
    )


class ApplicationInDBBase(ApplicationBase):
    """Internal application schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Application(ApplicationInDBBase):
    """Full application response schema including key and linked documents."""

    key: str = Field(
        ..., description="Unique machine-readable key for the application"
    )
    documents: list[Document]

    model_config = ConfigDict(from_attributes=True)


# Class used for when Application is to appear as a nested model and will only display key
class ApplicationNested(DBBaseUpdate):
    """Minimal application schema for nested references, shows key only."""

    key: str = Field(
        ..., description="Unique machine-readable key for the application"
    )

    model_config = ConfigDict(from_attributes=True)


# List object of Apps
class ApplicationList(BaseModel):
    """Paginated list of application objects."""

    pageDetails: PaginationPageDetails
    items: list[Application]
