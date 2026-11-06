from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator

from core.core_utils import sanitize_dns_name
from core.exceptions import InvalidFieldValue

from .apps import ApplicationNested as Application
from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails
from .guacamole import Guacamole


# Base VirtualMachine class
class VirtualMachineBase(DBBase):
    """Base schema for virtual machine objects with hardware and status fields."""

    name: str | None = Field(
        None, description="Display name of the virtual machine"
    )
    description: str | None = Field(
        None, description="Optional description of the virtual machine"
    )
    status: str | None = Field(
        None,
        description="Current power/operational status of the VM in Proxmox",
    )
    cpu: int | None = Field(None, description="Number of vCPUs assigned (1-24)")
    ram: int | None = Field(
        None, description="RAM in MB assigned (1024-268270)"
    )
    disk: int | None = Field(
        None, description="Disk size in GB assigned to the VM"
    )
    os: UUID4 | None = Field(
        None, description="ID of the operating system associated with the VM"
    )
    template: UUID4 | None = Field(
        None, description="ID of the template the VM was cloned from"
    )
    prevent_delete: bool | None = Field(
        None, description="If true, deletion of this VM is blocked"
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class VirtualMachineCreate(DBBaseCreate):
    """Payload for creating a new virtual machine from a template."""

    name: str = Field(
        ...,
        description="Display name of the virtual machine (Proxmox DNS-safe)",
    )
    description: str | None = Field(
        None, description="Optional description of the VM (max 999 chars)"
    )
    cpu: int = Field(..., description="Number of vCPUs to assign (1-24)")
    ram: int = Field(..., description="RAM in MB to assign (1024-268270)")
    template: UUID4 = Field(
        ..., description="ID of the template to clone the VM from"
    )
    prevent_delete: bool | None = Field(
        False, description="If true, deletion of this VM is blocked"
    )
    create_guacamole: bool = Field(
        False,
        description="If true, a Guacamole connection is created for the VM",
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "vm-student-01",
                "description": "Student-VM für die Veranstaltung",
                "cpu": 2,
                "ram": 4096,
                "template": "00000000-0000-0000-0000-000000000001",
                "prevent_delete": False,
                "create_guacamole": True,
            }
        },
    )


# Parameters to be used when a VirtualMachine is created for an Event
class VirtualMachineEventCreate(VirtualMachineCreate):
    """Payload for creating a VM scoped to a specific event and user."""

    event: UUID4 = Field(..., description="ID of the event this VM belongs to")
    user: UUID4 = Field(
        ..., description="ID of the user this VM is assigned to"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "vm-student-01",
                "description": "Student-VM für die Veranstaltung",
                "cpu": 2,
                "ram": 4096,
                "template": "00000000-0000-0000-0000-000000000001",
                "prevent_delete": False,
                "create_guacamole": True,
                "event": "00000000-0000-0000-0000-000000000002",
                "user": "00000000-0000-0000-0000-000000000003",
            }
        },
    )


# Properties to receive via API on clone
class VirtualMachineClone(DBBaseCreate):
    """Payload for cloning a virtual machine."""

    name: str = Field(
        ..., description="Display name of the cloned VM (Proxmox DNS-safe)"
    )
    description: str | None = Field(
        None,
        description="Optional description of the cloned VM (max 999 chars)",
    )
    cpu: int = Field(..., description="Number of vCPUs to assign (1-24)")
    ram: int = Field(..., description="RAM in MB to assign (1024-268270)")
    prevent_delete: bool | None = Field(
        False, description="If true, deletion of this VM is blocked"
    )
    create_guacamole: bool = Field(
        False,
        description="If true, a Guacamole connection is created for the VM",
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "vm-student-01-klon",
                "description": "Klon der Student-VM",
                "cpu": 2,
                "ram": 4096,
                "prevent_delete": False,
                "create_guacamole": False,
            }
        },
    )


