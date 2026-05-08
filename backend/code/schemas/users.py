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
    username: str | None = None
    name: str | None = None
    email: LenientEmailStr | None = None
    status: str | None = "E-Mail-Pending"
    locale: str | None = "de_DE"
    description: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class UserCreate(DBBaseCreate):
    username: str
    email: LenientEmailStr
    name: str | None = None
    description: str | None = None
    locale: str | None = "de_DE"
    status: str | None = "E-Mail-Pending"
    password: str | None = None
    password_repeat: str | None = None


# Properties to receive via API on update
class UserUpdate(DBBaseUpdate):
    name: str | None = None
    description: str | None = None
    email: LenientEmailStr | None = None
    status: str | None = "E-Mail-Pending"
    locale: str | None = "de_DE"


# Properties to receive via API on updateRoles
class UserUpdateRoles(DBBaseUpdate):
    roles: list[RoleKeyOnly] | None = None


class UserInDBBase(UserBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Additional properties stored in DB but not returned by API
class UserInDB(UserInDBBase):
    hashed_password: str
    resetToken: UUID4
    resetTokenCreatedAt: datetime
    twoFactorSecret: str
    mailValidateToken: UUID4
    password: str


# Only returns ID
class UserIdOnly(DBBaseUpdate):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class User(UserInDBBase):
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
    pageDetails: PaginationPageDetails
    items: list[User]


# Limited schema for users with object_search permission only
class UserSearch(BaseModel):
    id: UUID4
    username: str | None = None
    name: str | None = None
    email: LenientEmailStr | None = None
    model_config = ConfigDict(from_attributes=True)


# List object of UserSearch (limited)
class UserSearchList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[UserSearch]


# Properties to receive via API on update_password
class UserUpdatePassword(DBBaseUpdate):
    password_old: str
    password_new: str
    password_new_repeat: str


# Properties to receive via API on set_password
class UserSetPassword(DBBaseUpdate):
    password_new: str
    password_new_repeat: str


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
    username: str
    password: str
