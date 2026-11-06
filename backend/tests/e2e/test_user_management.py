"""
E2E workflow tests for user management.

Tests user CRUD, role assignment, permission management,
password operations, and user deletion cascade.
"""

import uuid
from datetime import datetime, timezone

from tests.e2e.conftest import API
from tests.helpers.auth_helpers import create_test_token

# ------------------------------------------------------------------
# Scenario A: User creation and role assignment
# ------------------------------------------------------------------


class TestUserCreationAndRoles:
    """Create users and manage their roles."""

    def test_create_user_then_assign_roles(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        role_admin,
    ):
        """POST /users/ -> 201, PUT /users/{id}/roles -> 200."""
        # Create user
        payload = {
            "username": f"newuser_{uuid.uuid4().hex[:6]}",
            "email": f"newuser_{uuid.uuid4().hex[:6]}@example.com",
            "name": "New User",
            "status": "Active",
        }
        resp = client.post(f"{API}/users/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        user_id = resp.json()["id"]

        # Set roles
        resp = client.put(
            f"{API}/users/{user_id}/roles",
            json={"roles": [{"key": "admin_full"}]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        roles = resp.json()["roles"]
        role_keys = [r["key"] for r in roles]
        assert "admin_full" in role_keys

        # Verify via GET
        resp = client.get(f"{API}/users/{user_id}", headers=auth_headers)
        assert resp.status_code == 200
        roles = resp.json()["roles"]
        role_keys = [r["key"] for r in roles]
        assert "admin_full" in role_keys

    def test_add_role_preserves_existing(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        role_teacher,
        role_student,
    ):
        """POST (update) roles adds to existing, does not replace."""
        # Create user with teacher role
        payload = {
            "username": f"roleadd_{uuid.uuid4().hex[:6]}",
            "email": f"roleadd_{uuid.uuid4().hex[:6]}@example.com",
            "name": "Role Add User",
            "status": "Active",
        }
        resp = client.post(f"{API}/users/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        user_id = resp.json()["id"]

        # Set initial role
        resp = client.put(
            f"{API}/users/{user_id}/roles",
            json={"roles": [{"key": "lehrende"}]},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # Add another role via POST (update)
        resp = client.post(
            f"{API}/users/{user_id}/roles",
            json={"roles": [{"key": "studierende"}]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        roles = resp.json()["roles"]
        role_keys = [r["key"] for r in roles]
        assert "lehrende" in role_keys
        assert "studierende" in role_keys

    def test_replace_roles_removes_old(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        role_teacher,
        role_student,
    ):
        """PUT roles replaces all existing roles."""
        payload = {
            "username": f"rolerpl_{uuid.uuid4().hex[:6]}",
            "email": f"rolerpl_{uuid.uuid4().hex[:6]}@example.com",
            "name": "Role Replace User",
            "status": "Active",
        }
        resp = client.post(f"{API}/users/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        user_id = resp.json()["id"]

        # Set both roles
        resp = client.put(
            f"{API}/users/{user_id}/roles",
            json={"roles": [{"key": "lehrende"}, {"key": "studierende"}]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()["roles"]) == 2

        # Replace with only teacher
        resp = client.put(
            f"{API}/users/{user_id}/roles",
            json={"roles": [{"key": "lehrende"}]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        roles = resp.json()["roles"]
        assert len(roles) == 1
        assert roles[0]["key"] == "lehrende"

    def test_cannot_modify_system_user_roles(
        self,
        client,
        db_session,
        system_user,
        mock_permission_allow,
        auth_headers,
        role_teacher,
    ):
        """Modifying system user roles returns 403."""
        resp = client.put(
            f"{API}/users/{system_user.id}/roles",
            json={"roles": [{"key": "lehrende"}]},
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# Scenario B: Self-access
# ------------------------------------------------------------------


class TestSelfAccess:
    """Test that users can access their own profile and password."""

    def test_user_can_view_own_profile(self, client, auth_headers, active_user):
        """GET /me returns own user data."""
        resp = client.get(f"{API}/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == active_user.username
        assert data["email"] == active_user.email

    def test_user_can_update_own_password(self, client, db_session, login_user):
        """PUT /me/password updates password."""
        headers = {"Authorization": f"Bearer {create_test_token(login_user)}"}
        payload = {
            "password_old": "testpassword123",
            "password_new": "NewPassword456!!",
            "password_new_repeat": "NewPassword456!!",
        }
        resp = client.put(f"{API}/me/password", json=payload, headers=headers)
        assert resp.status_code == 200

        # Verify old password no longer works
        resp = client.post(
            f"{API}/auth/login",
            data={
                "username": login_user.username,
                "password": "testpassword123",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 401

        # Verify new password works
        resp = client.post(
            f"{API}/auth/login",
            data={
                "username": login_user.username,
                "password": "NewPassword456!!",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200

    def test_user_cannot_set_password_with_wrong_old(
        self, client, db_session, login_user
    ):
        """PUT /me/password with wrong old password returns 400."""
        headers = {"Authorization": f"Bearer {create_test_token(login_user)}"}
        payload = {
            "password_old": "wrongpassword",
            "password_new": "newpassword456",
            "password_new_repeat": "newpassword456",
        }
        resp = client.put(f"{API}/me/password", json=payload, headers=headers)
        assert resp.status_code == 400

    def test_password_mismatch_returns_400(
        self, client, db_session, login_user
    ):
        """Password and repeat must match."""
        headers = {"Authorization": f"Bearer {create_test_token(login_user)}"}
        payload = {
            "password_old": "testpassword123",
            "password_new": "newpassword456",
            "password_new_repeat": "different789",
        }
        resp = client.put(f"{API}/me/password", json=payload, headers=headers)
        assert resp.status_code == 400

    def test_new_password_same_as_old_returns_400(
        self, client, db_session, login_user
    ):
        """New password cannot be the same as old password."""
        headers = {"Authorization": f"Bearer {create_test_token(login_user)}"}
        payload = {
            "password_old": "testpassword123",
            "password_new": "testpassword123",
            "password_new_repeat": "testpassword123",
        }
        resp = client.put(f"{API}/me/password", json=payload, headers=headers)
        assert resp.status_code == 400


# ------------------------------------------------------------------
# Scenario D: User deletion
# ------------------------------------------------------------------


class TestUserDeletion:
    """Test user deletion cascade and anonymization."""

    def test_delete_user_anonymizes_record(
        self,
        client,
        db_session,
        system_user,
        mock_permission_allow,
        mock_redis_queues,
        auth_headers,
    ):
        """Deleting a user anonymizes username, email, removes password."""
        from models import User

        # Create user to be deleted
        payload = {
            "username": f"todelete_{uuid.uuid4().hex[:6]}",
            "email": f"todelete_{uuid.uuid4().hex[:6]}@example.com",
            "name": "To Delete",
            "status": "Active",
        }
        resp = client.post(f"{API}/users/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        user_id = resp.json()["id"]

        # Delete
        resp = client.delete(f"{API}/users/{user_id}", headers=auth_headers)
        assert resp.status_code == 200

        # Verify anonymization in DB
        user = (
            db_session.query(User).filter(User.id == uuid.UUID(user_id)).first()
        )
        assert user is not None
        assert user.username.startswith("deleted_")
        assert user.hashed_password is None
        assert user.status == "deleted"
        assert "@mail.mail" in user.email

    def test_delete_user_removes_related_records(
        self,
        client,
        db_session,
        system_user,
        mock_permission_allow,
        mock_redis_queues,
        auth_headers,
    ):
        """Deleting a user removes EventsUser, ObjectPermissions, Tags."""
        from models import ObjectPermission, User

        now = datetime.now(timezone.utc)

        # Create user
        user = User(
            id=uuid.uuid4(),
            username=f"reldelete_{uuid.uuid4().hex[:6]}",
            name="Related Delete",
            email=f"reldelete_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password="$2b$12$dummyhashvalue",
            status="Active",
            locale="de_DE",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(user)
        db_session.flush()

        # Create ObjectPermission for the user
        obj_perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Event",
            object_id=uuid.uuid4(),
            entity_id=user.id,
            entity_type="User",
            permission_key="object_read",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(obj_perm)
        db_session.flush()

        user_id = user.id
        {"Authorization": f"Bearer {create_test_token(user)}"}

        # Delete via API
        resp = client.delete(f"{API}/users/{user_id}", headers=auth_headers)
        assert resp.status_code == 200

        # Verify ObjectPermission was removed
        remaining = (
            db_session.query(ObjectPermission)
            .filter(
                ObjectPermission.entity_id == user_id,
                ObjectPermission.entity_type == "User",
            )
            .count()
        )
        assert remaining == 0

    def test_cannot_delete_system_user(
        self,
        client,
        db_session,
        system_user,
        mock_permission_allow,
        auth_headers,
    ):
        """Deleting the system user returns 403."""
        resp = client.delete(
            f"{API}/users/{system_user.id}", headers=auth_headers
        )
        assert resp.status_code == 403

    def test_cannot_delete_already_deleted_user(
        self,
        client,
        db_session,
        system_user,
        mock_permission_allow,
        mock_redis_queues,
        auth_headers,
    ):
        """Deleting an already-deleted user returns 403."""
        # Create and delete user
        payload = {
            "username": f"deldel_{uuid.uuid4().hex[:6]}",
            "email": f"deldel_{uuid.uuid4().hex[:6]}@example.com",
            "name": "Double Delete",
            "status": "Active",
        }
        resp = client.post(f"{API}/users/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        user_id = resp.json()["id"]

        # First delete
        resp = client.delete(f"{API}/users/{user_id}", headers=auth_headers)
        assert resp.status_code == 200

        # Second delete -> 403
        resp = client.delete(f"{API}/users/{user_id}", headers=auth_headers)
        assert resp.status_code == 403

    def test_create_user_duplicate_username_returns_409(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
    ):
        """Creating a user with duplicate username returns 409."""
        unique = uuid.uuid4().hex[:6]
        payload = {
            "username": f"dupuser_{unique}",
            "email": f"dupuser_{unique}@example.com",
            "name": "First User",
            "status": "Active",
        }
        resp = client.post(f"{API}/users/", json=payload, headers=auth_headers)
        assert resp.status_code == 201

        # Same username, different email
        payload2 = {
            "username": f"dupuser_{unique}",
            "email": f"dupuser_{unique}_2@example.com",
            "name": "Second User",
            "status": "Active",
        }
        resp = client.post(f"{API}/users/", json=payload2, headers=auth_headers)
        assert resp.status_code == 409

    def test_create_user_duplicate_email_returns_409(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
    ):
        """Creating a user with duplicate email returns 409."""
        unique = uuid.uuid4().hex[:6]
        payload = {
            "username": f"emaildup1_{unique}",
            "email": f"emaildup_{unique}@example.com",
            "name": "First User",
            "status": "Active",
        }
        resp = client.post(f"{API}/users/", json=payload, headers=auth_headers)
        assert resp.status_code == 201

        # Different username, same email
        payload2 = {
            "username": f"emaildup2_{unique}",
            "email": f"emaildup_{unique}@example.com",
            "name": "Second User",
            "status": "Active",
        }
        resp = client.post(f"{API}/users/", json=payload2, headers=auth_headers)
        assert resp.status_code == 409

    def test_delete_user_enqueues_vm_cleanup(
        self,
        client,
        db_session,
        system_user,
        mock_permission_allow,
        mock_redis_queues,
        auth_headers,
    ):
        """Deleting a user with VMs enqueues cleanup jobs."""
        from models import User, VirtualMachine
        from models.associations import user_vm_association_table

        now = datetime.now(timezone.utc)

        # Create user
        user = User(
            id=uuid.uuid4(),
            username=f"vmdelete_{uuid.uuid4().hex[:6]}",
            name="VM Delete User",
            email=f"vmdelete_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password="$2b$12$dummyhashvalue",
            status="Active",
            locale="de_DE",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(user)
        db_session.flush()

        # Create VM owned by user
        vm = VirtualMachine(
            id=uuid.uuid4(),
            name=f"vm-{uuid.uuid4().hex[:6]}",
            description="Test VM",
            status="running",
            proxmoxId=10001,
            proxmoxNode="pve-node-01",
            cpu=2,
            ram=4096,
            disk=32,
            prevent_delete=False,
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db_session.add(vm)
        db_session.flush()

        # Associate user with VM
        db_session.execute(
            user_vm_association_table.insert().values(
                user_id=user.id, vm_id=vm.id
            )
        )
        db_session.flush()

        # Delete user
        resp = client.delete(f"{API}/users/{user.id}", headers=auth_headers)
        assert resp.status_code == 200

        # Verify jobs were enqueued
        assert len(mock_redis_queues) > 0
