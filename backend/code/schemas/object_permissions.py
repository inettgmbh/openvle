from enum import Enum

from pydantic import UUID4, BaseModel, ConfigDict, Field, model_validator

from core.exceptions import BadRequestError, InvalidFieldValue

from .base import DBBase, DBBaseCreate, PaginationPageDetails

# Non-standard legacy permission keys with their required object_types
LEGACY_PERMISSION_CONSTRAINTS = {
    "object_set_password": "User",
    "object_search": "User",
    "object_send": "Mail",
    "object_send_bulk": "Mail",
    "object_reset": "VirtualMachine",
    "object_actions_stop": ["VirtualMachine", "Event"],
    "object_actions_start": ["VirtualMachine", "Event"],
    "object_actions_shutdown": "VirtualMachine",
    "object_actions_pause": "VirtualMachine",
    "object_actions_hibernate": "VirtualMachine",
    "object_actions_resume": "VirtualMachine",
    "object_actions_reboot": "VirtualMachine",
    "object_actions_reset": "VirtualMachine",
    "object_admins": "Dashboard",
    "object_verwaltende": "Dashboard",
    "object_templates_update": "Event",
    "object_users_read": "Policy",
}


# object_types where object_id association is NOT allowed (global permissions only)
class DeactivatedObjectTypes(Enum):
    """Object types that only support global (non-object-scoped) permissions."""

    Activity = "Activity"
    Changelog = "Changelog"
    ObjectPermission = "ObjectPermission"
    Dashboard = "Dashboard"
    Language = "Language"
    Mail = "Mail"
    Proxmox = "Proxmox"
    # Role = "Role"
    SubTask = "SubTask"
    Tag = "Tag"
    Task = "Task"
    System = "System"


# Forbidden ObjectPermission combinations
FORBIDDEN_COMBINATIONS = {
    "Tag": None,  # Global deactivation
    "Activity": ["object_create", "object_update", "object_delete"],
}
GLOBAL_ONLY_PERMISSIONS = ["object_templates_update", "object_users_read"]

# Object types that support object-scoped permissions (object_id may be set)
OBJECT_SCOPED_TYPES = [
    "Application",
    "Course",
    "Document",
    "Event",
    "Guacamole",
    "GuacamoleConnectionProfile",
    "MailTemplate",
    "OS",
    "Policy",
    "Template",
    "Vendor",
    "VirtualMachine",
]


# ObjectPermission.key options
class ObjectPermissionKeys(Enum):
    """Standard permission key values assignable to roles."""

    object_full = "object_full"
    object_read = "object_read"
    object_create = "object_create"
    object_delete = "object_delete"
    object_update = "object_update"


