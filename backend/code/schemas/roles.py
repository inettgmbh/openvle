from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails
from .object_permissions import ObjectPermissionForRole


# Role base
class RoleBase(DBBase):
    name: str | None = None
    description: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class RoleCreate(DBBaseCreate):
    name: str
    description: str | None = None
    protected: bool = False
    key: str


# Properties to receive via API on update
class RoleUpdate(DBBaseUpdate):
    name: str | None = None
    description: str | None = None


# Properties to receive via API on update ObjectPermissions
class RoleUpdateObjectPermissions(BaseModel):
    object_permissions: list[UUID4]


class RoleInDBBase(RoleBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Role(RoleInDBBase):
    key: str
    protected: bool | None = None
    object_permissions: list[ObjectPermissionForRole] | None = None
    model_config = ConfigDict(from_attributes=True)


# Class used for when Role is to appear as a nested model and will only display key
class RoleNested(DBBaseUpdate):
    key: str
    name: str

    model_config = ConfigDict(from_attributes=True)


# Class used for when Role is to appear as a nested model and will only display key
class RoleKeyOnly(DBBaseUpdate):
    key: str

    model_config = ConfigDict(from_attributes=True)


# List object of Role
class RoleList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Role]
