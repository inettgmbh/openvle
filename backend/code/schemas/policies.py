from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base Policy class
class PolicyBase(DBBase):
    """Base schema for policy objects with name, description, and content fields."""

    name: str | None = Field(None, description="Display name of the policy")
    description: str | None = Field(
        None, description="Optional description of the policy"
    )
    content: str | None = Field(
        None, description="Full text content of the policy"
    )
    model_config = ConfigDict(from_attributes=True)


# Policy create schema
class PolicyCreate(DBBaseCreate):
    """Payload for creating a new policy."""

    name: str = Field(..., description="Display name of the policy")
    description: str | None = Field(
        None, description="Optional description of the policy"
    )
    content: str = Field(..., description="Full text content of the policy")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "Nutzungsrichtlinie",
                "description": "Allgemeine Nutzungsrichtlinie für das System",
                "content": "Mit der Nutzung dieses Systems stimmen Sie den folgenden Bedingungen zu...",
            }
        },
    )


# Policy create schema
class PolicyUpdate(DBBaseUpdate):
    """Payload for updating an existing policy's fields."""

    name: str | None = Field(None, description="Display name of the policy")
    description: str | None = Field(
        None, description="Optional description of the policy"
    )
    content: str | None = Field(
        None, description="Full text content of the policy"
    )
    active: bool | None = Field(
        None,
        description="Whether the policy is currently active and shown to users",
    )
    model_config = ConfigDict(from_attributes=True)


# Agree to policy schema
class PolicyUserAgree(DBBaseUpdate):
    """Payload for a user to agree or disagree to a policy."""

    agree: bool = Field(
        False,
        description="Set to true to indicate the user agrees to the policy",
    )

    model_config = ConfigDict(from_attributes=True)


class PolicyInDBBase(PolicyBase):
    """Internal policy schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Policy(PolicyInDBBase):
    """Full policy response schema including active status."""

    name: str
    description: str
    content: str
    active: bool

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class PolicyUser(DBBase):
    """Association schema linking a policy to a user who has agreed to it."""

    policy_id: UUID4 | None = Field(
        None, description="ID of the policy the user agreed to"
    )
    user_id: UUID4 | None = Field(
        None, description="ID of the user who agreed to the policy"
    )
    model_config = ConfigDict(from_attributes=True)


# List object of Policy
class PolicyList(BaseModel):
    """Paginated list of policy objects."""

    pageDetails: PaginationPageDetails
    items: list[Policy]


# List object of Policy-User associations
class PolicyUserList(BaseModel):
    """Paginated list of policy-user agreement associations."""

    pageDetails: PaginationPageDetails
    items: list[PolicyUser]
