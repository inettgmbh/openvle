from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, field_validator

from core.exceptions import InvalidFieldValue

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base GuacamoleConnectionProfile class
class GuacamoleConnectionProfileBase(DBBase):
    port: int | None = None
    protocol: str | None = None
    username: str | None = None
    objectId: UUID4 | None = None
    objectType: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class GuacamoleConnectionProfileCreate(DBBaseCreate):
    port: int = 3389
    protocol: str = "RDP"
    username: str | None = None
    password: str | None = None
    objectId: UUID4
    objectType: str

    # Validate Protocol field to only allow ["rdp", "vnc", "ssh", "k8s"] - Case insensitive
    @field_validator("protocol")
    @classmethod
    def gcp_protocol_validator(cls, val):
        CONNECTION_PROTOCOLS = ["rdp", "vnc", "ssh", "k8s"]
        if val.lower() not in CONNECTION_PROTOCOLS:
            raise InvalidFieldValue(
                field="protocol",
                value=val,
                supported_values=CONNECTION_PROTOCOLS,
            )
        return val

    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on cloning of another GCP
class GuacamoleConnectionProfileClone(DBBaseCreate):
    objectId: UUID4
    objectType: str
    port: None | int = 3389
    protocol: None | str = "RDP"
    username: str | None = None
    password: str | None = None

    # Validate Protocol field to only allow ["rdp", "vnc", "ssh", "k8s"] - Case insensitive
    @field_validator("protocol")
    @classmethod
    def gcp_protocol_validator(cls, val):
        CONNECTION_PROTOCOLS = ["rdp", "vnc", "ssh", "k8s"]
        if val.lower() not in CONNECTION_PROTOCOLS:
            raise InvalidFieldValue(
                field="protocol",
                value=val,
                supported_values=CONNECTION_PROTOCOLS,
            )
        return val

    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on update
class GuacamoleConnectionProfileUpdate(DBBaseUpdate):
    port: int | None = None
    protocol: str | None = None
    username: str | None = None
    password: str | None = None
    objectId: UUID4 | None = None
    objectType: str | None = None
    model_config = ConfigDict(from_attributes=True)


class GuacamoleConnectionProfileInDBBase(GuacamoleConnectionProfileBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class GuacamoleConnectionProfile(GuacamoleConnectionProfileInDBBase):
    model_config = ConfigDict(from_attributes=True)


# Returns only ID
class GuacamoleConnectionProfileIdOnly(DBBaseUpdate):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# List object of GuacamoleConnectionProfile
class GuacamoleConnectionProfileList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[GuacamoleConnectionProfile]
