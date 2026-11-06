"""Tests for schemas/users.py - User schema validation."""

import pytest
from pydantic import ValidationError
from schemas.users import (
    UserCreate,
    UserLogin,
    UserSetPassword,
    UserUpdate,
    UserUpdatePassword,
    UserUpdateRoles,
)


class TestUserCreateSchema:
    def test_valid_user_create(self):
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            name="Test User",
            password="secret123",
            password_repeat="secret123",
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.status == "E-Mail-Pending"
        assert user.locale == "de_DE"

    def test_invalid_email_format_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="not-an-email",
                name="Test",
            )

    def test_internal_domain_email_accepted(self):
        """LenientEmailStr accepts internal domains like .local."""
        user = UserCreate(
            username="intern",
            email="admin@company.local",
        )
        assert user.email == "admin@company.local"

    def test_corp_domain_email_accepted(self):
        user = UserCreate(
            username="intern",
            email="user@intranet.corp",
        )
        assert user.email == "user@intranet.corp"

    def test_email_whitespace_stripped(self):
        user = UserCreate(
            username="strip",
            email="  test@example.com  ",
        )
        assert user.email == "test@example.com"

    def test_minimal_fields(self):
        user = UserCreate(
            username="minimal",
            email="min@test.com",
        )
        assert user.username == "minimal"
        assert user.password is None
        assert user.name is None
        assert user.description is None

    def test_description_set(self):
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            description="A system administrator",
        )
        assert user.description == "A system administrator"

    def test_default_status(self):
        user = UserCreate(
            username="testuser",
            email="test@test.com",
        )
        assert user.status == "E-Mail-Pending"

    def test_custom_locale(self):
        user = UserCreate(
            username="testuser",
            email="test@test.com",
            locale="en_US",
        )
        assert user.locale == "en_US"


class TestUserLoginSchema:
    def test_valid_login(self):
        login = UserLogin(username="admin", password="secret")
        assert login.username == "admin"
        assert login.password == "secret"

    def test_missing_username_raises(self):
        with pytest.raises(ValidationError):
            UserLogin(password="secret")

    def test_missing_password_raises(self):
        with pytest.raises(ValidationError):
            UserLogin(username="admin")


class TestUserUpdatePasswordSchema:
    def test_valid_password_update(self):
        pwd = UserUpdatePassword(
            password_old="old",
            password_new="new",
            password_new_repeat="new",
        )
        assert pwd.password_old == "old"
        assert pwd.password_new == "new"

    def test_missing_old_password_raises(self):
        with pytest.raises(ValidationError):
            UserUpdatePassword(password_new="new", password_new_repeat="new")


class TestUserSetPasswordSchema:
    def test_valid_set_password(self):
        sp = UserSetPassword(
            password_new="newpass",
            password_new_repeat="newpass",
        )
        assert sp.password_new == "newpass"
        assert sp.password_new_repeat == "newpass"

    def test_missing_password_new_raises(self):
        with pytest.raises(ValidationError):
            UserSetPassword(password_new_repeat="newpass")

    def test_missing_password_new_repeat_raises(self):
        with pytest.raises(ValidationError):
            UserSetPassword(password_new="newpass")


class TestUserUpdateSchema:
    def test_valid_update(self):
        u = UserUpdate(name="New Name", email="new@example.com")
        assert u.name == "New Name"

    def test_all_optional(self):
        u = UserUpdate()
        assert u.name is None
        assert u.email is None
        assert u.description is None

    def test_defaults(self):
        u = UserUpdate()
        assert u.status == "E-Mail-Pending"
        assert u.locale == "de_DE"

    def test_internal_domain_email_accepted(self):
        u = UserUpdate(email="user@myhost.local")
        assert u.email == "user@myhost.local"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            UserUpdate(email="@missing-local-part.com")


class TestUserUpdateRolesSchema:
    def test_valid_update(self):
        u = UserUpdateRoles(roles=[{"key": "admin_full"}])
        assert len(u.roles) == 1
        assert u.roles[0].key == "admin_full"

    def test_none_roles(self):
        u = UserUpdateRoles(roles=None)
        assert u.roles is None

    def test_empty_list(self):
        u = UserUpdateRoles(roles=[])
        assert u.roles == []
