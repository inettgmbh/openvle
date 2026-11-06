"""Tests for controllers/users.py - CRUDUser operations."""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from controllers.users import CRUDUser
from core.auth import get_password_hash
from core.exceptions import (
    BadRequestError,
    GuacamoleConnectionError,
    IncorrectCredentials,
    ObjectNotFound,
    ProtectedObjectError,
)
from models import (
    Changelog,
    Event,
    EventsUser,
    Language,
    Mail,
    MailAction,
    MailTemplate,
    ObjectPermission,
    Role,
    Tag,
    User,
    VirtualMachine,
)
from models.associations import (
    user_vm_association_table,
)
from schemas.users import (
    UserCreate,
    UserSetPassword,
    UserUpdate,
    UserUpdatePassword,
    UserUpdateRoles,
)

from tests.factories import SystemSettingFactory
from tests.helpers.mock_request import create_mock_request


class TestCRUDUserLookup:
    def setup_method(self):
        self.crud = CRUDUser(User)

    def test_get_by_username_found(self, db_session, active_user):
        result = self.crud.get_by_username(db_session, username="testuser")
        assert result is not None
        assert result.username == "testuser"

    def test_get_by_username_not_found_returns_none(
        self, db_session, system_user
    ):
        result = self.crud.get_by_username(db_session, username="nonexistent")
        assert result is None

    def test_get_by_email_found(self, db_session, active_user):
        result = self.crud.get_by_email(
            db_session, email="testuser@example.com"
        )
        assert result is not None
        assert result.email == "testuser@example.com"

    def test_get_by_email_not_found_returns_none(self, db_session, system_user):
        result = self.crud.get_by_email(db_session, email="nobody@example.com")
        assert result is None


