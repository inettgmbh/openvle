import re

from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator

from core.exceptions import InvalidFieldValue

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base Tag class
class TagBase(DBBase):
    """Base schema for tag objects that can be attached to any resource."""

    key: str | None = Field(
        None,
        description="Tag key (lowercase alphanumeric and hyphens, no leading/trailing hyphens)",
    )
    value: str | None = Field(
        None,
        description="Tag value (lowercase alphanumeric and hyphens, no leading/trailing hyphens)",
    )
    objectId: UUID4 | None = Field(
        None, description="ID of the object this tag is attached to"
    )
    objectType: str | None = Field(
        None,
        description="Type of the object this tag is attached to, e.g. VirtualMachine",
    )
    description: str | None = Field(
        None, description="Optional description of the tag"
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class TagCreate(DBBaseCreate):
    """Payload for creating a new tag on a resource."""

    key: str = Field(
        ...,
        description="Tag key (lowercase alphanumeric and hyphens, no leading/trailing hyphens)",
    )
    value: str = Field(
        ...,
        description="Tag value (lowercase alphanumeric and hyphens, no leading/trailing hyphens)",
    )
    objectId: UUID4 = Field(
        ..., description="ID of the object to attach this tag to"
    )
    objectType: str = Field(
        ...,
        description="Type of the object to attach this tag to, e.g. VirtualMachine",
    )
    description: str | None = Field(
        None, description="Optional description of the tag"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "pool",
                "value": "pool-a",
                "objectId": "00000000-0000-0000-0000-000000000001",
                "objectType": "VirtualMachine",
                "description": "VM Pool A",
            }
        }
    )

    @field_validator("key", "value")
    @classmethod
    def validate_no_invalid_chars(cls, v: str, info):
        pattern = re.compile(r"^(?!-)[a-z0-9-]+(?<!-)$")
        if not pattern.match(v):
            raise InvalidFieldValue(
                field=info.field_name,
                value=v,
                supported_values="Numbers, lower-case letters and '-' (not at start or end).",
            )
        return v


class TagInDBBase(TagBase):
    """Internal tag schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Tag(TagInDBBase):
    """Full tag response schema."""

    key: str
    value: str
    objectId: UUID4
    objectType: str

    model_config = ConfigDict(from_attributes=True)


# Class used for when Tag is to appear as a nested model and will only display ID
class TagNested(DBBaseUpdate):
    """Minimal tag schema for nested references, shows ID only."""

    id: UUID4 = Field(..., description="Unique identifier of the tag")

    model_config = ConfigDict(from_attributes=True)


# List object of Tag
class TagList(BaseModel):
    """Paginated list of tag objects."""

    pageDetails: PaginationPageDetails
    items: list[Tag]
