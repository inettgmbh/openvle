from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base Guacamole class
class GuacamoleBase(DBBase):
    name: str | None = None
    description: str | None = None
    guacd_hostname: str | None = None
    guacd_port: int | None = 4822
    guacd_encryption: bool | None = True
    userId: UUID4 | None = None
    eventId: UUID4 | None = None

    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class GuacamoleCreate(DBBaseCreate):
    name: str
    description: str | None = None
    guacd_hostname: str | None = None
    guacd_port: int = 4822
    guacd_encryption: bool = True
    connection_profile: UUID4
    userId: UUID4
    eventId: UUID4 | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on update
class GuacamoleUpdate(DBBaseUpdate):
    name: str | None = None
    description: str | None = None
    guacd_hostname: str | None = None
    guacd_port: int | None = 4822
    guacd_encryption: bool | None = True

    model_config = ConfigDict(from_attributes=True)


class GuacamoleInDBBase(GuacamoleBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


class VirtualMachineGuacamoleNested(DBBaseUpdate):
    id: UUID4
    name: str
    proxmoxId: int | None = None
    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Guacamole(GuacamoleInDBBase):
    identifier: int | None = None
    connection_profile: UUID4
    vms: list[VirtualMachineGuacamoleNested] | None = None
    model_config = ConfigDict(from_attributes=True)


# Returns only ID
class GuacamoleIdOnly(DBBaseUpdate):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# List object of Guacamole
class GuacamoleList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Guacamole]
