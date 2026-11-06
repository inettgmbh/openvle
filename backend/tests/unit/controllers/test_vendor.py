"""Tests for controllers/vendor.py - CRUDVendor operations."""

import uuid
from datetime import datetime, timezone

from controllers.vendor import CRUDVendor
from models import ObjectPermission, Vendor
from schemas.vendor import VendorCreate, VendorUpdate

from tests.helpers.mock_request import create_mock_request


class TestCRUDVendorGetByName:
    def setup_method(self):
        self.crud = CRUDVendor(Vendor)

    def test_get_by_name_found(self, db_session, system_user):
        now = datetime.now(timezone.utc)
        vendor = Vendor(
            id=uuid.uuid4(),
            name="Test Vendor",
            description="A test vendor",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(vendor)
        db_session.flush()

        result = self.crud.get_by_name(db_session, name="Test Vendor")
        assert result is not None
        assert result.name == "Test Vendor"

    def test_get_by_name_not_found(self, db_session, system_user):
        result = self.crud.get_by_name(db_session, name="nonexistent")
        assert result is None


class TestCRUDVendorCreate:
    def setup_method(self):
        self.crud = CRUDVendor(Vendor)

    def test_create_vendor(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = VendorCreate(name="New Vendor", description="A new vendor")
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.name == "New Vendor"
        assert result.description == "A new vendor"

    def test_create_creates_object_permission(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = VendorCreate(name="Perm Vendor", description="Has perm")
        result = self.crud.create(db_session, request, obj_in=obj_in)

        obj_perm = (
            db_session.query(ObjectPermission)
            .filter(
                ObjectPermission.object_id == result.id,
                ObjectPermission.entity_id == active_user.id,
                ObjectPermission.permission_key == "object_full",
            )
            .first()
        )
        assert obj_perm is not None
        assert obj_perm.object_type == "Vendor"


class TestCRUDVendorUpdate:
    def setup_method(self):
        self.crud = CRUDVendor(Vendor)

    def test_update_vendor(self, db_session, active_user):
        """Update name and description on a vendor."""
        request = create_mock_request(active_user)
        obj_in = VendorCreate(
            name="Original Vendor", description="Original desc"
        )
        vendor = self.crud.create(db_session, request, obj_in=obj_in)

        updated = self.crud.update(
            vendor.id,
            db_session,
            request,
            obj_in=VendorUpdate(
                name="Updated Vendor", description="Updated desc"
            ),
        )
        assert updated.name == "Updated Vendor"
        assert updated.description == "Updated desc"


class TestCRUDVendorDelete:
    def setup_method(self):
        self.crud = CRUDVendor(Vendor)

    def test_delete_vendor(self, db_session, active_user):
        """Delete a vendor and verify it is gone."""
        request = create_mock_request(active_user)
        obj_in = VendorCreate(name="Delete Me", description="Will be deleted")
        vendor = self.crud.create(db_session, request, obj_in=obj_in)
        vendor_id = vendor.id

        self.crud.delete(db_session, vendor_id)

        fetched = db_session.get(Vendor, vendor_id)
        assert fetched is None


class TestCRUDVendorGetMulti:
    def setup_method(self):
        self.crud = CRUDVendor(Vendor)

    def test_get_multi_returns_all(self, db_session, active_user):
        """Create several vendors, get_multi returns all."""
        request = create_mock_request(active_user)
        for i in range(3):
            obj_in = VendorCreate(
                name=f"MultiVendor{i}", description=f"Desc {i}"
            )
            self.crud.create(db_session, request, obj_in=obj_in)

        result = self.crud.get_multi(db_session)
        assert len(result["items"]) >= 3

    def test_search_by_name(self, db_session, active_user):
        """get_multi with search parameter filters by name."""
        request = create_mock_request(active_user)
        obj_in = VendorCreate(name="UniqueVendorXYZ", description="For search")
        self.crud.create(db_session, request, obj_in=obj_in)

        result = self.crud.get_multi(
            db_session,
            search_field="name",
            search_value="UniqueVendorXYZ",
        )
        assert len(result["items"]) == 1
        assert result["items"][0].name == "UniqueVendorXYZ"

    def test_get_by_name_case_sensitive(self, db_session, active_user):
        """Verify get_by_name matches the correct case."""
        request = create_mock_request(active_user)
        obj_in = VendorCreate(name="CaseVendor", description="Case test")
        self.crud.create(db_session, request, obj_in=obj_in)

        result = self.crud.get_by_name(db_session, name="CaseVendor")
        assert result is not None
        assert result.name == "CaseVendor"
