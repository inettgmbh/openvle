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
    public = "public"
    authenticated = "authenticated"
    admins = "admins"
    internal = "internal"


class SystemSettingValueType(str, Enum):
    string = "string"
    integer = "integer"
    float = "float"
    boolean = "boolean"
    object = "object"
    array = "array"
    null = "null"


class SystemSettingCreate(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)

    @field_validator("visibility", mode="before")
    @classmethod
    def _normalize_visibility(cls, v):
        return v.lower() if isinstance(v, str) else v


class SystemSettingUpdate(DBBaseUpdate):
    value: JSONValue = Field(
        None,
        description="Updated JSON value",
        examples=["new-value"],
    )

    model_config = ConfigDict(from_attributes=True)


class SystemSettingBase(DBBase):
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
    id: UUID4  # type: ignore

    model_config = ConfigDict(from_attributes=True)  # type: ignore


class SystemSetting(SystemSettingInDBBase):
    model_config = ConfigDict(from_attributes=True)  # type: ignore


class SystemSettingList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[SystemSetting]


class SystemSettingWithoutAudit(BaseModel):
    key: str
    value: JSONValue
    type: SystemSettingValueType

    model_config = ConfigDict(from_attributes=True)


class SystemSettingWithoutAuditList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[SystemSettingWithoutAudit]