class TestCRUDUserCreate:
    def setup_method(self):
        self.crud = CRUDUser(User)

    def test_create_hashes_password(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = UserCreate(
            username="newuser",
            email="new@example.com",
            name="New User",
            password="SecurePass12!!",
            password_repeat="SecurePass12!!",
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.hashed_password is not None
        assert result.hashed_password != "mysecret123"
        assert result.hashed_password.startswith("$2b$")

    def test_create_mismatched_passwords_raises(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = UserCreate(
            username="mismatch",
            email="mismatch@example.com",
            name="Mismatch",
            password="password1",
            password_repeat="password2",
        )
        with pytest.raises(BadRequestError):
            self.crud.create(db_session, request, obj_in=obj_in)

    def test_create_without_password(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = UserCreate(
            username="nopass",
            email="nopass@example.com",
            name="No Pass",
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.hashed_password is None


class TestCRUDUserRoles:
    def setup_method(self):
        self.crud = CRUDUser(User)

    def test_set_roles_system_user_raises(
        self, db_session, system_user, role_admin
    ):
        request = create_mock_request(system_user)
        obj_in = UserUpdateRoles(roles=[{"key": "admin_full"}])
        with pytest.raises((ProtectedObjectError, BadRequestError)):
            self.crud.set_roles(
                system_user.id, db_session, request, obj_in=obj_in
            )

    def test_set_roles_assigns_single_role(
        self, db_session, active_user, system_user, role_admin, role_teacher
    ):
        request = create_mock_request(active_user)
        result = self.crud.set_roles(
            active_user.id,
            db_session,
            request,
            obj_in=UserUpdateRoles(roles=[{"key": "admin_full"}]),
        )
        role_keys = [r.key for r in result.roles]
        assert role_keys == ["admin_full"]

    def test_set_roles_multiple_roles(
        self, db_session, active_user, system_user, role_admin, role_teacher
    ):
        request = create_mock_request(active_user)
        result = self.crud.set_roles(
            active_user.id,
            db_session,
            request,
            obj_in=UserUpdateRoles(
                roles=[{"key": "admin_full"}, {"key": "lehrende"}]
            ),
        )
        role_keys = [r.key for r in result.roles]
        assert "admin_full" in role_keys
        assert "lehrende" in role_keys
        assert len(result.roles) == 2

    def test_set_roles_nonexistent_role_raises(
        self, db_session, active_user, system_user
    ):
        request = create_mock_request(active_user)
        obj_in = UserUpdateRoles(roles=[{"key": "nonexistent_role"}])
        with pytest.raises(ObjectNotFound):
            self.crud.set_roles(
                active_user.id, db_session, request, obj_in=obj_in
            )

    def test_set_roles_deleted_user_raises(
        self, db_session, system_user, role_admin
    ):
        deleted = _create_user(
            db_session,
            system_user,
            "deleted_setroles",
            "delsr@example.com",
            status="deleted",
        )
        request = create_mock_request(deleted)
        obj_in = UserUpdateRoles(roles=[{"key": "admin_full"}])
        with pytest.raises(ProtectedObjectError):
            self.crud.set_roles(deleted.id, db_session, request, obj_in=obj_in)


class TestCRUDUserDelete:
    def setup_method(self):
        self.crud = CRUDUser(User)

    def test_delete_anonymizes_user_data(
        self, db_session, active_user, system_user
    ):
        user_id = active_user.id
        self.crud.delete(db_session, id=user_id)
        deleted = db_session.get(User, user_id)
        assert deleted is not None  # Soft delete: user still exists
        assert deleted.username.startswith("deleted_")
        assert "test" not in deleted.email

    def test_delete_system_user_raises(self, db_session, system_user):
        with pytest.raises((ProtectedObjectError, BadRequestError)):
            self.crud.delete(db_session, id=system_user.id)


class TestCRUDUserPassword:
    def setup_method(self):
        self.crud = CRUDUser(User)

    def test_update_password_success(
        self, db_session, active_user, system_user
    ):
        # First set a known password
        old_password = "oldpass123"
        active_user.hashed_password = get_password_hash(old_password)
        db_session.flush()

        request = create_mock_request(active_user)
        obj_in = UserUpdatePassword(
            password_old=old_password,
            password_new="SecurePass12!!",
            password_new_repeat="SecurePass12!!",
        )
        result = self.crud.update_password(db_session, request, obj_in=obj_in)
        assert result is not None
        # Verify the new password works
        from core.auth import verify_password

        assert verify_password("SecurePass12!!", result.hashed_password)

    def test_update_password_wrong_old_raises(
        self, db_session, active_user, system_user
    ):
        active_user.hashed_password = get_password_hash("realpass")
        db_session.flush()

        request = create_mock_request(active_user)
        obj_in = UserUpdatePassword(
            password_old="wrongpass",
            password_new="newpass",
            password_new_repeat="newpass",
        )
        with pytest.raises((IncorrectCredentials, BadRequestError)):
            self.crud.update_password(db_session, request, obj_in=obj_in)

    def test_update_password_mismatch_raises(
        self, db_session, active_user, system_user
    ):
        old_password = "oldpass"
        active_user.hashed_password = get_password_hash(old_password)
        db_session.flush()

        request = create_mock_request(active_user)
        obj_in = UserUpdatePassword(
            password_old=old_password,
            password_new="new1",
            password_new_repeat="new2",
        )
        with pytest.raises(BadRequestError):
            self.crud.update_password(db_session, request, obj_in=obj_in)


# ---------------------------------------------------------------------------
# Fixture: seed password policy settings into the test DB
# ---------------------------------------------------------------------------


@pytest.fixture()
def password_settings(db_session):
    """Ensure the six passwords.* SystemSettings exist with the required values.

    Uses upsert logic because these rows are already seeded by the Alembic
    migration; a plain INSERT would raise a duplicate-key error.
    """
    from models import SystemSetting

    settings_data = [
        ("passwords.min", "8", "authenticated", "Minimale Passwortlänge"),
        ("passwords.max", "64", "authenticated", "Maximale Passwortlänge"),
        (
            "passwords.lowercase.min",
            "2",
            "authenticated",
            "Mindestanzahl Kleinbuchstaben",
        ),
        (
            "passwords.uppercase.min",
            "2",
            "authenticated",
            "Mindestanzahl Großbuchstaben",
        ),
        (
            "passwords.numbers.min",
            "2",
            "authenticated",
            "Mindestanzahl Ziffern",
        ),
        (
            "passwords.special.min",
            "2",
            "authenticated",
            "Mindestanzahl Sonderzeichen",
        ),
    ]

    for key, value, visibility, description in settings_data:
        row = db_session.query(SystemSetting).filter_by(key=key).first()
        if row is None:
            SystemSettingFactory(
                key=key,
                value=value,
                visibility=visibility,
                description=description,
            )
        elif row.value != value:
            row.value = value
    db_session.flush()


# ---------------------------------------------------------------------------
# TestCRUDUserPasswordValidation
# ---------------------------------------------------------------------------


class TestCRUDUserPasswordValidation:
    """Tests for validate_password() enforcement in create / update_password / set_password."""

    def setup_method(self):
        self.crud = CRUDUser(User)

    # --- create ---

    def test_create_valid_password_succeeds(
        self, db_session, active_user, password_settings
    ):
        request = create_mock_request(active_user)
        obj_in = UserCreate(
            username="validpwuser",
            email="validpw@example.com",
            name="Valid PW",
            password="SecurePass12!!",
            password_repeat="SecurePass12!!",
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.hashed_password is not None

    def test_create_password_too_short_raises(
        self, db_session, active_user, password_settings
    ):
        request = create_mock_request(active_user)
        obj_in = UserCreate(
            username="shortpw",
            email="shortpw@example.com",
            name="Short PW",
            password="Ab1!",
            password_repeat="Ab1!",
        )
        with pytest.raises(BadRequestError):
            self.crud.create(db_session, request, obj_in=obj_in)

    def test_create_password_missing_uppercase_raises(
        self, db_session, active_user, password_settings
    ):
        request = create_mock_request(active_user)
        obj_in = UserCreate(
            username="noupcase",
            email="noupcase@example.com",
            name="No Upper",
            password="securepass12!!",
            password_repeat="securepass12!!",
        )
        with pytest.raises(BadRequestError):
            self.crud.create(db_session, request, obj_in=obj_in)

    def test_create_password_missing_digits_raises(
        self, db_session, active_user, password_settings
    ):
        request = create_mock_request(active_user)
        obj_in = UserCreate(
            username="nodigits",
            email="nodigits@example.com",
            name="No Digits",
            password="SecurePass!!",
            password_repeat="SecurePass!!",
        )
        with pytest.raises(BadRequestError):
            self.crud.create(db_session, request, obj_in=obj_in)

    def test_create_password_missing_special_raises(
        self, db_session, active_user, password_settings
    ):
        request = create_mock_request(active_user)
        obj_in = UserCreate(
            username="nospecial",
            email="nospecial@example.com",
            name="No Special",
            password="SecurePass12",
            password_repeat="SecurePass12",
        )
        with pytest.raises(BadRequestError):
            self.crud.create(db_session, request, obj_in=obj_in)

    # --- update_password ---

    def test_update_password_invalid_raises(
        self, db_session, active_user, system_user, password_settings
    ):
        old_password = "OldPass12!!"
        active_user.hashed_password = get_password_hash(old_password)
        db_session.flush()

        request = create_mock_request(active_user)
        obj_in = UserUpdatePassword(
            password_old=old_password,
            password_new="tooshort",
            password_new_repeat="tooshort",
        )
        with pytest.raises(BadRequestError):
            self.crud.update_password(db_session, request, obj_in=obj_in)

    # --- set_password ---

    def test_set_password_invalid_raises(
        self, db_session, active_user, system_user, password_settings
    ):
        active_user.hashed_password = get_password_hash("OldPass12!!")
        db_session.flush()

        request = create_mock_request(system_user)
        obj_in = UserSetPassword(
            password_new="tooshort",
            password_new_repeat="tooshort",
        )
        with pytest.raises(BadRequestError):
            self.crud.set_password(
                db_session, request, obj_in=obj_in, user_id=active_user.id
            )


# ---------------------------------------------------------------------------
# Helper to create common test data inline
# ---------------------------------------------------------------------------


def _create_user(
    db,
    system_user,
    username,
    email,
    status="Active",
    hashed_password="$2b$12$dummyhash",
):
    """Create a user record for testing."""
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        username=username,
        name=f"Name {username}",
        email=email,
        hashed_password=hashed_password,
        status=status,
        locale="de_DE",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(user)
    db.flush()
    return user


def _create_role(db, key, system_user):
    """Create a Role record."""
    now = datetime.now(timezone.utc)
    role = Role(
        id=uuid.uuid4(),
        name=key,
        key=key,
        protected=False,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(role)
    db.flush()
    return role


def _create_event(db, system_user, name, slug, status_id, course_id):
    """Create an Event record."""
    now = datetime.now(timezone.utc)
    event = Event(
        id=uuid.uuid4(),
        name=name,
        slug=slug,
        dateStart=date(2026, 3, 1),
        dateEnd=date(2026, 3, 31),
        guacamole=True,
        status=status_id,
        course=course_id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(event)
    db.flush()
    return event


def _create_vm(db, system_user, name):
    """Create a VirtualMachine record."""
    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name=name,
        cpu=2,
        ram=2048,
        disk=20,
        status="running",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(vm)
    db.flush()
    return vm


# ---------------------------------------------------------------------------
# TestCRUDUserGetMulti
# ---------------------------------------------------------------------------


class TestCRUDUserGetMulti:
    """Tests for CRUDUser.get_multi() - custom override with filtering."""

    def setup_method(self):
        self.crud = CRUDUser(User)

    def test_get_multi_excludes_system_user(
        self, db_session, system_user, active_user
    ):
        result = self.crud.get_multi(db_session)
        usernames = [u.username for u in result["items"]]
        assert "system" not in usernames

    def test_get_multi_excludes_deleted_users(
        self, db_session, system_user, active_user
    ):
        _create_user(
            db_session,
            system_user,
            "deleted_abc12345",
            "del@example.com",
            status="deleted",
        )
        result = self.crud.get_multi(db_session)
        usernames = [u.username for u in result["items"]]
        assert "deleted_abc12345" not in usernames

    def test_get_multi_returns_active_users(
        self, db_session, system_user, active_user
    ):
        _create_user(db_session, system_user, "user2", "user2@example.com")
        result = self.crud.get_multi(db_session)
        usernames = [u.username for u in result["items"]]
        assert "testuser" in usernames
        assert "user2" in usernames

    def test_get_multi_returns_paginated_result(
        self, db_session, system_user, active_user
    ):
        result = self.crud.get_multi(db_session)
        assert "pageDetails" in result
        assert "items" in result
        assert result["pageDetails"]["totalCount"] >= 1

    def test_get_multi_with_search(self, db_session, system_user, active_user):
        _create_user(db_session, system_user, "alice", "alice@example.com")
        result = self.crud.get_multi(
            db_session, search_field="username", search_value="alice"
        )
        usernames = [u.username for u in result["items"]]
        assert "alice" in usernames
        assert "testuser" not in usernames

    def test_get_multi_with_limit(self, db_session, system_user, active_user):
        for i in range(5):
            _create_user(
                db_session, system_user, f"multi{i}", f"multi{i}@example.com"
            )
        result = self.crud.get_multi(db_session, limit=2, page=1)
        assert len(result["items"]) <= 2


# ---------------------------------------------------------------------------
# TestCRUDUserUpdate
# ---------------------------------------------------------------------------


class TestCRUDUserUpdate:
    """Tests for CRUDUser.update() - custom override that also syncs Guacamole status."""

    def setup_method(self):
        self.crud = CRUDUser(User)

    def test_update_basic_fields(self, db_session, active_user, system_user):
        request = create_mock_request(active_user)
        obj_in = UserUpdate(name="Updated Name")
        result = self.crud.update(
            active_user.id, db_session, request, obj_in=obj_in
        )
        assert result.name == "Updated Name"

    def test_update_system_user_raises(self, db_session, system_user):
        request = create_mock_request(system_user)
        obj_in = UserUpdate(name="Hacked System")
        with pytest.raises(ProtectedObjectError):
            self.crud.update(system_user.id, db_session, request, obj_in=obj_in)

    def test_update_deleted_user_raises(self, db_session, system_user):
        deleted = _create_user(
            db_session,
            system_user,
            "deleted_xyz",
            "delxyz@example.com",
            status="deleted",
        )
        request = create_mock_request(system_user)
        obj_in = UserUpdate(name="Should Fail")
        with pytest.raises(ProtectedObjectError):
            self.crud.update(deleted.id, db_session, request, obj_in=obj_in)

    def test_update_external_user_cannot_change_name(
        self, db_session, system_user
    ):
        """External users (no hashed_password) may not update name or email."""
        ext_user = _create_user(
            db_session,
            system_user,
            "extuser",
            "ext@example.com",
            hashed_password=None,
        )
        request = create_mock_request(ext_user)
        obj_in = UserUpdate(name="New Name")
        with pytest.raises(BadRequestError):
            self.crud.update(ext_user.id, db_session, request, obj_in=obj_in)

    def test_update_external_user_cannot_change_email(
        self, db_session, system_user
    ):
        ext_user = _create_user(
            db_session,
            system_user,
            "extuser2",
            "ext2@example.com",
            hashed_password=None,
        )
        request = create_mock_request(ext_user)
        obj_in = UserUpdate(email="new@example.com")
        with pytest.raises(BadRequestError):
            self.crud.update(ext_user.id, db_session, request, obj_in=obj_in)

    @patch("controllers.users.guacamole_connect")
    def test_update_ban_user_locks_guacamole(
        self, mock_guac_connect, db_session, active_user, system_user
    ):
        """Banning a user should call guacamole lock_user."""
        mock_guac = MagicMock()
        mock_guac.detail_user.return_value = {"username": active_user.username}
        mock_guac.lock_user.return_value = True
        mock_guac_connect.return_value = mock_guac

        request = create_mock_request(active_user)
        obj_in = UserUpdate(status="Banned")
        result = self.crud.update(
            active_user.id, db_session, request, obj_in=obj_in
        )

        assert result.status == "Banned"
        mock_guac.lock_user.assert_called_once_with(active_user.username)

    @patch("controllers.users.guacamole_connect")
    def test_update_unban_user_unlocks_guacamole(
        self, mock_guac_connect, db_session, system_user
    ):
        """Unbanning a user should call guacamole unlock_user."""
        banned_user = _create_user(
            db_session,
            system_user,
            "banned",
            "banned@example.com",
            status="Banned",
        )
        mock_guac = MagicMock()
        mock_guac.detail_user.return_value = {"username": banned_user.username}
        mock_guac.unlock_user.return_value = True
        mock_guac_connect.return_value = mock_guac

        request = create_mock_request(banned_user)
        obj_in = UserUpdate(status="Active")
        result = self.crud.update(
            banned_user.id, db_session, request, obj_in=obj_in
        )

        assert result.status == "Active"
        mock_guac.unlock_user.assert_called_once_with(banned_user.username)

    @patch("controllers.users.guacamole_connect")
    def test_update_status_change_guacamole_unavailable_raises(
        self, mock_guac_connect, db_session, active_user, system_user
    ):
        """If Guacamole is unreachable during a status change, GuacamoleConnectionError is raised."""
        mock_guac_connect.return_value = None

        request = create_mock_request(active_user)
        obj_in = UserUpdate(status="Banned")
        with pytest.raises(GuacamoleConnectionError):
            self.crud.update(active_user.id, db_session, request, obj_in=obj_in)

    def test_update_no_status_change_skips_guacamole(
        self, db_session, active_user, system_user
    ):
        """When status does not change, no Guacamole interaction should happen."""
        request = create_mock_request(active_user)
        obj_in = UserUpdate(name="Still Active", status="Active")
        # Should succeed without any Guacamole mock because status is unchanged
        result = self.crud.update(
            active_user.id, db_session, request, obj_in=obj_in
        )
        assert result.name == "Still Active"


# ---------------------------------------------------------------------------
# TestCRUDUserUpdateRoles
# ---------------------------------------------------------------------------


class TestCRUDUserUpdateRoles:
    """Tests for CRUDUser.update_roles() - appends roles to existing ones."""

    def setup_method(self):
        self.crud = CRUDUser(User)

    def test_update_roles_appends_new_role(
        self, db_session, active_user, system_user, role_admin, role_teacher
    ):
        """update_roles should add the new role on top of existing ones."""
        # First set an initial role
        request = create_mock_request(active_user)
        self.crud.set_roles(
            active_user.id,
            db_session,
            request,
            obj_in=UserUpdateRoles(roles=[{"key": "admin_full"}]),
        )

        # Now update_roles to add teacher
        result = self.crud.update_roles(
            active_user.id,
            db_session,
            request,
            obj_in=UserUpdateRoles(roles=[{"key": "lehrende"}]),
        )
        role_keys = [r.key for r in result.roles]
        assert "admin_full" in role_keys
        assert "lehrende" in role_keys

    def test_update_roles_system_user_raises(
        self, db_session, system_user, role_admin
    ):
        request = create_mock_request(system_user)
        obj_in = UserUpdateRoles(roles=[{"key": "admin_full"}])
        with pytest.raises(ProtectedObjectError):
            self.crud.update_roles(
                system_user.id, db_session, request, obj_in=obj_in
            )

    def test_update_roles_deleted_user_raises(
        self, db_session, system_user, role_admin
    ):
        deleted = _create_user(
            db_session,
            system_user,
            "deleted_roleu",
            "delr@example.com",
            status="deleted",
        )
        request = create_mock_request(deleted)
        obj_in = UserUpdateRoles(roles=[{"key": "admin_full"}])
        with pytest.raises(ProtectedObjectError):
            self.crud.update_roles(
                deleted.id, db_session, request, obj_in=obj_in
            )

    def test_update_roles_nonexistent_role_raises(
        self, db_session, active_user, system_user
    ):
        request = create_mock_request(active_user)
        obj_in = UserUpdateRoles(roles=[{"key": "nonexistent_role"}])
        with pytest.raises(ObjectNotFound):
            self.crud.update_roles(
                active_user.id, db_session, request, obj_in=obj_in
            )


# ---------------------------------------------------------------------------
# TestCRUDUserSetPassword
# ---------------------------------------------------------------------------


class TestCRUDUserSetPassword:
    """Tests for CRUDUser.set_password() - admin action to directly set a user's password."""

    def setup_method(self):
        self.crud = CRUDUser(User)

    def test_set_password_success(self, db_session, active_user, system_user):
        active_user.hashed_password = get_password_hash("oldpassword")
        db_session.flush()

        request = create_mock_request(system_user)
        obj_in = UserSetPassword(
            password_new="SecurePass12!!",
            password_new_repeat="SecurePass12!!",
        )
        result = self.crud.set_password(
            db_session, request, obj_in=obj_in, user_id=active_user.id
        )
        from core.auth import verify_password

        assert verify_password("SecurePass12!!", result.hashed_password)

    def test_set_password_mismatch_raises(
        self, db_session, active_user, system_user
    ):
        active_user.hashed_password = get_password_hash("existing")
        db_session.flush()

        request = create_mock_request(system_user)
        obj_in = UserSetPassword(
            password_new="pass1",
            password_new_repeat="pass2",
        )
        with pytest.raises(BadRequestError):
            self.crud.set_password(
                db_session, request, obj_in=obj_in, user_id=active_user.id
            )

    def test_set_password_system_user_raises(self, db_session, system_user):
        request = create_mock_request(system_user)
        obj_in = UserSetPassword(
            password_new="newpass",
            password_new_repeat="newpass",
        )
        with pytest.raises(ProtectedObjectError):
            self.crud.set_password(
                db_session, request, obj_in=obj_in, user_id=system_user.id
            )

    def test_set_password_deleted_user_raises(self, db_session, system_user):
        deleted = _create_user(
            db_session,
            system_user,
            "deleted_setpw",
            "delsp@example.com",
            status="deleted",
        )
        request = create_mock_request(system_user)
        obj_in = UserSetPassword(
            password_new="newpass",
            password_new_repeat="newpass",
        )
        with pytest.raises(ProtectedObjectError):
            self.crud.set_password(
                db_session, request, obj_in=obj_in, user_id=deleted.id
            )

    def test_set_password_external_user_raises(self, db_session, system_user):
        """External users (no hashed_password) cannot have their password set."""
        ext_user = _create_user(
            db_session,
            system_user,
            "extset",
            "extset@example.com",
            hashed_password=None,
        )
        request = create_mock_request(system_user)
        obj_in = UserSetPassword(
            password_new="newpass",
            password_new_repeat="newpass",
        )
        with pytest.raises(BadRequestError):
            self.crud.set_password(
                db_session, request, obj_in=obj_in, user_id=ext_user.id
            )

    def test_set_password_nonexistent_user_raises(
        self, db_session, system_user
    ):
        request = create_mock_request(system_user)
        obj_in = UserSetPassword(
            password_new="newpass",
            password_new_repeat="newpass",
        )
        with pytest.raises(ObjectNotFound):
            self.crud.set_password(
                db_session, request, obj_in=obj_in, user_id=uuid.uuid4()
            )


# ---------------------------------------------------------------------------
# TestCRUDUserDeletePreview
# ---------------------------------------------------------------------------


def _get_or_create_mail_template(db, system_user):
    """Return an existing MailTemplate or create one with minimal dependencies."""
    tpl = db.query(MailTemplate).first()
    if tpl:
        return tpl
    now = datetime.now(timezone.utc)
    lang = db.query(Language).first()
    if not lang:
        lang = Language(
            id=uuid.uuid4(),
            key="de_DE",
            name="Deutsch",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db.add(lang)
        db.flush()
    action = db.query(MailAction).first()
    if not action:
        action = MailAction(
            id=uuid.uuid4(),
            name="Test Action",
            description="Test",
            slug=f"test_{uuid.uuid4().hex[:6]}",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db.add(action)
        db.flush()
    tpl = MailTemplate(
        id=uuid.uuid4(),
        name=f"Test Template {uuid.uuid4().hex[:4]}",
        subject="Test Subject",
        contentHTML="<p>html</p>",
        contentPlain="plain",
        language=lang.id,
        mail_action=action.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(tpl)
    db.flush()
    return tpl


def _create_mail(db, user, system_user, subject="Test Mail"):
    now = datetime.now(timezone.utc)
    tpl = _get_or_create_mail_template(db, system_user)
    mail = Mail(
        id=uuid.uuid4(),
        subject=subject,
        fromName="System",
        fromMail="system@example.com",
        toMail=user.email,
        sendStatus="sent",
        templateId=tpl.id,
        replyTo="noreply@example.com",
        user_id=user.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(mail)
    db.flush()
    return mail


def _create_tag(db, user):
    now = datetime.now(timezone.utc)
    tag = Tag(
        id=uuid.uuid4(),
        key="test-key",
        value="test-value",
        objectId=user.id,
        objectType="User",
        createdAt=now,
        updatedAt=now,
        createdById=user.id,
        updatedById=user.id,
    )
    db.add(tag)
    db.flush()
    return tag


def _create_changelog(db, user):
    entry = Changelog(
        id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        object="User",
        objectId=user.id,
        userId=user.id,
    )
    db.add(entry)
    db.flush()
    return entry


def _create_object_permission(db, user, system_user):
    now = datetime.now(timezone.utc)
    perm = ObjectPermission(
        id=uuid.uuid4(),
        object_type="User",
        object_id=user.id,
        entity_id=system_user.id,
        entity_type="User",
        permission_key="object_read",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(perm)
    db.flush()
    return perm


class TestCRUDUserDeletePreview:
    """Tests for CRUDUser.delete_preview() - returns structured preview of all objects deleted with the user."""

    def setup_method(self):
        self.crud = CRUDUser(User)

    def test_delete_preview_response_shape(
        self, db_session, active_user, system_user
    ):
        """Response has stats and all item list fields."""
        result = self.crud.delete_preview(db_session, id=active_user.id)
        assert hasattr(result, "stats")
        assert hasattr(result, "virtual_machines")
        assert hasattr(result, "connections")
        assert hasattr(result, "mails")
        assert hasattr(result, "changelogs")
        assert hasattr(result, "object_permissions")
        assert hasattr(result, "tags")
        assert hasattr(result, "event_memberships")

    def test_delete_preview_empty_when_no_related_objects(
        self, db_session, active_user, system_user
    ):
        result = self.crud.delete_preview(db_session, id=active_user.id)
        assert result.virtual_machines.items == []
        assert result.connections.items == []
        assert result.mails.items == []
        assert result.changelogs.items == []
        assert result.object_permissions.items == []
        assert result.tags.items == []
        assert result.event_memberships.items == []
        assert result.virtual_machines.truncated is False
        assert result.mails.truncated is False
        assert result.stats.virtual_machines == 0
        assert result.stats.mails == 0

    def test_delete_preview_includes_associated_vms(
        self, db_session, active_user, system_user
    ):
        """VMs associated via the user_vm association table appear in preview."""
        vm = _create_vm(db_session, system_user, "preview-vm")
        db_session.execute(
            user_vm_association_table.insert().values(
                user_id=active_user.id, vm_id=vm.id
            )
        )
        db_session.flush()

        result = self.crud.delete_preview(db_session, id=active_user.id)
        vm_ids = [v.id for v in result.virtual_machines.items]
        assert vm.id in vm_ids
        assert result.stats.virtual_machines == 1

    def test_delete_preview_includes_created_vms(
        self, db_session, active_user, system_user
    ):
        """VMs created by the user (createdById) appear in preview."""
        vm = _create_vm(db_session, active_user, "created-vm")
        result = self.crud.delete_preview(db_session, id=active_user.id)
        vm_ids = [v.id for v in result.virtual_machines.items]
        assert vm.id in vm_ids

    def test_delete_preview_includes_mails(
        self, db_session, active_user, system_user
    ):
        mail = _create_mail(db_session, active_user, system_user, "Hello User")
        result = self.crud.delete_preview(db_session, id=active_user.id)
        mail_ids = [m.id for m in result.mails.items]
        assert mail.id in mail_ids
        assert result.stats.mails == 1
        assert result.mails.items[0].subject == "Hello User"
        assert result.mails.items[0].send_status == "sent"

    def test_delete_preview_includes_changelogs(
        self, db_session, active_user, system_user
    ):
        entry = _create_changelog(db_session, active_user)
        result = self.crud.delete_preview(db_session, id=active_user.id)
        log_ids = [c.id for c in result.changelogs.items]
        assert entry.id in log_ids
        assert result.stats.changelogs == 1

    def test_delete_preview_includes_object_permissions(
        self, db_session, active_user, system_user
    ):
        perm = _create_object_permission(db_session, active_user, system_user)
        result = self.crud.delete_preview(db_session, id=active_user.id)
        perm_ids = [p.id for p in result.object_permissions.items]
        assert perm.id in perm_ids
        assert result.stats.object_permissions >= 1

    def test_delete_preview_includes_tags(
        self, db_session, active_user, system_user
    ):
        tag = _create_tag(db_session, active_user)
        result = self.crud.delete_preview(db_session, id=active_user.id)
        tag_ids = [t.id for t in result.tags.items]
        assert tag.id in tag_ids
        assert result.stats.tags == 1

    def test_delete_preview_stats_count_event_memberships(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
    ):
        now = datetime.now(timezone.utc)
        event = _create_event(
            db_session,
            system_user,
            "Preview Event",
            "prev-evt",
            event_statuses["Geplant"].id,
            sample_course.id,
        )
        role = _create_role(
            db_session, f"student_{uuid.uuid4().hex[:6]}", system_user
        )
        membership = EventsUser(
            id=uuid.uuid4(),
            event_id=event.id,
            user_id=active_user.id,
            role_id=role.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(membership)
        db_session.flush()

        result = self.crud.delete_preview(db_session, id=active_user.id)
        assert result.stats.event_memberships == 1
        assert len(result.event_memberships.items) == 1
        em = result.event_memberships.items[0]
        assert em.id == event.id
        assert em.name == "Preview Event"
        assert em.status == "Geplant"
        assert em.role.id == role.id
        assert em.role.name == role.name

    def test_delete_preview_stats_total_counts_match_lists(
        self, db_session, active_user, system_user
    ):
        """Stats totals should match list lengths when under the 100-item limit."""
        _create_mail(db_session, active_user, system_user, "Mail 1")
        _create_mail(db_session, active_user, system_user, "Mail 2")
        _create_tag(db_session, active_user)
        _create_changelog(db_session, active_user)

        result = self.crud.delete_preview(db_session, id=active_user.id)
        assert result.stats.mails == len(result.mails.items)
        assert result.stats.tags == len(result.tags.items)
        assert result.stats.changelogs == len(result.changelogs.items)
        assert result.mails.truncated is False
        assert result.tags.truncated is False
        assert result.changelogs.truncated is False

    def test_delete_preview_truncates_mails_at_limit(
        self, db_session, active_user, system_user
    ):
        """101 mails -> stats.mails == 101, items count capped at 100, truncated == True."""
        for i in range(101):
            _create_mail(db_session, active_user, system_user, f"Mail {i}")

        result = self.crud.delete_preview(db_session, id=active_user.id)
        assert result.stats.mails == 101
        assert len(result.mails.items) == 100
        assert result.mails.truncated is True

    def test_delete_preview_nonexistent_user_raises(
        self, db_session, system_user
    ):
        with pytest.raises(ObjectNotFound):
            self.crud.delete_preview(db_session, id=uuid.uuid4())


# ---------------------------------------------------------------------------
# TestCRUDUserGetUserEvents
# ---------------------------------------------------------------------------


class TestCRUDUserGetUserEvents:
    """Tests for CRUDUser.get_user_events() - returns events the user is enrolled in."""

    def setup_method(self):
        self.crud = CRUDUser(User)

    def test_get_user_events_returns_enrolled_events(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
        role_student,
    ):
        status_id = event_statuses["Aktiv"].id
        event = _create_event(
            db_session,
            system_user,
            "Enrolled Evt",
            "enr001",
            status_id,
            sample_course.id,
        )
        # Enroll user in event
        eu = EventsUser(
            id=uuid.uuid4(),
            user_id=active_user.id,
            event_id=event.id,
            role_id=role_student.id,
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(eu)
        db_session.flush()

        result = self.crud.get_user_events(db_session, id=active_user.id)
        assert result["pageDetails"]["totalCount"] == 1
        event_ids = [e.id for e in result["items"]]
        assert event.id in event_ids

    def test_get_user_events_empty_when_not_enrolled(
        self, db_session, active_user, system_user
    ):
        result = self.crud.get_user_events(db_session, id=active_user.id)
        assert result["pageDetails"]["totalCount"] == 0
        assert result["items"] == []

    def test_get_user_events_excludes_other_users_events(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
        role_student,
    ):
        other_user = _create_user(
            db_session, system_user, "other", "other@example.com"
        )
        status_id = event_statuses["Aktiv"].id
        event = _create_event(
            db_session,
            system_user,
            "Other Evt",
            "oth001",
            status_id,
            sample_course.id,
        )
        eu = EventsUser(
            id=uuid.uuid4(),
            user_id=other_user.id,
            event_id=event.id,
            role_id=role_student.id,
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(eu)
        db_session.flush()

        result = self.crud.get_user_events(db_session, id=active_user.id)
        assert result["pageDetails"]["totalCount"] == 0

    def test_get_user_events_has_role_ids_attribute(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
        role_teacher,
    ):
        """Events returned should have a role_ids attribute set."""
        status_id = event_statuses["Geplant"].id
        event = _create_event(
            db_session,
            system_user,
            "Role Evt",
            "rol001",
            status_id,
            sample_course.id,
        )
        eu = EventsUser(
            id=uuid.uuid4(),
            user_id=active_user.id,
            event_id=event.id,
            role_id=role_teacher.id,
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(eu)
        db_session.flush()

        result = self.crud.get_user_events(db_session, id=active_user.id)
        assert len(result["items"]) == 1
        evt = result["items"][0]
        assert hasattr(evt, "role_ids")
        assert role_teacher.id in evt.role_ids

    def test_get_user_events_pagination(
        self,
        db_session,
        active_user,
        system_user,
        event_statuses,
        sample_course,
        role_student,
    ):
        status_id = event_statuses["Aktiv"].id
        for i in range(3):
            event = _create_event(
                db_session,
                system_user,
                f"PagEvt{i}",
                f"pag{i:03d}",
                status_id,
                sample_course.id,
            )
            eu = EventsUser(
                id=uuid.uuid4(),
                user_id=active_user.id,
                event_id=event.id,
                role_id=role_student.id,
                createdAt=datetime.now(timezone.utc),
                updatedAt=datetime.now(timezone.utc),
                createdById=system_user.id,
                updatedById=system_user.id,
            )
            db_session.add(eu)
        db_session.flush()

        result = self.crud.get_user_events(
            db_session, id=active_user.id, limit=2, page=1
        )
        assert len(result["items"]) == 2
        assert result["pageDetails"]["totalCount"] == 3


# ---------------------------------------------------------------------------
# TestCRUDUserGetUserVMs
# ---------------------------------------------------------------------------


class TestCRUDUserGetUserVMs:
    """Tests for CRUDUser.get_user_vms() - returns VMs assigned to or created by the user."""

    def setup_method(self):
        self.crud = CRUDUser(User)

    def test_get_user_vms_via_association(
        self, db_session, active_user, system_user
    ):
        """VMs linked through the user_vm association table should be returned."""
        vm = _create_vm(db_session, system_user, "assoc-vm")
        db_session.execute(
            user_vm_association_table.insert().values(
                user_id=active_user.id, vm_id=vm.id
            )
        )
        db_session.flush()

        result = self.crud.get_user_vms(db_session, id=active_user.id)
        vm_ids = [v.id for v in result["items"]]
        assert vm.id in vm_ids

    def test_get_user_vms_via_created_by(
        self, db_session, active_user, system_user
    ):
        """VMs where createdById matches the user should be returned."""
        vm = _create_vm(db_session, active_user, "created-vm")
        result = self.crud.get_user_vms(db_session, id=active_user.id)
        vm_ids = [v.id for v in result["items"]]
        assert vm.id in vm_ids

    def test_get_user_vms_empty_when_none(
        self, db_session, active_user, system_user
    ):
        result = self.crud.get_user_vms(db_session, id=active_user.id)
        assert result["pageDetails"]["totalCount"] == 0
        assert result["items"] == []

    def test_get_user_vms_excludes_other_users(
        self, db_session, active_user, system_user
    ):
        other_user = _create_user(
            db_session, system_user, "vmother", "vmoth@example.com"
        )
        vm = _create_vm(db_session, system_user, "other-vm")
        db_session.execute(
            user_vm_association_table.insert().values(
                user_id=other_user.id, vm_id=vm.id
            )
        )
        db_session.flush()

        result = self.crud.get_user_vms(db_session, id=active_user.id)
        vm_ids = [v.id for v in result["items"]]
        assert vm.id not in vm_ids

    def test_get_user_vms_deduplicates(
        self, db_session, active_user, system_user
    ):
        """A VM that is both created by AND associated to the user should appear only once."""
        vm = _create_vm(db_session, active_user, "dedup-vm")
        db_session.execute(
            user_vm_association_table.insert().values(
                user_id=active_user.id, vm_id=vm.id
            )
        )
        db_session.flush()

        result = self.crud.get_user_vms(db_session, id=active_user.id)
        vm_ids = [v.id for v in result["items"]]
        assert vm_ids.count(vm.id) == 1

    def test_get_user_vms_pagination(
        self, db_session, active_user, system_user
    ):
        for i in range(4):
            vm = _create_vm(db_session, system_user, f"pag-vm-{i}")
            db_session.execute(
                user_vm_association_table.insert().values(
                    user_id=active_user.id, vm_id=vm.id
                )
            )
        db_session.flush()

        result = self.crud.get_user_vms(
            db_session, id=active_user.id, limit=2, page=1
        )
        assert len(result["items"]) == 2
        assert result["pageDetails"]["totalCount"] == 4

    def test_get_user_vms_returns_paginated_result(
        self, db_session, active_user, system_user
    ):
        result = self.crud.get_user_vms(db_session, id=active_user.id)
        assert "pageDetails" in result
        assert "items" in result