# ObjectPermissions base
class ObjectPermissionBase(DBBase):
    """Base schema for object permission entries linking roles to resource access."""

    object_type: str | None = Field(
        None,
        description="Type of the resource this permission applies to, e.g. VirtualMachine",
    )
    object_id: UUID4 | None = Field(
        None,
        description="ID of the specific resource, or null for global permissions",
    )
    entity_id: UUID4 | None = Field(
        None, description="ID of the role or user this permission is granted to"
    )
    entity_type: str | None = Field(
        None,
        description="Type of the entity this permission is granted to, e.g. Role",
    )
    permission_key: str | None = Field(
        None,
        description="Permission key granted. One of: object_full, object_read, object_create, object_update, object_delete, or a legacy key",
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class ObjectPermissionCreate(DBBaseCreate):
    """Payload for creating a new object permission assignment."""

    object_type: str = Field(
        ...,
        description="Type of the resource this permission applies to, e.g. VirtualMachine",
    )
    object_id: UUID4 | None = Field(
        None,
        description="ID of the specific resource, or null for global permissions",
    )
    entity_id: UUID4 = Field(
        ..., description="ID of the role or user this permission is granted to"
    )
    entity_type: str = Field(
        ...,
        description="Type of the entity this permission is granted to, e.g. Role",
    )
    permission_key: str = Field(
        ...,
        description="Permission key to grant. One of: object_full, object_read, object_create, object_update, object_delete, or a legacy key",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "object_type": "VirtualMachine",
                "object_id": "00000000-0000-0000-0000-000000000001",
                "entity_id": "00000000-0000-0000-0000-000000000002",
                "entity_type": "Role",
                "permission_key": "object_read",
            }
        },
    )

    @model_validator(mode="before")
    @classmethod
    def validate_object_permission(cls, values):
        object_type = values.get("object_type")
        object_id = values.get("object_id")
        permission_key = values.get("permission_key")

        # Validate forbidden combinations
        if object_type in FORBIDDEN_COMBINATIONS:
            forbidden_perms = FORBIDDEN_COMBINATIONS[object_type]

            # If None, entire object_type is forbidden
            if forbidden_perms is None:
                raise InvalidFieldValue(field="object_type", value=object_type)

            # If list, check if permission_key is in forbidden list
            if permission_key in forbidden_perms:
                raise InvalidFieldValue(
                    field="permission_key", value=permission_key
                )

        # Validate global-only permission keys (must have object_id=None)
        if permission_key in GLOBAL_ONLY_PERMISSIONS and object_id is not None:
            raise BadRequestError(
                message=f"Permission key '{permission_key}' can only be used as a global permission and may not be assigned to an object."
            )

        # Validate deactivated types with object_id
        deactivated_types = [t.value for t in DeactivatedObjectTypes]
        if object_type in deactivated_types and object_id is not None:
            raise InvalidFieldValue(
                field="object_type",
                value=object_type,
                supported_values=", ".join(OBJECT_SCOPED_TYPES),
            )

        # Only allow object_create if object_id is None
        if permission_key == "object_create" and object_id is not None:
            raise BadRequestError(
                message="Cannot create generic 'object_create' Permission if 'object_id' is provided."
            )

        # Validate legacy permission keys are only used with correct object_type
        if permission_key in LEGACY_PERMISSION_CONSTRAINTS:
            allowed_types = LEGACY_PERMISSION_CONSTRAINTS[permission_key]
            # Handle both single string and list of strings
            if isinstance(allowed_types, str):
                allowed_types = [allowed_types]

            if object_type not in allowed_types:
                allowed_types_str = "' or '".join(allowed_types)
                raise BadRequestError(
                    message=f"Permission key '{permission_key}' can only be used with object_type '{allowed_types_str}', not '{object_type}'."
                )

        # Validate permission_key is either a valid enum value or a legacy key
        valid_enum_values = [key.value for key in ObjectPermissionKeys]

        # Build context-aware list of valid keys for this object_type/object_id combination
        valid_keys_for_context = valid_enum_values.copy()

        # Remove forbidden permissions for this object_type
        if object_type in FORBIDDEN_COMBINATIONS:
            forbidden_perms = FORBIDDEN_COMBINATIONS[object_type]
            if forbidden_perms is not None:  # If not entirely forbidden
                for forbidden_perm in forbidden_perms:
                    if forbidden_perm in valid_keys_for_context:
                        valid_keys_for_context.remove(forbidden_perm)

        # Add legacy permissions that are valid for this object_type
        for legacy_key, allowed_types in LEGACY_PERMISSION_CONSTRAINTS.items():
            if isinstance(allowed_types, str):
                allowed_types = [allowed_types]
            if object_type in allowed_types:
                # Check if it's forbidden for this object_type
                if object_type in FORBIDDEN_COMBINATIONS:
                    forbidden_perms = FORBIDDEN_COMBINATIONS[object_type]
                    if (
                        forbidden_perms is not None
                        and legacy_key in forbidden_perms
                    ):
                        continue  # Skip forbidden permission

                # Check if it's a global-only permission and object_id is provided
                if (
                    legacy_key in GLOBAL_ONLY_PERMISSIONS
                    and object_id is not None
                ):
                    continue  # Skip this key - it's not valid with object_id
                valid_keys_for_context.append(legacy_key)

        # Remove object_create if object_id is provided
        if object_id is not None and "object_create" in valid_keys_for_context:
            valid_keys_for_context.remove("object_create")

        if permission_key not in valid_keys_for_context:
            raise InvalidFieldValue(
                field="permission_key",
                value=permission_key,
                supported_values=", ".join(sorted(valid_keys_for_context)),
            )

        return values

    model_config = ConfigDict(from_attributes=True)


