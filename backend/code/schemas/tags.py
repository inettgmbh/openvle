import re

from pydantic import UUID4, BaseModel, ConfigDict, field_validator

from core.exceptions import InvalidFieldValue

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base Tag class
class TagBase(DBBase):
    key: str | None = None
    value: str | None = None
    objectId: UUID4 | None = None
    objectType: str | None = None
    description: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class TagCreate(DBBaseCreate):
    key: str
    value: str
    objectId: UUID4
    objectType: str
    description: str | None = None

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
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Tag(TagInDBBase):
    key: str
    value: str
    objectId: UUID4
    objectType: str

    model_config = ConfigDict(from_attributes=True)


# Class used for when Tag is to appear as a nested model and will only display ID
class TagNested(DBBaseUpdate):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# List object of Tag
class TagList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Tag]
