from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base MailAction class
class MailActionBase(DBBase):
    """Base schema for mail action objects that trigger automated emails."""

    name: str | None = Field(
        None, description="Display name of the mail action"
    )
    description: str | None = Field(
        None, description="Optional description of the mail action"
    )
    slug: str | None = Field(
        None,
        description="Unique machine-readable slug identifying the mail action trigger",
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class MailActionCreate(DBBaseCreate):
    """Payload for creating a new mail action trigger."""

    name: str = Field(..., description="Display name of the mail action")
    description: str = Field(
        ...,
        description="Description of when and why this mail action is triggered",
    )
    slug: str = Field(
        ...,
        description="Unique machine-readable slug identifying the mail action trigger",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "Benutzerregistrierung",
                "description": "Wird ausgelöst, wenn sich ein neuer Benutzer registriert",
                "slug": "user_registered",
            }
        },
    )


class MailActionInDBBase(MailActionBase):
    """Internal mail action schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class MailAction(MailActionInDBBase):
    """Full mail action response schema."""

    model_config = ConfigDict(from_attributes=True)


# Class used for when MailAction is to appear as a nested model and will only display ID
class MailActionNested(DBBaseUpdate):
    """Minimal mail action schema for nested references, shows ID only."""

    id: UUID4 = Field(..., description="Unique identifier of the mail action")

    model_config = ConfigDict(from_attributes=True)


# List object of MailAction
class MailActionList(BaseModel):
    """Paginated list of mail action objects."""

    pageDetails: PaginationPageDetails
    items: list[MailAction]