class ObjectPermissionInDBBase(ObjectPermissionBase):
    """Internal object permission schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class ObjectPermission(ObjectPermissionInDBBase):
    """Full object permission response schema."""

    object_type: str | None = None
    object_id: UUID4 | None = None
    entity_id: UUID4 | None = None
    entity_type: str
    permission_key: str | None = None
    model_config = ConfigDict(from_attributes=True)


class ObjectPermissionForRole(BaseModel):
    """Reduced object permission schema embedded in role responses."""

    id: UUID4 = Field(
        ..., description="Unique identifier of the object permission"
    )
    object_type: str | None = Field(
        None, description="Type of the resource this permission applies to"
    )
    object_id: UUID4 | None = Field(
        None,
        description="ID of the specific resource, or null for global permissions",
    )
    permission_key: str | None = Field(
        None, description="Permission key granted"
    )
    model_config = ConfigDict(from_attributes=True)


# List object of ObjectPermission
class ObjectPermissionList(BaseModel):
    """Paginated list of object permission entries."""

    pageDetails: PaginationPageDetails
    items: list[ObjectPermission]


class ObjectPermissionScopes(BaseModel):
    """Which scopes this object type supports."""

    global_: bool = Field(
        ...,
        alias="global",
        description="Supports global permissions (object_id=None)",
    )
    object: bool = Field(
        ..., description="Supports object-scoped permissions (with object_id)"
    )

    model_config = ConfigDict(populate_by_name=True)


class ObjectPermissionKeysByScope(BaseModel):
    """Permission keys split by scope."""

    global_: list[str] = Field(
        ...,
        alias="global",
        description="Keys valid for global permissions (object_id=None)",
    )
    object: list[str] | None = Field(
        None,
        description="Keys valid for object-scoped permissions, or null if not supported",
    )

    model_config = ConfigDict(populate_by_name=True)


class ObjectPermissionTypeSchema(BaseModel):
    """Valid permission keys for a given object type, split by scope."""

    object_type: str = Field(
        ..., description="The object type this schema applies to"
    )
    scopes: ObjectPermissionScopes = Field(
        ..., description="Which scopes this object type supports"
    )
    permission_keys: ObjectPermissionKeysByScope = Field(
        ..., description="Valid permission keys per scope"
    )

    model_config = ConfigDict(populate_by_name=True)


class ObjectPermissionTypeSchemaList(BaseModel):
    """List of permission schemas for all known object types."""

    pageDetails: PaginationPageDetails
    items: list[ObjectPermissionTypeSchema]


def get_permission_schema_for_type(
    object_type: str,
) -> ObjectPermissionTypeSchema:
    """Compute valid permission keys for a given object_type from static constraints."""
    deactivated_types = [t.value for t in DeactivatedObjectTypes]
    supports_object_scoped = object_type not in deactivated_types

    forbidden = FORBIDDEN_COMBINATIONS.get(object_type)

    # Entirely forbidden type (e.g. Tag)
    if forbidden is None and object_type in FORBIDDEN_COMBINATIONS:
        return ObjectPermissionTypeSchema(
            object_type=object_type,
            scopes=ObjectPermissionScopes.model_validate(
                {"global": True, "object": False}
            ),
            permission_keys=ObjectPermissionKeysByScope.model_validate(
                {"global": [], "object": None}
            ),
        )

    standard_keys = [k.value for k in ObjectPermissionKeys]
    forbidden_list = forbidden or []

    global_keys: list[str] = []
    object_keys: list[str] = []

    for key in standard_keys:
        if key in forbidden_list:
            continue
        is_global_only = (
            not supports_object_scoped
            or key in GLOBAL_ONLY_PERMISSIONS
            or key == "object_create"
        )
        global_keys.append(key)
        if not is_global_only:
            object_keys.append(key)

    for legacy_key, allowed_types in LEGACY_PERMISSION_CONSTRAINTS.items():
        if isinstance(allowed_types, str):
            allowed_types = [allowed_types]
        if object_type not in allowed_types:
            continue
        if legacy_key in forbidden_list:
            continue
        is_global_only = (
            not supports_object_scoped or legacy_key in GLOBAL_ONLY_PERMISSIONS
        )
        global_keys.append(legacy_key)
        if not is_global_only:
            object_keys.append(legacy_key)

    return ObjectPermissionTypeSchema(
        object_type=object_type,
        scopes=ObjectPermissionScopes.model_validate(
            {"global": True, "object": supports_object_scoped}
        ),
        permission_keys=ObjectPermissionKeysByScope.model_validate(
            {
                "global": global_keys,
                "object": object_keys if supports_object_scoped else None,
            }
        ),
    )
