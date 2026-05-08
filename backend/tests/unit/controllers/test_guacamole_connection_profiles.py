"""Tests for controllers/guacamole_connection_profiles.py - CRUDGuacamoleConnectionProfile operations."""

import uuid
from datetime import datetime, timezone

import pytest

from controllers.guacamole_connection_profiles import (
    CRUDGuacamoleConnectionProfile,
)
from core.exceptions import ModelNotFound, ObjectNotFound
from models import GuacamoleConnectionProfile, ObjectPermission, Role, Template, Vendor
from models.associations import user_role_association_table
from schemas.guacamole_connection_profiles import (
    GuacamoleConnectionProfileClone,
    GuacamoleConnectionProfileCreate,
)
from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def sample_vendor_gcp(db_session, system_user):
    now = datetime.now(timezone.utc)
    vendor = Vendor(
        id=uuid.uuid4(),
        name="GCP Vendor",
        description="Vendor for GCP tests",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


@pytest.fixture()
def sample_template(db_session, system_user, sample_vendor_gcp):
    now = datetime.now(timezone.utc)
    tpl = Template(
        id=uuid.uuid4(),
        name="tpl-01",
        proxmoxId=100,
        proxmoxNode="pve-node-1",
        status="stopped",
        cpu=2,
        ram=4096,
        disk=32,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(tpl)
    db_session.flush()
    return tpl


class TestGCPCreate:
    def setup_method(self):
        self.crud = CRUDGuacamoleConnectionProfile(GuacamoleConnectionProfile)

    def test_create_gcp(self, db_session, active_user, sample_template):
        request = create_mock_request(active_user)
        obj_in = GuacamoleConnectionProfileCreate(
            port=3389,
            protocol="rdp",
            username="admin",
            password="pass",
            objectId=str(sample_template.id),
            objectType="Template",
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.objectId == sample_template.id
        assert result.objectType == "Template"
        assert result.protocol == "rdp"

    def test_create_creates_object_permission(
        self, db_session, active_user, sample_template
    ):
        request = create_mock_request(active_user)
        obj_in = GuacamoleConnectionProfileCreate(
            port=3389,
            protocol="rdp",
            objectId=str(sample_template.id),
            objectType="Template",
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)

        obj_perm = (
            db_session.query(ObjectPermission)
            .filter(
                ObjectPermission.object_id == result.id,
                ObjectPermission.object_type == "GuacamoleConnectionProfile",
                ObjectPermission.permission_key == "object_full",
            )
            .first()
        )
        assert obj_perm is not None

    def test_create_invalid_object_type_raises(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = GuacamoleConnectionProfileCreate(
            port=3389,
            protocol="rdp",
            objectId=str(uuid.uuid4()),
            objectType="FakeModel",
        )
        with pytest.raises(ModelNotFound):
            self.crud.create(db_session, request, obj_in=obj_in)

    def test_create_nonexistent_object_raises(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = GuacamoleConnectionProfileCreate(
            port=3389,
            protocol="rdp",
            objectId=str(uuid.uuid4()),
            objectType="Template",
        )
        with pytest.raises(ObjectNotFound):
            self.crud.create(db_session, request, obj_in=obj_in)


class TestGCPClone:
    def setup_method(self):
        self.crud = CRUDGuacamoleConnectionProfile(GuacamoleConnectionProfile)

    def test_clone_inherits_defaults(self, db_session, active_user, sample_template):
        request = create_mock_request(active_user)
        # Create source GCP
        source_in = GuacamoleConnectionProfileCreate(
            port=3389,
            protocol="rdp",
            username="source-user",
            password="source-pass",
            objectId=str(sample_template.id),
            objectType="Template",
        )
        source = self.crud.create(db_session, request, obj_in=source_in)

        # Clone without specifying port/protocol/username/password
        clone_in = GuacamoleConnectionProfileClone(
            objectId=str(sample_template.id),
            objectType="Template",
        )
        cloned = self.crud.clone(
            db_session, id=source.id, request=request, obj_in=clone_in
        )
        assert cloned.port == 3389
        assert cloned.protocol.lower() == "rdp"
        assert cloned.username == "source-user"
        assert cloned.password == "source-pass"
        assert cloned.id != source.id


class TestGCPGetGcpsForObject:
    def setup_method(self):
        self.crud = CRUDGuacamoleConnectionProfile(GuacamoleConnectionProfile)

    def test_returns_profiles_for_object(
        self, db_session, active_user, sample_template
    ):
        request = create_mock_request(active_user)
        obj_in = GuacamoleConnectionProfileCreate(
            port=3389,
            protocol="rdp",
            objectId=str(sample_template.id),
            objectType="Template",
        )
        self.crud.create(db_session, request, obj_in=obj_in)

        result = self.crud.get_gcps_for_object(
            objectId=sample_template.id,
            objectType="Template",
            db=db_session,
        )
        assert len(result["items"]) == 1
        assert result["items"][0].objectType == "Template"


class TestGCPGetGcpsForObjectAuth:
    def setup_method(self):
        self.crud = CRUDGuacamoleConnectionProfile(GuacamoleConnectionProfile)

    def test_returns_profiles_user_has_permission_for(
        self, db_session, active_user, sample_template
    ):
        """User with object_full permission on a GCP can see it via auth query."""
        request = create_mock_request(active_user)
        # create() also creates an object_full ObjectPermission for active_user
        obj_in = GuacamoleConnectionProfileCreate(
            port=3389,
            protocol="rdp",
            objectId=str(sample_template.id),
            objectType="Template",
        )
        created_gcp = self.crud.create(db_session, request, obj_in=obj_in)

        result = self.crud.get_gcps_for_object_auth(
            request=request,
            objectId=sample_template.id,
            objectType="Template",
            db=db_session,
        )
        gcp_ids = [item.id for item in result["items"]]
        assert created_gcp.id in gcp_ids

    def test_excludes_profiles_without_permission(
        self, db_session, active_user, system_user, sample_template
    ):
        """GCP created by another user without shared permissions is not visible."""
        now = datetime.now(timezone.utc)
        # Create a GCP directly (no object permission for active_user)
        gcp = GuacamoleConnectionProfile(
            id=uuid.uuid4(),
            port=3389,
            protocol="rdp",
            objectId=sample_template.id,
            objectType="Template",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(gcp)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_gcps_for_object_auth(
            request=request,
            objectId=sample_template.id,
            objectType="Template",
            db=db_session,
        )
        gcp_ids = [item.id for item in result["items"]]
        assert gcp.id not in gcp_ids

    def test_returns_profiles_via_role_permission(
        self, db_session, active_user, system_user, sample_template
    ):
        """GCP visible when user's role has an object permission for it."""
        now = datetime.now(timezone.utc)
        # Create a role and assign active_user to it
        role = Role(
            id=uuid.uuid4(),
            name="GCP Viewer",
            key="gcp_viewer",
            protected=False,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(role)
        db_session.flush()
        db_session.execute(
            user_role_association_table.insert().values(
                user_id=active_user.id, role_id=role.id
            )
        )
        db_session.flush()

        # Create a GCP directly
        gcp = GuacamoleConnectionProfile(
            id=uuid.uuid4(),
            port=3389,
            protocol="rdp",
            objectId=sample_template.id,
            objectType="Template",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(gcp)
        db_session.flush()

        # Create role-level ObjectPermission for this GCP
        role_perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="GuacamoleConnectionProfile",
            object_id=gcp.id,
            entity_id=role.id,
            entity_type="Role",
            permission_key="object_read",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(role_perm)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_gcps_for_object_auth(
            request=request,
            objectId=sample_template.id,
            objectType="Template",
            db=db_session,
        )
        gcp_ids = [item.id for item in result["items"]]
        assert gcp.id in gcp_ids

    def test_returns_empty_for_different_object_type(
        self, db_session, active_user, sample_template
    ):
        """Auth query with wrong objectType returns no results."""
        request = create_mock_request(active_user)
        obj_in = GuacamoleConnectionProfileCreate(
            port=3389,
            protocol="rdp",
            objectId=str(sample_template.id),
            objectType="Template",
        )
        self.crud.create(db_session, request, obj_in=obj_in)

        result = self.crud.get_gcps_for_object_auth(
            request=request,
            objectId=sample_template.id,
            objectType="VirtualMachine",
            db=db_session,
        )
        assert len(result["items"]) == 0
