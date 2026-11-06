from datetime import datetime
from typing import Generic, TypeVar

from pydantic import UUID4, BaseModel, ConfigDict, Field, computed_field

from core.mariadb import SessionLocal
from models import User as UserModel

from .base import (
    DBBase,
    DBBaseCreate,
    DBBaseUpdate,
    LenientEmailStr,
    PaginationPageDetails,
)
from .roles import RoleKeyOnly, RoleNested


# Base User class
class UserBase(DBBase):
    """Base schema for user objects with common profile fields."""

    username: str | None = Field(None, description="Unique login username")
    name: str | None = Field(None, description="Human-readable display name")
    email: LenientEmailStr | None = Field(
        None, description="User's email address"
    )
    status: str | None = Field(
        "E-Mail-Pending",
        description="User status. One of: Active, Banned, E-Mail-Pending",
    )
    locale: str | None = Field(
        "de_DE", description="User's preferred locale, e.g. de_DE or en_US"
    )
    description: str | None = Field(
        None, description="Optional free-text description of the user"
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class UserCreate(DBBaseCreate):
    """Payload for creating a new user account."""

    username: str = Field(..., description="Unique login username")
    email: LenientEmailStr = Field(..., description="User's email address")
    name: str | None = Field(None, description="Human-readable display name")
    description: str | None = Field(
        None, description="Optional free-text description of the user"
    )
    locale: str | None = Field(
        "de_DE", description="User's preferred locale, e.g. de_DE or en_US"
    )
    status: str | None = Field(
        "E-Mail-Pending",
        description="User status. One of: Active, Banned, E-Mail-Pending",
    )
    password: str | None = Field(
        None, description="Plain-text password set on creation"
    )
    password_repeat: str | None = Field(
        None, description="Password confirmation, must match password"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "max.mustermann",
                "email": "max.mustermann@example.com",
                "name": "Max Mustermann",
                "locale": "de_DE",
                "status": "Active",
                "password": "SecurePass123!",
                "password_repeat": "SecurePass123!",
            }
        }
    )


# Properties to receive via API on update
class UserUpdate(DBBaseUpdate):
    """Payload for updating an existing user's profile fields."""

    name: str | None = Field(None, description="Human-readable display name")
    description: str | None = Field(
        None, description="Optional free-text description of the user"
    )
    email: LenientEmailStr | None = Field(
        None, description="User's email address"
    )
    status: str | None = Field(
        "E-Mail-Pending",
        description="User status. One of: Active, Banned, E-Mail-Pending",
    )
    locale: str | None = Field(
        "de_DE", description="User's preferred locale, e.g. de_DE or en_US"
    )


# Properties to receive via API on updateRoles
class UserUpdateRoles(DBBaseUpdate):
    """Payload for replacing a user's assigned roles."""

    roles: list[RoleKeyOnly] | None = Field(
        None, description="List of role keys to assign to the user"
    )


class UserInDBBase(UserBase):
    """Internal user schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Additional properties stored in DB but not returned by API
class UserInDB(UserInDBBase):
    """Full internal user schema including sensitive credential fields."""

    hashed_password: str = Field(
        ..., description="Bcrypt-hashed password stored in the database"
    )
    resetToken: UUID4 = Field(
        ..., description="Token used for password reset flows"
    )
    resetTokenCreatedAt: datetime = Field(
        ..., description="Timestamp when the reset token was generated"
    )
    twoFactorSecret: str = Field(
        ..., description="TOTP secret used for two-factor authentication"
    )
    mailValidateToken: UUID4 = Field(
        ..., description="Token used to verify the user's email address"
    )
    password: str = Field(
        ...,
        description="Temporary plain-text password field used during creation",
    )


# Only returns ID
class UserIdOnly(DBBaseUpdate):
    """Minimal user schema returning only the UUID."""

    id: UUID4 = Field(..., description="Unique identifier of the user")

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class User(UserInDBBase):
    """Full user response schema including roles and computed type."""

    roles: list[RoleNested]

    @computed_field
    @property
    def user_type(self) -> str:
        db = SessionLocal()
        user_object = db.get(UserModel, self.id)
        db.close()
        return "internal" if user_object.hashed_password else "external"

    model_config = ConfigDict(from_attributes=True)

    def model_dump(self, *args, **kwargs):
        result = super().model_dump(*args, **kwargs)
        # If deleted_ user: only return id + username
        username = result.get("username", "")
        if username and "deleted_" in username:
            return {
                "id": result.get("id"),
                "username": username,
            }
        return result


# Restricted schema for /auth/user (own user info)
class UserSelf(User):
    """Reduced user schema for the authenticated user's own profile endpoint."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra=lambda schema, _model: [
            schema.get("properties", {}).pop(f, None)
            for f in ("updatedAt", "updatedById", "createdById")
        ],
    )

    def model_dump(self, *args, **kwargs):
        result = super().model_dump(*args, **kwargs)
        for field in (
            "updatedAt",
            "updatedById",
            "createdById",
        ):
            result.pop(field, None)
        return result


