from pydantic import UUID4, BaseModel, ConfigDict, field_validator

from core.core_utils import sanitize_dns_name
from core.exceptions import InvalidFieldValue

from .apps import ApplicationNested as Application
from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails
from .guacamole import Guacamole


# Base VirtualMachine class
class VirtualMachineBase(DBBase):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    cpu: int | None = None
    ram: int | None = None
    disk: int | None = None
    os: UUID4 | None = None
    template: UUID4 | None = None
    prevent_delete: bool | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class VirtualMachineCreate(DBBaseCreate):
    name: str
    description: str | None = None
    cpu: int
    ram: int
    template: UUID4
    prevent_delete: bool | None = False
    create_guacamole: bool = False

    # Validate name field according to Proxmox limitations
    @field_validator("name")
    @classmethod
    def pve_name_validation(cls, val):
        return sanitize_dns_name(val)

    # Validate description field according to Proxmox limitations
    @field_validator("description")
    @classmethod
    def pve_description_validation(cls, val):
        return val[:999]

    # Validate CPU field according to Proxmox limitations
    @field_validator("cpu")
    @classmethod
    def pve_cpu_validation(cls, val):
        if val < 1 or val > 24:
            raise InvalidFieldValue(
                field="cpu",
                value=val,
                supported_values="Any value ranging from 1 to 24.",
            )
        return val

    # Validate RAM field according to Proxmox limitations
    @field_validator("ram")
    @classmethod
    def pve_ram_validation(cls, val):
        if val < 1024 or val > 268270:
            raise InvalidFieldValue(
                field="ram",
                value=val,
                supported_values="Any value ranging from 1024 to 268270.",
            )
        return val

    model_config = ConfigDict(from_attributes=True)


# Parameters to be used when a VirtualMachine is created for an Event
class VirtualMachineEventCreate(VirtualMachineCreate):
    event: UUID4
    user: UUID4


# Properties to receive via API on clone
class VirtualMachineClone(DBBaseCreate):
    name: str
    description: str | None = None
    cpu: int
    ram: int
    prevent_delete: bool | None = False
    create_guacamole: bool = False

    # Validate name field according to Proxmox limitations
    @field_validator("name")
    @classmethod
    def pve_name_validation(cls, val):
        return sanitize_dns_name(val)

    # Validate description field according to Proxmox limitations
    @field_validator("description")
    @classmethod
    def pve_description_validation(cls, val):
        return val[:999]

    # Validate CPU field according to Proxmox limitations
    @field_validator("cpu")
    @classmethod
    def pve_cpu_validation(cls, val):
        if val < 1 or val > 24:
            raise InvalidFieldValue(
                field="cpu",
                value=val,
                supported_values="Any value ranging from 1 to 24.",
            )
        return val

    # Validate RAM field according to Proxmox limitations
    @field_validator("ram")
    @classmethod
    def pve_ram_validation(cls, val):
        if val < 1024 or val > 268270:
            raise InvalidFieldValue(
                field="ram",
                value=val,
                supported_values="Any value ranging from 1024 to 268270.",
            )
        return val

    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on update
class VirtualMachineUpdate(DBBaseUpdate):
    name: str | None = None
    description: str | None = None
    cpu: int | None = None
    ram: int | None = None
    os: UUID4 | None = None
    prevent_delete: bool | None = False
    restart_vm: bool = False

    # Validate name field according to Proxmox limitations
    @field_validator("name")
    @classmethod
    def pve_name_validation(cls, val):
        return sanitize_dns_name(val)

    # Validate description field according to Proxmox limitations
    @field_validator("description")
    @classmethod
    def pve_description_validation(cls, val):
        return val[:999]

    # Validate CPU field according to Proxmox limitations
    @field_validator("cpu")
    @classmethod
    def pve_cpu_validation(cls, val):
        if val < 1 or val > 24:
            raise InvalidFieldValue(
                field="cpu",
                value=val,
                supported_values="Any value ranging from 1 to 24.",
            )
        return val

    # Validate RAM field according to Proxmox limitations
    @field_validator("ram")
    @classmethod
    def pve_ram_validation(cls, val):
        if val < 1024 or val > 268270:
            raise InvalidFieldValue(
                field="ram",
                value=val,
                supported_values="Any value ranging from 1024 to 268270.",
            )
        return val

    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on Migrate
class VirtualMachineMigrate(DBBaseUpdate):
    targetNode: str


# Properties to receive via API on HA_ADD
class VirtualMachineHaAdd(DBBaseUpdate):
    ha_state: str = "started"
    ha_max_restart: int = 5
    ha_max_relocate: int = 5


# Properties to receive via API on updateApps
class VirtualMachineUpdateApps(DBBaseUpdate):
    apps: list[Application] | None = None


class VirtualMachineInDBBase(VirtualMachineBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class VirtualMachine(VirtualMachineInDBBase):
    status: str | None = None
    template: UUID4 | None = None
    os: UUID4 | None = None
    proxmoxNode: str | None = None
    proxmoxId: int | None = None
    event: UUID4 | None = None
    ipv4: str | None = None
    apps: list[Application] | None = None
    guacamoles: list[Guacamole] | None = None
    model_config = ConfigDict(from_attributes=True)


# Class to used as nested response model
class VirtualMachineNested(DBBase):
    name: str | None = None
    status: str | None = None
    template: UUID4 | None = None
    proxmoxNode: str | None = None
    proxmoxId: int | None = None
    event: UUID4 | None = None
    prevent_delete: bool | None = None
    model_config = ConfigDict(from_attributes=True)


# Returns only ID
class VirtualMachineIdOnly(DBBaseUpdate):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Base class for VM based bulk actions
class VirtualMachineIdList(BaseModel):
    vms: list[UUID4] | None = None
    model_config = ConfigDict(from_attributes=True)


# Bulk schema for HA add
class VirtualMachineBulkHaAdd(VirtualMachineIdList):
    ha_state: str = "started"
    ha_max_restart: int = 5
    ha_max_relocate: int = 5

    model_config = ConfigDict(from_attributes=True)


# Bulk schema for migrate
class VirtualMachineBulkMigrate(VirtualMachineIdList):
    targetNode: str

    model_config = ConfigDict(from_attributes=True)


# List object of VirtualMachine
class VirtualMachineList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[VirtualMachine]


# List object of VirtualMachineNested
class VirtualMachineNestedList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[VirtualMachineNested]
