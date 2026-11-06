"""Tests for controllers/roles.py - CRUDRole operations."""

import uuid
from datetime import datetime, timezone

import pytest
from controllers.roles import CRUDRole
from core.exceptions import (
    ObjectNotFound,
    ProtectedObjectError,
    RequiredParameterMissingError,
)
from models import Changelog, ObjectPermission, Role
from models.associations import (
    user_role_association_table,
)
from schemas.roles import (
    RoleCreate,
    RoleUpdateObjectPermissions,
)

from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def normal_role(db_session, system_user):
    """Create a non-protected role."""
    now = datetime.now(timezone.utc)
    role = Role(
        id=uuid.uuid4(),
        name="Test Role",
        key="test_role",
        protected=False,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(role)
    db_session.flush()
    return role


class TestCRUDRoleGetByName:
    def setup_method(self):
        self.crud = CRUDRole(Role)

    def test_get_by_name_found(self, db_session, normal_role):
        result = self.crud.get_by_name(db_session, name="Test Role")
        assert result is not None
        assert result.key == "test_role"

    def test_get_by_name_not_found(self, db_session, system_user):
        result = self.crud.get_by_name(db_session, name="nonexistent")
        assert result is None


class TestCRUDRoleGetByKey:
    def setup_method(self):
        self.crud = CRUDRole(Role)

    def test_get_by_key_found(self, db_session, normal_role):
        result = self.crud.get_by_key(db_session, key="test_role")
        assert result is not None
        assert result.name == "Test Role"

    def test_get_by_key_not_found(self, db_session, system_user):
        result = self.crud.get_by_key(db_session, key="nonexistent")
        assert result is None


class TestCRUDRoleCreate:
    def setup_method(self):
        self.crud = CRUDRole(Role)

    def test_create_role(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = RoleCreate(
            name="New Role", key="new_role", description="A new role"
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.name == "New Role"
        assert result.key == "new_role"


class TestCRUDRoleGetMembers:
    def setup_method(self):
        self.crud = CRUDRole(Role)

    def test_returns_role_members(
        self, db_session, system_user, active_user, normal_role
    ):
        db_session.execute(
            user_role_association_table.insert().values(
                user_id=active_user.id, role_id=normal_role.id
            )
        )
        db_session.flush()

        result = self.crud.get_members(db_session, id=normal_role.id)
        user_ids = [u.id for u in result["items"]]
        assert active_user.id in user_ids
        # System user should be excluded
        assert system_user.id not in user_ids

    def test_returns_empty_when_no_members(
        self, db_session, system_user, normal_role
    ):
        result = self.crud.get_members(db_session, id=normal_role.id)
        assert len(result["items"]) == 0


class TestCRUDRoleDelete:
    def setup_method(self):
        self.crud = CRUDRole(Role)

    def test_delete_normal_role(self, db_session, system_user, normal_role):
        result = self.crud.delete(db_session, id=normal_role.id)
        assert "deleted" in result["detail"]

    def test_delete_protected_role_raises(self, db_session, system_user):
        now = datetime.now(timezone.utc)
        protected_role = Role(
            id=uuid.uuid4(),
            name="Protected Role",
            key="protected_role",
            protected=True,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(protected_role)
        db_session.flush()

        with pytest.raises(ProtectedObjectError):
            self.crud.delete(db_session, id=protected_role.id)

    def test_delete_cascades_changelogs(
        self, db_session, system_user, normal_role
    ):
        cl = Changelog(
            id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            valueOld="old",
            valueNew="new",
            object="Role",
            objectId=normal_role.id,
            userId=system_user.id,
        )
        db_session.add(cl)
        db_session.flush()

        self.crud.delete(db_session, id=normal_role.id)

        remaining = (
            db_session.query(Changelog)
            .filter(Changelog.objectId == normal_role.id)
            .all()
        )
        assert len(remaining) == 0


class TestCRUDRoleSetObjectPermissions:
    def setup_method(self):
        self.crud = CRUDRole(Role)

    def test_set_object_permissions(self, db_session, active_user, normal_role):
        """Set object permissions replaces the role's object_permissions list."""
        now = datetime.now(timezone.utc)
        obj_perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Course",
            object_id=uuid.uuid4(),
            entity_id=normal_role.id,
            entity_type="Role",
            permission_key="object_read",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(obj_perm)
        db_session.flush()

        request = create_mock_request(active_user)
        obj_in = RoleUpdateObjectPermissions(object_permissions=[obj_perm.id])
        result = self.crud.set_object_permissions(
            normal_role.id, db_session, request, obj_in=obj_in
        )
        op_ids = [op.id for op in result.object_permissions]
        assert obj_perm.id in op_ids

    def test_set_object_permissions_replaces(
        self, db_session, active_user, normal_role
    ):
        """Setting object permissions replaces previously assigned ones."""
        now = datetime.now(timezone.utc)
        obj_perm_1 = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Course",
            object_id=uuid.uuid4(),
            entity_id=normal_role.id,
            entity_type="Role",
            permission_key="object_read",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        obj_perm_2 = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Event",
            object_id=uuid.uuid4(),
            entity_id=normal_role.id,
            entity_type="Role",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add_all([obj_perm_1, obj_perm_2])
        db_session.flush()

        request = create_mock_request(active_user)
        # First set perm_1
        obj_in_1 = RoleUpdateObjectPermissions(
            object_permissions=[obj_perm_1.id]
        )
        self.crud.set_object_permissions(
            normal_role.id, db_session, request, obj_in=obj_in_1
        )
        # Then replace with perm_2
        obj_in_2 = RoleUpdateObjectPermissions(
            object_permissions=[obj_perm_2.id]
        )
        result = self.crud.set_object_permissions(
            normal_role.id, db_session, request, obj_in=obj_in_2
        )
        op_ids = [op.id for op in result.object_permissions]
        assert obj_perm_2.id in op_ids
        assert obj_perm_1.id not in op_ids

    def test_set_object_permissions_empty_raises(
        self, db_session, active_user, normal_role
    ):
        """Empty object_permissions list raises RequiredParameterMissingError."""
        request = create_mock_request(active_user)
        obj_in = RoleUpdateObjectPermissions(object_permissions=[])
        with pytest.raises(RequiredParameterMissingError):
            self.crud.set_object_permissions(
                normal_role.id, db_session, request, obj_in=obj_in
            )

    def test_set_object_permissions_nonexistent_id_raises(
        self, db_session, active_user, normal_role
    ):
        """Non-existent ObjectPermission ID raises ObjectNotFound."""
        request = create_mock_request(active_user)
        fake_id = uuid.uuid4()
        obj_in = RoleUpdateObjectPermissions(object_permissions=[fake_id])
        with pytest.raises(ObjectNotFound):
            self.crud.set_object_permissions(
                normal_role.id, db_session, request, obj_in=obj_in
            )

    def test_set_object_permissions_nonexistent_role_raises(
        self, db_session, active_user
    ):
        """Non-existent role ID raises ObjectNotFound."""
        request = create_mock_request(active_user)
        obj_in = RoleUpdateObjectPermissions(object_permissions=[uuid.uuid4()])
        with pytest.raises(ObjectNotFound):
            self.crud.set_object_permissions(
                uuid.uuid4(), db_session, request, obj_in=obj_in
            )


class TestCRUDRoleUpdateObjectPermissions:
    def setup_method(self):
        self.crud = CRUDRole(Role)

    def test_update_object_permissions_appends(
        self, db_session, active_user, normal_role
    ):
        """Updating object permissions appends to existing list."""
        now = datetime.now(timezone.utc)
        obj_perm_1 = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Course",
            object_id=uuid.uuid4(),
            entity_id=normal_role.id,
            entity_type="Role",
            permission_key="object_read",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        obj_perm_2 = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Event",
            object_id=uuid.uuid4(),
            entity_id=normal_role.id,
            entity_type="Role",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add_all([obj_perm_1, obj_perm_2])
        db_session.flush()

        request = create_mock_request(active_user)
        # First set perm_1
        obj_in_1 = RoleUpdateObjectPermissions(
            object_permissions=[obj_perm_1.id]
        )
        self.crud.set_object_permissions(
            normal_role.id, db_session, request, obj_in=obj_in_1
        )
        # Then update (append) perm_2
        obj_in_2 = RoleUpdateObjectPermissions(
            object_permissions=[obj_perm_2.id]
        )
        result = self.crud.update_object_permissions(
            normal_role.id, db_session, request, obj_in=obj_in_2
        )
        op_ids = [op.id for op in result.object_permissions]
        assert obj_perm_1.id in op_ids
        assert obj_perm_2.id in op_ids

    def test_update_object_permissions_avoids_duplicates(
        self, db_session, active_user, normal_role
    ):
        """Updating with an already-assigned permission does not duplicate it."""
        now = datetime.now(timezone.utc)
        obj_perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Course",
            object_id=uuid.uuid4(),
            entity_id=normal_role.id,
            entity_type="Role",
            permission_key="object_read",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(obj_perm)
        db_session.flush()

        request = create_mock_request(active_user)
        # Set the permission first
        obj_in = RoleUpdateObjectPermissions(object_permissions=[obj_perm.id])
        self.crud.set_object_permissions(
            normal_role.id, db_session, request, obj_in=obj_in
        )
        # Update with the same permission again
        result = self.crud.update_object_permissions(
            normal_role.id, db_session, request, obj_in=obj_in
        )
        op_ids = [op.id for op in result.object_permissions]
        assert op_ids.count(obj_perm.id) == 1

    def test_update_object_permissions_empty_raises(
        self, db_session, active_user, normal_role
    ):
        """Empty object_permissions list raises RequiredParameterMissingError."""
        request = create_mock_request(active_user)
        obj_in = RoleUpdateObjectPermissions(object_permissions=[])
        with pytest.raises(RequiredParameterMissingError):
            self.crud.update_object_permissions(
                normal_role.id, db_session, request, obj_in=obj_in
            )

    def test_update_object_permissions_nonexistent_id_raises(
        self, db_session, active_user, normal_role
    ):
        """Non-existent ObjectPermission ID raises ObjectNotFound."""
        now = datetime.now(timezone.utc)
        # First set a valid object permission so the dynamic attribute exists
        valid_perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Course",
            object_id=uuid.uuid4(),
            entity_id=normal_role.id,
            entity_type="Role",
            permission_key="object_read",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(valid_perm)
        db_session.flush()

        request = create_mock_request(active_user)
        obj_in_setup = RoleUpdateObjectPermissions(
            object_permissions=[valid_perm.id]
        )
        self.crud.set_object_permissions(
            normal_role.id, db_session, request, obj_in=obj_in_setup
        )

        # Now try to update with a fake ID
        fake_id = uuid.uuid4()
        obj_in = RoleUpdateObjectPermissions(object_permissions=[fake_id])
        with pytest.raises(ObjectNotFound):
            self.crud.update_object_permissions(
                normal_role.id, db_session, request, obj_in=obj_in
            )
