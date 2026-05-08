from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base Policy class
class PolicyBase(DBBase):
    name: str | None = None
    description: str | None = None
    content: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Policy create schema
class PolicyCreate(DBBaseCreate):
    name: str
    description: str | None = None
    content: str

    model_config = ConfigDict(from_attributes=True)


# Policy create schema
class PolicyUpdate(DBBaseUpdate):
    name: str | None = None
    description: str | None = None
    content: str | None = None
    active: bool | None = None
    model_config = ConfigDict(from_attributes=True)


# Agree to policy schema
class PolicyUserAgree(DBBaseUpdate):
    agree: bool = False

    model_config = ConfigDict(from_attributes=True)


class PolicyInDBBase(PolicyBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Policy(PolicyInDBBase):
    name: str
    description: str
    content: str
    active: bool

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class PolicyUser(DBBase):
    policy_id: UUID4 | None = None
    user_id: UUID4 | None = None
    model_config = ConfigDict(from_attributes=True)


# List object of Policy
class PolicyList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Policy]


# List object of Policy-User associations
class PolicyUserList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[PolicyUser]
