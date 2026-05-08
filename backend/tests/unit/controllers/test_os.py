"""Tests for controllers/os.py - CRUDOperatingSystem operations."""

import uuid
from datetime import datetime, timezone

import pytest

from controllers.os import CRUDOperatingSystem
from models import OS, Document, ObjectPermission, Vendor
from schemas.os import OSCreate, OSUpdate, OSUpdateDocuments
from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def sample_vendor(db_session, system_user):
    """Create a sample vendor for OS tests."""
    now = datetime.now(timezone.utc)
    vendor = Vendor(
        id=uuid.uuid4(),
        name="Canonical",
        description="Ubuntu publisher",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


@pytest.fixture()
def second_vendor(db_session, system_user):
    """Create a second vendor."""
    now = datetime.now(timezone.utc)
    vendor = Vendor(
        id=uuid.uuid4(),
        name="Debian Project",
        description="Debian publisher",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


@pytest.fixture()
def sample_document(db_session, system_user):
    """Create a sample document for testing."""
    now = datetime.now(timezone.utc)
    doc = Document(
        id=uuid.uuid4(),
        name="test-doc.pdf",
        description="A test document",
        path="./tmp/test-doc.pdf",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(doc)
    db_session.flush()
    return doc


class TestCRUDOSGetByName:
    def setup_method(self):
        self.crud = CRUDOperatingSystem(OS)

    def test_get_by_name_found(self, db_session, system_user, sample_vendor):
        now = datetime.now(timezone.utc)
        os_obj = OS(
            id=uuid.uuid4(),
            name="Ubuntu",
            key="ubuntu-22.04",
            version="22.04",
            vendor=sample_vendor.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(os_obj)
        db_session.flush()

        result = self.crud.get_by_name(db_session, name="Ubuntu")
        assert result is not None
        assert result.name == "Ubuntu"

    def test_get_by_name_not_found(self, db_session, system_user):
        result = self.crud.get_by_name(db_session, name="nonexistent")
        assert result is None


class TestCRUDOSGetByKey:
    def setup_method(self):
        self.crud = CRUDOperatingSystem(OS)

    def test_get_by_key_found(self, db_session, system_user, sample_vendor):
        now = datetime.now(timezone.utc)
        os_obj = OS(
            id=uuid.uuid4(),
            name="Debian 12",
            key="debian-12",
            version="12",
            vendor=sample_vendor.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(os_obj)
        db_session.flush()

        result = self.crud.get_by_key(db_session, key="debian-12")
        assert result is not None
        assert result.key == "debian-12"

    def test_get_by_key_not_found(self, db_session, system_user):
        result = self.crud.get_by_key(db_session, key="nonexistent")
        assert result is None


class TestCRUDOSCreate:
    def setup_method(self):
        self.crud = CRUDOperatingSystem(OS)

    def test_create_os(self, db_session, active_user, sample_vendor):
        request = create_mock_request(active_user)
        obj_in = OSCreate(
            name="New OS",
            key="new-os-1.0",
            version="1.0",
            vendor=str(sample_vendor.id),
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.name == "New OS"
        assert result.vendor == sample_vendor.id

    def test_create_creates_object_permission(
        self, db_session, active_user, sample_vendor
    ):
        request = create_mock_request(active_user)
        obj_in = OSCreate(
            name="Perm OS",
            key="perm-os-1.0",
            version="1.0",
            vendor=str(sample_vendor.id),
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)

        obj_perm = (
            db_session.query(ObjectPermission)
            .filter(
                ObjectPermission.object_id == result.id,
                ObjectPermission.entity_id == active_user.id,
                ObjectPermission.permission_key == "object_full",
                ObjectPermission.object_type == "OS",
            )
            .first()
        )
        assert obj_perm is not None


class TestCRUDOSUpdate:
    def setup_method(self):
        self.crud = CRUDOperatingSystem(OS)

    def test_update_fields(self, db_session, active_user, sample_vendor):
        now = datetime.now(timezone.utc)
        os_obj = OS(
            id=uuid.uuid4(),
            name="Old OS",
            key="old-os",
            version="1.0",
            vendor=sample_vendor.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(os_obj)
        db_session.flush()

        request = create_mock_request(active_user)
        obj_in = OSUpdate(name="Updated OS")
        result = self.crud.update(os_obj.id, db_session, request, obj_in=obj_in)
        assert result.name == "Updated OS"

    def test_update_vendor(self, db_session, active_user, sample_vendor, second_vendor):
        now = datetime.now(timezone.utc)
        os_obj = OS(
            id=uuid.uuid4(),
            name="Changeable OS",
            key="change-os",
            version="1.0",
            vendor=sample_vendor.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(os_obj)
        db_session.flush()

        request = create_mock_request(active_user)
        obj_in = OSUpdate(vendor=str(second_vendor.id))
        result = self.crud.update(os_obj.id, db_session, request, obj_in=obj_in)
        assert result.vendor == second_vendor.id


class TestCRUDOSDocuments:
    def setup_method(self):
        self.crud = CRUDOperatingSystem(OS)

    def test_update_documents_appends(
        self, db_session, active_user, sample_vendor, sample_document
    ):
        now = datetime.now(timezone.utc)
        os_obj = OS(
            id=uuid.uuid4(),
            name="Doc OS",
            key="doc-os",
            version="1.0",
            vendor=sample_vendor.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(os_obj)
        db_session.flush()

        request = create_mock_request(active_user)
        obj_in = OSUpdateDocuments(documents=[{"id": str(sample_document.id)}])
        result = self.crud.update_documents(
            os_obj.id, db_session, request, obj_in=obj_in
        )
        assert len(result.documents) == 1
        assert result.documents[0].id == sample_document.id

    def test_set_documents_replaces(
        self, db_session, active_user, sample_vendor, sample_document
    ):
        now = datetime.now(timezone.utc)
        os_obj = OS(
            id=uuid.uuid4(),
            name="Set Doc OS",
            key="set-doc-os",
            version="1.0",
            vendor=sample_vendor.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(os_obj)
        db_session.flush()

        # First add a document
        request = create_mock_request(active_user)
        obj_in = OSUpdateDocuments(documents=[{"id": str(sample_document.id)}])
        self.crud.update_documents(os_obj.id, db_session, request, obj_in=obj_in)

        # Now set (replace) with empty list
        obj_in_empty = OSUpdateDocuments(documents=[])
        result = self.crud.set_documents(
            os_obj.id, db_session, request, obj_in=obj_in_empty
        )
        assert len(result.documents) == 0