# List object of User
class UserList(BaseModel):
    """Paginated list of full user objects."""

    pageDetails: PaginationPageDetails
    items: list[User]


# Limited schema for users with object_search permission only
class UserSearch(BaseModel):
    """Reduced user schema returned for searches with limited permissions."""

    id: UUID4
    username: str | None = Field(None, description="Unique login username")
    name: str | None = Field(None, description="Human-readable display name")
    email: LenientEmailStr | None = Field(
        None, description="User's email address"
    )
    model_config = ConfigDict(from_attributes=True)


# List object of UserSearch (limited)
class UserSearchList(BaseModel):
    """Paginated list of limited user search results."""

    pageDetails: PaginationPageDetails
    items: list[UserSearch]


# Properties to receive via API on update_password
class UserUpdatePassword(DBBaseUpdate):
    """Payload for changing the authenticated user's own password."""

    password_old: str = Field(
        ..., description="Current password for verification"
    )
    password_new: str = Field(..., description="New password to set")
    password_new_repeat: str = Field(
        ..., description="New password confirmation, must match password_new"
    )


# Properties to receive via API on set_password
class UserSetPassword(DBBaseUpdate):
    """Payload for an admin to set a user's password without the old password."""

    password_new: str = Field(..., description="New password to set")
    password_new_repeat: str = Field(
        ..., description="New password confirmation, must match password_new"
    )


T = TypeVar("T")


class TruncatedList(BaseModel, Generic[T]):
    """List wrapper that signals whether the items have been capped to a limit."""

    items: list[T]
    truncated: bool

    model_config = ConfigDict(from_attributes=True)


class UserDeletePreviewVirtualMachine(BaseModel):
    id: UUID4
    name: str
    model_config = ConfigDict(from_attributes=True)


class UserDeletePreviewConnection(BaseModel):
    id: UUID4
    name: str
    model_config = ConfigDict(from_attributes=True)


class UserDeletePreviewMail(BaseModel):
    id: UUID4
    subject: str
    to_mail: str = Field(alias="toMail")
    send_status: str = Field(alias="sendStatus")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserDeletePreviewChangelog(BaseModel):
    id: UUID4
    object: str | None = None
    object_id: UUID4 = Field(alias="objectId")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserDeletePreviewObjectPermission(BaseModel):
    id: UUID4
    object_type: str
    permission_key: str
    model_config = ConfigDict(from_attributes=True)


class UserDeletePreviewTag(BaseModel):
    id: UUID4
    key: str
    value: str
    model_config = ConfigDict(from_attributes=True)


class UserDeletePreviewEventMembershipRole(BaseModel):
    id: UUID4
    name: str
    model_config = ConfigDict(from_attributes=True)


class UserDeletePreviewEventMembership(BaseModel):
    id: UUID4
    name: str
    status: str
    role: UserDeletePreviewEventMembershipRole
    model_config = ConfigDict(from_attributes=True)


class UserDeletePreviewStats(BaseModel):
    virtual_machines: int
    connections: int
    mails: int
    changelogs: int
    object_permissions: int
    event_memberships: int
    policy_memberships: int
    tags: int


class UserDeletePreview(BaseModel):
    stats: UserDeletePreviewStats
    virtual_machines: TruncatedList[UserDeletePreviewVirtualMachine]
    connections: TruncatedList[UserDeletePreviewConnection]
    mails: TruncatedList[UserDeletePreviewMail]
    changelogs: TruncatedList[UserDeletePreviewChangelog]
    object_permissions: TruncatedList[UserDeletePreviewObjectPermission]
    tags: TruncatedList[UserDeletePreviewTag]
    event_memberships: TruncatedList[UserDeletePreviewEventMembership]


# Properties to receive via API on Login
class UserLogin(DBBaseUpdate):
    """Payload for authenticating a user with username and password."""

    username: str = Field(
        ..., description="Username of the account to authenticate"
    )
    password: str = Field(
        ..., description="Plain-text password for authentication"
    )
