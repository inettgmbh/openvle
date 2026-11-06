from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails
from .object_permissions import ObjectPermissionForRole


# Role base
class RoleBase(DBBase):
    """Base schema for role objects with name and description fields."""

    name: str | None = Field(None, description="Display name of the role")
    description: str | None = Field(
        None, description="Optional description of the role"
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class RoleCreate(DBBaseCreate):
    """Payload for creating a new role."""

    name: str = Field(..., description="Display name of the role")
    description: str | None = Field(
        None, description="Optional description of the role"
    )
    protected: bool = Field(
        False, description="If true, the role cannot be deleted"
    )
    key: str = Field(
        ..., description="Unique machine-readable key for the role"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Studierender",
                "description": "Standardrolle für Studierende",
                "protected": False,
                "key": "studierende",
            }
        }
    )


# Properties to receive via API on update
class RoleUpdate(DBBaseUpdate):
    """Payload for updating an existing role's name or description."""

    name: str | None = Field(None, description="Display name of the role")
    description: str | None = Field(
        None, description="Optional description of the role"
    )


# Properties to receive via API on update ObjectPermissions
class RoleUpdateObjectPermissions(BaseModel):
    """Payload for replacing the object permissions assigned to a role."""

    object_permissions: list[UUID4] = Field(
        ..., description="List of object permission IDs to assign to the role"
    )


class RoleInDBBase(RoleBase):
    """Internal role schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Role(RoleInDBBase):
    """Full role response schema including key, protection flag, and permissions."""

    key: str = Field(
        ..., description="Unique machine-readable key for the role"
    )
    protected: bool | None = Field(
        None, description="If true, the role cannot be deleted"
    )
    object_permissions: list[ObjectPermissionForRole] | None = Field(
        None, description="Object permissions assigned to this role"
    )
    model_config = ConfigDict(from_attributes=True)


# Class used for when Role is to appear as a nested model and will only display key
class RoleNested(DBBaseUpdate):
    """Minimal role schema for nested references, shows key and name."""

    key: str = Field(
        ..., description="Unique machine-readable key for the role"
    )
    name: str = Field(..., description="Display name of the role")

    model_config = ConfigDict(from_attributes=True)


# Class used for when Role is to appear as a nested model and will only display key
class RoleKeyOnly(DBBaseUpdate):
    """Minimal role schema for nested references, shows key only."""

    key: str = Field(
        ..., description="Unique machine-readable key for the role"
    )

    model_config = ConfigDict(from_attributes=True)


# List object of Role
class RoleList(BaseModel):
    """Paginated list of role objects."""

    pageDetails: PaginationPageDetails
    items: list[Role]
