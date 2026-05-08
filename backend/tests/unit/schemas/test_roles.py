"""Tests for schemas/roles.py - Role schema validation."""

import uuid

from pydantic import ValidationError
import pytest

from schemas.roles import (
    RoleCreate,
    RoleKeyOnly,
    RoleNested,
    RoleUpdate,
    RoleUpdateObjectPermissions,
)


class TestRoleCreate:
    def test_valid_create(self):
        r = RoleCreate(name="Admin", key="admin_full")
        assert r.name == "Admin"
        assert r.key == "admin_full"
        assert r.protected is False

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            RoleCreate(key="test")

    def test_missing_key_raises(self):
        with pytest.raises(ValidationError):
            RoleCreate(name="Test")

    def test_protected_default(self):
        r = RoleCreate(name="Test", key="test")
        assert r.protected is False

    def test_optional_description(self):
        r = RoleCreate(name="Test", key="test", description="A role")
        assert r.description == "A role"


class TestRoleUpdate:
    def test_valid_update(self):
        u = RoleUpdate(name="Updated Role")
        assert u.name == "Updated Role"

    def test_all_optional(self):
        u = RoleUpdate()
        assert u.name is None
        assert u.description is None


class TestRoleNested:
    def test_valid_nested(self):
        n = RoleNested(key="admin_full", name="Admin")
        assert n.key == "admin_full"
        assert n.name == "Admin"


class TestRoleKeyOnly:
    def test_valid(self):
        k = RoleKeyOnly(key="lehrende")
        assert k.key == "lehrende"


class TestRoleUpdateObjectPermissions:
    def test_valid_update(self):
        op_ids = [uuid.uuid4(), uuid.uuid4()]
        u = RoleUpdateObjectPermissions(object_permissions=op_ids)
        assert len(u.object_permissions) == 2

    def test_missing_raises(self):
        with pytest.raises(ValidationError):
            RoleUpdateObjectPermissions()

    def test_empty_list(self):
        u = RoleUpdateObjectPermissions(object_permissions=[])
        assert u.object_permissions == []
