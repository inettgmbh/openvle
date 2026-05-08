from typing import Optional

from sqlalchemy.orm import Session

from models.vendor import Vendor
from schemas.vendor import VendorCreate, VendorUpdate

from .base import CRUDBase


class CRUDVendor(CRUDBase[Vendor, VendorCreate, VendorUpdate]):
    # Get Vendor by name
    def get_by_name(self, db: Session, *, name: str) -> Vendor | None:
        vendor = db.query(Vendor).filter(Vendor.name == name).first()
        return vendor


vendor = CRUDVendor(Vendor)
