from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator

from core.exceptions import InvalidFieldValue

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base GuacamoleConnectionProfile class
class GuacamoleConnectionProfileBase(DBBase):
    """Base schema for Guacamole connection profile objects."""

    port: int | None = Field(
        None, description="Port to connect to on the remote host"
    )
    protocol: str | None = Field(
        None, description="Remote desktop protocol. One of: rdp, vnc, ssh, k8s"
    )
    username: str | None = Field(
        None,
        description="Username for authenticating the remote desktop session",
    )
    objectId: UUID4 | None = Field(
        None,
        description="ID of the object this connection profile is attached to",
    )
    objectType: str | None = Field(
        None,
        description="Type of the object this connection profile is attached to",
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class GuacamoleConnectionProfileCreate(DBBaseCreate):
    """Payload for creating a new Guacamole connection profile."""

    port: int = Field(
        3389,
        description="Port to connect to on the remote host (default 3389 for RDP)",
    )
    protocol: str = Field(
        "RDP", description="Remote desktop protocol. One of: rdp, vnc, ssh, k8s"
    )
    username: str | None = Field(
        None,
        description="Username for authenticating the remote desktop session",
    )
    password: str | None = Field(
        None,
        description="Password for authenticating the remote desktop session",
    )
    objectId: UUID4 = Field(
        ..., description="ID of the object to attach this connection profile to"
    )
    objectType: str = Field(
        ...,
        description="Type of the object to attach this connection profile to",
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "port": 3389,
                "protocol": "RDP",
                "username": "administrator",
                "password": None,
                "objectId": "00000000-0000-0000-0000-000000000001",
                "objectType": "VirtualMachine",
            }
        },
    )


# Properties to receive via API on cloning of another GCP
class GuacamoleConnectionProfileClone(DBBaseCreate):
    """Payload for cloning an existing Guacamole connection profile onto a new object."""

    objectId: UUID4 = Field(
        ...,
        description="ID of the target object to attach the cloned profile to",
    )
    objectType: str = Field(..., description="Type of the target object")
    port: int | None = Field(
        3389,
        description="Port to connect to on the remote host (default 3389 for RDP)",
    )
    protocol: str | None = Field(
        "RDP", description="Remote desktop protocol. One of: rdp, vnc, ssh, k8s"
    )
    username: str | None = Field(
        None,
        description="Username for authenticating the remote desktop session",
    )
    password: str | None = Field(
        None,
        description="Password for authenticating the remote desktop session",
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "objectId": "00000000-0000-0000-0000-000000000001",
                "objectType": "VirtualMachine",
                "port": 3389,
                "protocol": "RDP",
                "username": "administrator",
                "password": None,
            }
        },
    )


# Properties to receive via API on update
class GuacamoleConnectionProfileUpdate(DBBaseUpdate):
    """Payload for updating an existing Guacamole connection profile."""

    port: int | None = Field(
        None, description="Port to connect to on the remote host"
    )
    protocol: str | None = Field(
        None, description="Remote desktop protocol. One of: rdp, vnc, ssh, k8s"
    )
    username: str | None = Field(
        None,
        description="Username for authenticating the remote desktop session",
    )
    password: str | None = Field(
        None,
        description="Password for authenticating the remote desktop session",
    )
    objectId: UUID4 | None = Field(
        None,
        description="ID of the object this connection profile is attached to",
    )
    objectType: str | None = Field(
        None,
        description="Type of the object this connection profile is attached to",
    )
    model_config = ConfigDict(from_attributes=True)


class GuacamoleConnectionProfileInDBBase(GuacamoleConnectionProfileBase):
    """Internal Guacamole connection profile schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class GuacamoleConnectionProfile(GuacamoleConnectionProfileInDBBase):
    """Full Guacamole connection profile response schema."""

    model_config = ConfigDict(from_attributes=True)


# Returns only ID
class GuacamoleConnectionProfileIdOnly(DBBaseUpdate):
    """Minimal Guacamole connection profile schema returning only the UUID."""

    id: UUID4 = Field(
        ..., description="Unique identifier of the Guacamole connection profile"
    )

    model_config = ConfigDict(from_attributes=True)


# List object of GuacamoleConnectionProfile
class GuacamoleConnectionProfileList(BaseModel):
    """Paginated list of Guacamole connection profile objects."""

    pageDetails: PaginationPageDetails
    items: list[GuacamoleConnectionProfile]
