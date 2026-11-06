"""Tests for controllers/object_permissions.py - CRUDObjectPermission operations."""

import json
import uuid
from datetime import datetime, timezone

import pytest
from controllers.object_permissions import CRUDObjectPermission
from core.exceptions import (
    DuplicateObjectPermission,
    InvalidFieldValue,
    ModelNotFound,
    ObjectNotFound,
    ProtectedObjectError,
)
from models import Application, Changelog, ObjectPermission, Role, User, Vendor
from models.associations import user_role_association_table
from schemas.object_permissions import ObjectPermissionCreate

from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def sample_vendor(db_session, system_user):
    now = datetime.now(timezone.utc)
    vendor = Vendor(
        id=uuid.uuid4(),
        name="ObjPerm Vendor",
        description="Vendor for ObjPerm tests",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


@pytest.fixture()
def sample_app(db_session, system_user, sample_vendor):
    now = datetime.now(timezone.utc)
    app = Application(
        id=uuid.uuid4(),
        key="test-app",
        name="Test App",
        vendor=sample_vendor.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(app)
    db_session.flush()
    return app


@pytest.fixture()
def unprotected_role(db_session, system_user):
    now = datetime.now(timezone.utc)
    role = Role(
        id=uuid.uuid4(),
        name="Unprotected Role",
        key="unprotected",
        protected=False,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(role)
    db_session.flush()
    return role


class TestCreateFull:
    def setup_method(self):
        self.crud = CRUDObjectPermission(ObjectPermission)

    def test_create_full(self, db_session, active_user, sample_app):
        request = create_mock_request(active_user)
        result = self.crud.create_full(
            db_session, request, "Application", sample_app.id, active_user.id
        )
        assert result.permission_key == "object_full"
        assert result.entity_id == active_user.id
        assert result.object_type == "Application"
        assert result.object_id == sample_app.id


class TestCreateReset:
    def setup_method(self):
        self.crud = CRUDObjectPermission(ObjectPermission)

    def test_create_reset(self, db_session, active_user, sample_app):
        request = create_mock_request(active_user)
        result = self.crud.create_reset(
            db_session, request, "Application", sample_app.id, active_user.id
        )
        assert result.permission_key == "object_reset"
        assert result.entity_id == active_user.id


class TestCreateValidation:
    def setup_method(self):
        self.crud = CRUDObjectPermission(ObjectPermission)

    def test_exact_duplicate_raises(self, db_session, active_user, sample_app):
        request = create_mock_request(active_user)
        obj_in = ObjectPermissionCreate(
            object_type="Application",
            object_id=sample_app.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_read",
        )
        self.crud.create(db_session, request, obj_in=obj_in)

        with pytest.raises(DuplicateObjectPermission):
            self.crud.create(db_session, request, obj_in=obj_in)

    def test_basic_crud_max_one(self, db_session, active_user, sample_app):
        """Only one basic CRUD perm per entity+object."""
        request = create_mock_request(active_user)
        obj_in1 = ObjectPermissionCreate(
            object_type="Application",
            object_id=sample_app.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_read",
        )
        self.crud.create(db_session, request, obj_in=obj_in1)

        obj_in2 = ObjectPermissionCreate(
            object_type="Application",
            object_id=sample_app.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_update",
        )
        with pytest.raises(DuplicateObjectPermission):
            self.crud.create(db_session, request, obj_in=obj_in2)

    def test_object_create_with_crud_allowed(
        self, db_session, active_user, sample_app
    ):
        """object_create can coexist with one basic CRUD permission."""
        request = create_mock_request(active_user)
        # First add a basic CRUD perm
        obj_in1 = ObjectPermissionCreate(
            object_type="Application",
            object_id=sample_app.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_read",
        )
        self.crud.create(db_session, request, obj_in=obj_in1)

        # Now add object_create (global, no object_id)
        obj_in2 = ObjectPermissionCreate(
            object_type="Application",
            object_id=None,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_create",
        )
        result = self.crud.create(db_session, request, obj_in=obj_in2)
        assert result.permission_key == "object_create"

    def test_creates_changelog(self, db_session, active_user, sample_app):
        request = create_mock_request(active_user)
        obj_in = ObjectPermissionCreate(
            object_type="Application",
            object_id=sample_app.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_full",
        )
        self.crud.create(db_session, request, obj_in=obj_in)

        changelogs = (
            db_session.query(Changelog)
            .filter(
                Changelog.objectId == active_user.id,
                Changelog.object == "User",
            )
            .all()
        )
        assert len(changelogs) >= 1
        cl = changelogs[-1]
        # valueOld and valueNew must be valid JSON
        old = json.loads(cl.valueOld)
        new = json.loads(cl.valueNew)
        assert old == {"permissions": []}
        assert new["permissions"][0]["object_type"] == "Application"
        assert new["permissions"][0]["object_id"] == str(sample_app.id)
        assert new["permissions"][0]["permission_key"] == "object_full"

    def test_creates_changelog_without_object_id(self, db_session, active_user):
        """Changelog valueNew contains null object_id when none provided."""
        request = create_mock_request(active_user)
        obj_in = ObjectPermissionCreate(
            object_type="Dashboard",
            object_id=None,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_read",
        )
        self.crud.create(db_session, request, obj_in=obj_in)

        changelogs = (
            db_session.query(Changelog)
            .filter(
                Changelog.objectId == active_user.id,
                Changelog.object == "User",
            )
            .all()
        )
        cl = changelogs[-1]
        new = json.loads(cl.valueNew)
        assert new["permissions"][0]["object_id"] is None

    def test_invalid_entity_type_raises(
        self, db_session, active_user, sample_app
    ):
        request = create_mock_request(active_user)
        obj_in = ObjectPermissionCreate(
            object_type="Application",
            object_id=sample_app.id,
            entity_id=active_user.id,
            entity_type="Invalid",
            permission_key="object_read",
        )
        with pytest.raises(InvalidFieldValue):
            self.crud.create(db_session, request, obj_in=obj_in)

    def test_nonexistent_entity_raises(
        self, db_session, active_user, sample_app
    ):
        request = create_mock_request(active_user)
        fake_id = uuid.uuid4()
        obj_in = ObjectPermissionCreate(
            object_type="Application",
            object_id=sample_app.id,
            entity_id=fake_id,
            entity_type="User",
            permission_key="object_read",
        )
        with pytest.raises(ObjectNotFound):
            self.crud.create(db_session, request, obj_in=obj_in)

    def test_protected_role_entity_raises(
        self, db_session, active_user, sample_app, system_user
    ):
        protected_role = (
            db_session.query(Role).filter_by(key="admin_full").one()
        )

        request = create_mock_request(active_user)
        obj_in = ObjectPermissionCreate(
            object_type="Application",
            object_id=sample_app.id,
            entity_id=protected_role.id,
            entity_type="Role",
            permission_key="object_read",
        )
        with pytest.raises(ProtectedObjectError):
            self.crud.create(db_session, request, obj_in=obj_in)

    def test_invalid_object_type_raises(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = ObjectPermissionCreate(
            object_type="FakeModel",
            object_id=None,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_read",
        )
        with pytest.raises(ModelNotFound):
            self.crud.create(db_session, request, obj_in=obj_in)

    def test_role_entity_allowed(
        self, db_session, active_user, sample_app, unprotected_role
    ):
        """Non-protected roles can be assigned object permissions."""
        request = create_mock_request(active_user)
        obj_in = ObjectPermissionCreate(
            object_type="Application",
            object_id=sample_app.id,
            entity_id=unprotected_role.id,
            entity_type="Role",
            permission_key="object_read",
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.entity_type == "Role"
        assert result.entity_id == unprotected_role.id


class TestGetMultiTypeId:
    def setup_method(self):
        self.crud = CRUDObjectPermission(ObjectPermission)

    def test_returns_object_specific_and_global(
        self, db_session, active_user, sample_app
    ):
        request = create_mock_request(active_user)
        # Create an object-specific permission
        self.crud.create_full(
            db_session, request, "Application", sample_app.id, active_user.id
        )
        # Create a global permission for Application type
        now = datetime.now(timezone.utc)
        global_perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Application",
            object_id=None,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_read",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(global_perm)
        db_session.flush()

        result = self.crud.get_multi_type_id(
            "Application", sample_app.id, db_session
        )
        assert len(result["items"]) >= 2


class TestDelete:
    def setup_method(self):
        self.crud = CRUDObjectPermission(ObjectPermission)

    def test_delete_creates_changelog(
        self, db_session, active_user, sample_app
    ):
        request = create_mock_request(active_user)
        perm = self.crud.create_full(
            db_session, request, "Application", sample_app.id, active_user.id
        )

        result = self.crud.delete(db_session, id=perm.id, request=request)
        assert "deleted" in result["detail"]

        changelogs = (
            db_session.query(Changelog)
            .filter(Changelog.objectId == active_user.id)
            .all()
        )
        assert len(changelogs) >= 1
        cl = changelogs[-1]
        # valueOld and valueNew must be valid JSON
        old = json.loads(cl.valueOld)
        new = json.loads(cl.valueNew)
        assert new == {"permissions": []}
        assert old["permissions"][0]["object_type"] == "Application"
        assert old["permissions"][0]["object_id"] == str(sample_app.id)
        assert old["permissions"][0]["permission_key"] == "object_full"

    def test_delete_changelog_without_object_id(self, db_session, active_user):
        """Changelog valueOld contains null object_id when perm had none."""
        request = create_mock_request(active_user)
        perm = self.crud.create_full(
            db_session, request, "Dashboard", None, active_user.id
        )

        self.crud.delete(db_session, id=perm.id, request=request)

        changelogs = (
            db_session.query(Changelog)
            .filter(Changelog.objectId == active_user.id)
            .order_by(Changelog.timestamp.desc())
            .all()
        )
        cl = changelogs[0]
        old = json.loads(cl.valueOld)
        assert old["permissions"][0]["object_id"] is None


class TestGetMultiTypeIdAuth:
    def setup_method(self):
        self.crud = CRUDObjectPermission(ObjectPermission)

    def test_returns_user_own_permissions(
        self, db_session, active_user, system_user, sample_app
    ):
        """User sees their own object permissions for a given type/id."""
        # User needs at least one role for the query to include user-level filters
        now = datetime.now(timezone.utc)
        role = Role(
            id=uuid.uuid4(),
            name="Auth Helper",
            key="auth_helper",
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

        request = create_mock_request(active_user)
        self.crud.create_full(
            db_session, request, "Application", sample_app.id, active_user.id
        )

        result = self.crud.get_multi_type_id_auth(
            request=request,
            object_type="Application",
            object_id=sample_app.id,
            db=db_session,
        )
        assert len(result["items"]) >= 1
        entity_ids = [p.entity_id for p in result["items"]]
        assert active_user.id in entity_ids

    def test_excludes_other_user_permissions(
        self, db_session, active_user, system_user, sample_app
    ):
        """User does not see permissions belonging to other users."""
        now = datetime.now(timezone.utc)
        # Create another user
        other_user_id = uuid.uuid4()
        other_user = User(
            id=other_user_id,
            username="otheruser",
            name="Other User",
            email="other@example.com",
            hashed_password="$2b$12$dummyhashvalue",
            status="Active",
            locale="de_DE",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(other_user)
        db_session.flush()

        # Create object permission for other_user
        other_perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Application",
            object_id=sample_app.id,
            entity_id=other_user.id,
            entity_type="User",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(other_perm)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_multi_type_id_auth(
            request=request,
            object_type="Application",
            object_id=sample_app.id,
            db=db_session,
        )
        entity_ids = [p.entity_id for p in result["items"]]
        assert other_user.id not in entity_ids

    def test_returns_role_permissions(
        self, db_session, active_user, system_user, sample_app
    ):
        """User sees permissions for a role they belong to."""
        now = datetime.now(timezone.utc)
        # Create a role and assign active_user to it
        role = Role(
            id=uuid.uuid4(),
            name="App Viewer",
            key="app_viewer",
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

        # Create role-level ObjectPermission
        role_perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Application",
            object_id=sample_app.id,
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
        result = self.crud.get_multi_type_id_auth(
            request=request,
            object_type="Application",
            object_id=sample_app.id,
            db=db_session,
        )
        perm_ids = [p.id for p in result["items"]]
        assert role_perm.id in perm_ids

    def test_includes_global_permissions(
        self, db_session, active_user, system_user, sample_app
    ):
        """Global permissions (object_id=None) for the user's type are included."""
        now = datetime.now(timezone.utc)
        # User needs at least one role for the query to include user-level filters
        role = Role(
            id=uuid.uuid4(),
            name="Auth Helper 2",
            key="auth_helper_2",
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

        global_perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Application",
            object_id=None,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_read",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(global_perm)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_multi_type_id_auth(
            request=request,
            object_type="Application",
            object_id=sample_app.id,
            db=db_session,
        )
        perm_ids = [p.id for p in result["items"]]
        assert global_perm.id in perm_ids

    def test_excludes_object_create_permissions(
        self, db_session, active_user, sample_app
    ):
        """object_create permissions are excluded from the results."""
        now = datetime.now(timezone.utc)
        create_perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Application",
            object_id=None,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_create",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(create_perm)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_multi_type_id_auth(
            request=request,
            object_type="Application",
            object_id=sample_app.id,
            db=db_session,
        )
        perm_keys = [p.permission_key for p in result["items"]]
        assert "object_create" not in perm_keys

    def test_returns_empty_when_no_permissions(
        self, db_session, active_user, sample_app
    ):
        """Returns empty when user has no permissions for the object."""
        request = create_mock_request(active_user)
        result = self.crud.get_multi_type_id_auth(
            request=request,
            object_type="Application",
            object_id=sample_app.id,
            db=db_session,
        )
        assert len(result["items"]) == 0
