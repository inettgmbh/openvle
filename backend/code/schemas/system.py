from enum import Enum
from typing import Annotated, Any

from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)

from .base import DBBase, DBBaseUpdate, PaginationPageDetails

JSONValue = str | int | float | bool | None | dict[str, Any] | list[Any]


class SystemSettingVisibility(str, Enum):
    """Enumeration of visibility levels for system settings."""

    public = "public"
    authenticated = "authenticated"
    admins = "admins"
    internal = "internal"


class SystemSettingValueType(str, Enum):
    """Enumeration of supported JSON value types for system settings."""

    string = "string"
    integer = "integer"
    float = "float"
    boolean = "boolean"
    object = "object"
    array = "array"
    null = "null"


class SystemSettingCreate(BaseModel):
    """Payload for creating a new system setting key-value entry."""

    key: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=1, pattern=r"^[a-z0-9_.-]+$"
        ),
    ] = Field(
        ..., max_length=250, description="Unique key, e.g. 'feature.flags.beta'"
    )
    value: JSONValue = Field(
        None,
        description="Any JSON-compatible value",
    )
    description: str | None = Field(
        None, max_length=1000, description="Any description of the setting"
    )
    visibility: SystemSettingVisibility = Field(
        ..., description="Setting visibility level"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "key": "feature.maintenance.mode",
                "value": "false",
                "description": "Aktiviert oder deaktiviert den Wartungsmodus",
                "visibility": "admins",
            }
        },
    )

    @field_validator("visibility", mode="before")
    @classmethod
    def _normalize_visibility(cls, v):
        return v.lower() if isinstance(v, str) else v


class SystemSettingUpdate(DBBaseUpdate):
    """Payload for updating the value of an existing system setting."""

    value: JSONValue = Field(
        None,
        description="Updated JSON value",
        examples=["new-value"],
    )

    model_config = ConfigDict(from_attributes=True)


class SystemSettingBase(DBBase):
    """Base schema for system setting objects with key, value, and visibility."""

    key: Annotated[
        str,
        Field(
            max_length=250, description="Unique key, e.g. 'feature.flags.beta'"
        ),
    ]
    value: Annotated[
        JSONValue,
        Field(
            description="Any JSON-compatible value",
        ),
    ]
    description: Annotated[
        str,
        Field(max_length=1000, description="Any description of the setting"),
    ]
    visibility: SystemSettingVisibility = Field(
        ..., description="Visibility of the setting"
    )
    type: SystemSettingValueType = Field(
        ..., description="Data type of the value field"
    )

    model_config = ConfigDict(from_attributes=True)


class SystemSettingInDBBase(SystemSettingBase):
    """Internal system setting schema with required ID field."""

    id: UUID4  # type: ignore

    model_config = ConfigDict(from_attributes=True)  # type: ignore


class SystemSetting(SystemSettingInDBBase):
    """Full system setting response schema."""

    model_config = ConfigDict(from_attributes=True)  # type: ignore


class SystemSettingList(BaseModel):
    """Paginated list of system setting objects."""

    pageDetails: PaginationPageDetails
    items: list[SystemSetting]


class SystemSettingWithoutAudit(BaseModel):
    """System setting schema without audit fields, for public/authenticated responses."""

    key: str
    value: JSONValue
    type: SystemSettingValueType

    model_config = ConfigDict(from_attributes=True)


class SystemSettingWithoutAuditList(BaseModel):
    """Paginated list of system settings without audit fields."""

    pageDetails: PaginationPageDetails
    items: list[SystemSettingWithoutAudit]
