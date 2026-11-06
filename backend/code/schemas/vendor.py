from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base Vendor class
class VendorBase(DBBase):
    """Base schema for software/hardware vendor objects."""

    name: str | None = Field(None, description="Display name of the vendor")
    description: str | None = Field(
        None, description="Optional description of the vendor"
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class VendorCreate(DBBaseCreate):
    """Payload for creating a new vendor."""

    name: str = Field(..., description="Display name of the vendor")
    description: str | None = Field(
        None, description="Optional description of the vendor"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Microsoft",
                "description": "Microsoft Corporation",
            }
        }
    )


# Properties to receive via API on update
class VendorUpdate(DBBaseUpdate):
    """Payload for updating an existing vendor's details."""

    name: str | None = Field(None, description="Display name of the vendor")
    description: str | None = Field(
        None, description="Optional description of the vendor"
    )
    model_config = ConfigDict(from_attributes=True)


class VendorInDBBase(VendorBase):
    """Internal vendor schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Vendor(VendorInDBBase):
    """Full vendor response schema."""

    name: str
    description: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Class used for when Vendor is to appear as a nested model and will only display ID
class VendorNested(DBBaseUpdate):
    """Minimal vendor schema for nested references, shows ID only."""

    id: UUID4 = Field(..., description="Unique identifier of the vendor")

    model_config = ConfigDict(from_attributes=True)


# List object of Vendor
class VendorList(BaseModel):
    """Paginated list of vendor objects."""

    pageDetails: PaginationPageDetails
    items: list[Vendor]
