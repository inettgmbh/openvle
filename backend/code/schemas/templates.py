from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, field_validator

from core.core_utils import sanitize_dns_name
from core.exceptions import InvalidFieldValue

from .apps import ApplicationNested as Application
from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base Template class
class TemplateBase(DBBase):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    proxmoxNode: str | None = None
    proxmoxId: int | None = None
    cpu: int | None = None
    ram: int | None = None
    disk: int | None = None
    os: UUID4 | None = None
    prevent_delete: bool | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class TemplateCreate(DBBaseCreate):
    source_vm: UUID4
    name: str
    description: str | None = None
    cpu: int
    ram: int
    disk: int
    prevent_delete: bool | None = False

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
class TemplateUpdate(DBBaseUpdate):
    name: str | None = None
    description: str | None = None
    cpu: int | None = None
    ram: int | None = None
    os: UUID4 | None = None
    prevent_delete: bool | None = None

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
    apps: list[Application] | None = None


class TemplateInDBBase(TemplateBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Template(TemplateInDBBase):
    status: str | None = None
    apps: list[Application] | None = None
    os: UUID4 | None = None
    proxmoxNode: str | None = None
    proxmoxId: int | None = None
    model_config = ConfigDict(from_attributes=True)


# Additional properties to return via API
class TemplateIdOnly(DBBaseUpdate):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Additional properties to return via API
class TemplateNested(DBBaseUpdate):
    name: str

    model_config = ConfigDict(from_attributes=True)


# List object of Template
class TemplateList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Template]