# Properties to receive via API on update
class VirtualMachineUpdate(DBBaseUpdate):
    """Payload for updating an existing virtual machine's configuration."""

    name: str | None = Field(
        None, description="Display name of the VM (Proxmox DNS-safe)"
    )
    description: str | None = Field(
        None, description="Optional description of the VM (max 999 chars)"
    )
    cpu: int | None = Field(
        None, description="Number of vCPUs to assign (1-24)"
    )
    ram: int | None = Field(
        None, description="RAM in MB to assign (1024-268270)"
    )
    os: UUID4 | None = Field(
        None, description="ID of the operating system associated with the VM"
    )
    prevent_delete: bool | None = Field(
        False, description="If true, deletion of this VM is blocked"
    )
    restart_vm: bool = Field(
        False, description="If true, the VM will be restarted after the update"
    )

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
    """Payload for migrating a virtual machine to a different Proxmox node."""

    targetNode: str = Field(
        ..., description="Name of the target Proxmox node to migrate the VM to"
    )


# Properties to receive via API on HA_ADD
class VirtualMachineHaAdd(DBBaseUpdate):
    """Payload for adding a virtual machine to Proxmox High Availability."""

    ha_state: str = Field(
        "started", description="Desired HA state for the VM, e.g. started"
    )
    ha_max_restart: int = Field(
        5, description="Maximum number of HA restart attempts"
    )
    ha_max_relocate: int = Field(
        5, description="Maximum number of HA relocation attempts"
    )


# Properties to receive via API on updateApps
class VirtualMachineUpdateApps(DBBaseUpdate):
    """Payload for replacing the applications linked to a virtual machine."""

    apps: list[Application] | None = Field(
        None, description="List of application keys to assign to the VM"
    )


class VirtualMachineInDBBase(VirtualMachineBase):
    """Internal virtual machine schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class VirtualMachine(VirtualMachineInDBBase):
    """Full virtual machine response schema including apps, Guacamole, and network info."""

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
    """Minimal virtual machine schema for nested references."""

    name: str | None = Field(
        None, description="Display name of the virtual machine"
    )
    status: str | None = Field(
        None, description="Current power/operational status of the VM"
    )
    template: UUID4 | None = Field(
        None, description="ID of the template the VM was cloned from"
    )
    proxmoxNode: str | None = Field(
        None, description="Proxmox node where the VM resides"
    )
    proxmoxId: int | None = Field(None, description="Proxmox VM ID")
    event: UUID4 | None = Field(
        None, description="ID of the event this VM belongs to"
    )
    prevent_delete: bool | None = Field(
        None, description="If true, deletion of this VM is blocked"
    )
    model_config = ConfigDict(from_attributes=True)


# Returns only ID
class VirtualMachineIdOnly(DBBaseUpdate):
    """Minimal virtual machine schema returning only the UUID."""

    id: UUID4 = Field(
        ..., description="Unique identifier of the virtual machine"
    )

    model_config = ConfigDict(from_attributes=True)


# Base class for VM based bulk actions
class VirtualMachineIdList(BaseModel):
    """Payload base for bulk actions targeting a list of virtual machines by ID."""

    vms: list[UUID4] | None = Field(
        None, description="List of virtual machine UUIDs to act on"
    )
    model_config = ConfigDict(from_attributes=True)


# Bulk schema for HA add
class VirtualMachineBulkHaAdd(VirtualMachineIdList):
    """Payload for adding multiple VMs to Proxmox High Availability in bulk."""

    ha_state: str = Field(
        "started", description="Desired HA state for the VMs, e.g. started"
    )
    ha_max_restart: int = Field(
        5, description="Maximum number of HA restart attempts"
    )
    ha_max_relocate: int = Field(
        5, description="Maximum number of HA relocation attempts"
    )

    model_config = ConfigDict(from_attributes=True)


# Bulk schema for migrate
class VirtualMachineBulkMigrate(VirtualMachineIdList):
    """Payload for bulk-migrating multiple VMs to a different Proxmox node."""

    targetNode: str = Field(
        ..., description="Name of the target Proxmox node to migrate VMs to"
    )

    model_config = ConfigDict(from_attributes=True)


# List object of VirtualMachine
class VirtualMachineList(BaseModel):
    """Paginated list of virtual machine objects."""

    pageDetails: PaginationPageDetails
    items: list[VirtualMachine]


# List object of VirtualMachineNested
class VirtualMachineNestedList(BaseModel):
    """Paginated list of nested virtual machine objects."""

    pageDetails: PaginationPageDetails
    items: list[VirtualMachineNested]
