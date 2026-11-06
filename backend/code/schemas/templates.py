from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator

from core.core_utils import sanitize_dns_name
from core.exceptions import InvalidFieldValue

from .apps import ApplicationNested as Application
from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base Template class
class TemplateBase(DBBase):
    """Base schema for VM template objects with hardware and status fields."""

    name: str | None = Field(None, description="Display name of the template")
    description: str | None = Field(
        None, description="Optional description of the template"
    )
    status: str | None = Field(
        None, description="Current status of the template in Proxmox"
    )
    proxmoxNode: str | None = Field(
        None, description="Proxmox node where the template resides"
    )
    proxmoxId: int | None = Field(
        None, description="Proxmox VM ID of the template"
    )
    cpu: int | None = Field(None, description="Number of vCPUs assigned (1-24)")
    ram: int | None = Field(
        None, description="RAM in MB assigned (1024-268270)"
    )
    disk: int | None = Field(
        None, description="Disk size in GB assigned to the template"
    )
    os: UUID4 | None = Field(
        None,
        description="ID of the operating system associated with the template",
    )
    prevent_delete: bool | None = Field(
        None, description="If true, deletion of this template is blocked"
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class TemplateCreate(DBBaseCreate):
    """Payload for creating a new VM template from an existing VM."""

    source_vm: UUID4 = Field(
        ...,
        description="ID of the source virtual machine to clone as a template",
    )
    name: str = Field(
        ..., description="Display name of the template (Proxmox DNS-safe)"
    )
    description: str | None = Field(
        None, description="Optional description of the template (max 999 chars)"
    )
    cpu: int = Field(..., description="Number of vCPUs to assign (1-24)")
    ram: int = Field(..., description="RAM in MB to assign (1024-268270)")
    disk: int = Field(
        ..., description="Disk size in GB to assign to the template"
    )
    prevent_delete: bool | None = Field(
        False, description="If true, deletion of this template is blocked"
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
                "source_vm": "00000000-0000-0000-0000-000000000001",
                "name": "ubuntu-22-04-base",
                "description": "Ubuntu 22.04 Basisvorlage",
                "cpu": 2,
                "ram": 4096,
                "disk": 32,
                "prevent_delete": True,
            }
        },
    )


# Properties to receive via API on update
class TemplateUpdate(DBBaseUpdate):
    """Payload for updating an existing VM template's configuration."""

    name: str | None = Field(
        None, description="Display name of the template (Proxmox DNS-safe)"
    )
    description: str | None = Field(
        None, description="Optional description of the template (max 999 chars)"
    )
    cpu: int | None = Field(
        None, description="Number of vCPUs to assign (1-24)"
    )
    ram: int | None = Field(
        None, description="RAM in MB to assign (1024-268270)"
    )
    os: UUID4 | None = Field(
        None,
        description="ID of the operating system associated with the template",
    )
    prevent_delete: bool | None = Field(
        None, description="If true, deletion of this template is blocked"
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


# Properties to receive via API on updateApps
class TemplateUpdateApps(DBBaseUpdate):
    """Payload for replacing the applications linked to a template."""

    apps: list[Application] | None = Field(
        None, description="List of application keys to assign to the template"
    )


class TemplateInDBBase(TemplateBase):
    """Internal template schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Template(TemplateInDBBase):
    """Full template response schema including status, apps, and Proxmox details."""

    status: str | None = None
    apps: list[Application] | None = None
    os: UUID4 | None = None
    proxmoxNode: str | None = None
    proxmoxId: int | None = None
    model_config = ConfigDict(from_attributes=True)


# Additional properties to return via API
class TemplateIdOnly(DBBaseUpdate):
    """Minimal template schema returning only the UUID."""

    id: UUID4 = Field(..., description="Unique identifier of the template")

    model_config = ConfigDict(from_attributes=True)


# Additional properties to return via API
class TemplateNested(DBBaseUpdate):
    """Minimal template schema for nested references, shows name only."""

    name: str = Field(..., description="Display name of the template")

    model_config = ConfigDict(from_attributes=True)


# List object of Template
class TemplateList(BaseModel):
    """Paginated list of template objects."""

    pageDetails: PaginationPageDetails
    items: list[Template]
