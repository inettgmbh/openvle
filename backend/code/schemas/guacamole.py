from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base Guacamole class
class GuacamoleBase(DBBase):
    """Base schema for Guacamole remote desktop connection objects."""

    name: str | None = Field(
        None, description="Display name of the Guacamole connection"
    )
    description: str | None = Field(
        None, description="Optional description of the Guacamole connection"
    )
    guacd_hostname: str | None = Field(
        None, description="Hostname or IP of the guacd daemon"
    )
    guacd_port: int | None = Field(
        4822, description="Port the guacd daemon listens on (default 4822)"
    )
    guacd_encryption: bool | None = Field(
        True,
        description="Whether TLS encryption is used for the guacd connection",
    )
    userId: UUID4 | None = Field(
        None, description="ID of the user this Guacamole connection belongs to"
    )
    eventId: UUID4 | None = Field(
        None,
        description="ID of the event this Guacamole connection is scoped to",
    )

    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class GuacamoleCreate(DBBaseCreate):
    """Payload for creating a new Guacamole remote desktop connection."""

    name: str = Field(
        ..., description="Display name of the Guacamole connection"
    )
    description: str | None = Field(
        None, description="Optional description of the Guacamole connection"
    )
    guacd_hostname: str | None = Field(
        None, description="Hostname or IP of the guacd daemon"
    )
    guacd_port: int = Field(
        4822, description="Port the guacd daemon listens on (default 4822)"
    )
    guacd_encryption: bool = Field(
        True,
        description="Whether TLS encryption is used for the guacd connection",
    )
    connection_profile: UUID4 = Field(
        ..., description="ID of the Guacamole connection profile to use"
    )
    userId: UUID4 = Field(
        ..., description="ID of the user this Guacamole connection belongs to"
    )
    eventId: UUID4 | None = Field(
        None,
        description="ID of the event this Guacamole connection is scoped to",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "RDP-Verbindung Student-01",
                "description": "RDP-Verbindung zur Student-VM",
                "guacd_hostname": None,
                "guacd_port": 4822,
                "guacd_encryption": True,
                "connection_profile": "00000000-0000-0000-0000-000000000001",
                "userId": "00000000-0000-0000-0000-000000000002",
                "eventId": None,
            }
        },
    )


# Properties to receive via API on update
class GuacamoleUpdate(DBBaseUpdate):
    """Payload for updating an existing Guacamole connection."""

    name: str | None = Field(
        None, description="Display name of the Guacamole connection"
    )
    description: str | None = Field(
        None, description="Optional description of the Guacamole connection"
    )
    guacd_hostname: str | None = Field(
        None, description="Hostname or IP of the guacd daemon"
    )
    guacd_port: int | None = Field(
        4822, description="Port the guacd daemon listens on (default 4822)"
    )
    guacd_encryption: bool | None = Field(
        True,
        description="Whether TLS encryption is used for the guacd connection",
    )

    model_config = ConfigDict(from_attributes=True)


class GuacamoleInDBBase(GuacamoleBase):
    """Internal Guacamole schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


class VirtualMachineGuacamoleNested(DBBaseUpdate):
    """Minimal virtual machine schema as used in Guacamole nested responses."""

    id: UUID4 = Field(
        ..., description="Unique identifier of the virtual machine"
    )
    name: str = Field(..., description="Display name of the virtual machine")
    proxmoxId: int | None = Field(None, description="Proxmox VM ID")
    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Guacamole(GuacamoleInDBBase):
    """Full Guacamole response schema including identifier and linked VMs."""

    identifier: int | None = Field(
        None,
        description="Numeric identifier of the connection in the Guacamole server",
    )
    connection_profile: UUID4 = Field(
        ..., description="ID of the Guacamole connection profile used"
    )
    vms: list[VirtualMachineGuacamoleNested] | None = Field(
        None, description="Virtual machines linked to this Guacamole connection"
    )
    model_config = ConfigDict(from_attributes=True)


# Returns only ID
class GuacamoleIdOnly(DBBaseUpdate):
    """Minimal Guacamole schema returning only the UUID."""

    id: UUID4 = Field(
        ..., description="Unique identifier of the Guacamole connection"
    )

    model_config = ConfigDict(from_attributes=True)


# List object of Guacamole
class GuacamoleList(BaseModel):
    """Paginated list of Guacamole connection objects."""

    pageDetails: PaginationPageDetails
    items: list[Guacamole]
