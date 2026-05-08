from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# Base Vendor class
class VendorBase(DBBase):
    name: str | None = None
    description: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class VendorCreate(DBBaseCreate):
    name: str
    description: str | None = None


# Properties to receive via API on update
class VendorUpdate(DBBaseUpdate):
    name: str | None = None
    description: str | None = None
    model_config = ConfigDict(from_attributes=True)


class VendorInDBBase(VendorBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Vendor(VendorInDBBase):
    name: str
    description: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Class used for when Vendor is to appear as a nested model and will only display ID
class VendorNested(DBBaseUpdate):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# List object of Vendor
class VendorList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Vendor]
