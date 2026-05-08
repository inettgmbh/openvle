"""Tests for schemas/object_permissions.py - ObjectPermission schema validation."""

import uuid

import pytest

from core.exceptions import BadRequestError, InvalidFieldValue
from schemas.object_permissions import (
    FORBIDDEN_COMBINATIONS,
    GLOBAL_ONLY_PERMISSIONS,
    LEGACY_PERMISSION_CONSTRAINTS,
    DeactivatedObjectTypes,
    ObjectPermissionCreate,
    ObjectPermissionKeys,
)


def _make_op(**kwargs):
    defaults = {
        "object_type": "Course",
        "object_id": uuid.uuid4(),
        "entity_id": uuid.uuid4(),
        "entity_type": "User",
        "permission_key": "object_read",
    }
    defaults.update(kwargs)
    return ObjectPermissionCreate(**defaults)


class TestObjectPermissionCreate:
    def test_valid_create(self):
        op = _make_op()
        assert op.object_type == "Course"
        assert op.permission_key == "object_read"

    def test_required_fields(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ObjectPermissionCreate(
                entity_id=uuid.uuid4(),
                entity_type="User",
                permission_key="object_read",
            )

    def test_valid_global_permission_no_object_id(self):
        op = _make_op(object_id=None, permission_key="object_create")
        assert op.object_id is None

    def test_valid_object_level_permission(self):
        op = _make_op(
            object_type="Event",
            object_id=uuid.uuid4(),
            permission_key="object_read",
        )
        assert op.permission_key == "object_read"


class TestObjectPermissionValidation:
    def test_forbidden_type_tag_raises(self):
        """Tag object_type is entirely forbidden."""
        with pytest.raises(InvalidFieldValue):
            _make_op(object_type="Tag", permission_key="object_read")

    def test_forbidden_combination_activity_create_raises(self):
        """Activity + object_create is forbidden."""
        with pytest.raises(InvalidFieldValue):
            _make_op(
                object_type="Activity",
                object_id=None,
                permission_key="object_create",
            )

    def test_forbidden_combination_activity_update_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_op(
                object_type="Activity",
                object_id=None,
                permission_key="object_update",
            )

    def test_forbidden_combination_activity_delete_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_op(
                object_type="Activity",
                object_id=None,
                permission_key="object_delete",
            )

    def test_activity_read_allowed(self):
        """Activity + object_read is NOT forbidden."""
        op = _make_op(
            object_type="Activity",
            object_id=None,
            permission_key="object_read",
        )
        assert op.permission_key == "object_read"

    def test_global_only_permission_with_object_id_raises(self):
        for perm_key in GLOBAL_ONLY_PERMISSIONS:
            allowed_types = LEGACY_PERMISSION_CONSTRAINTS[perm_key]
            if isinstance(allowed_types, str):
                allowed_types = [allowed_types]
            with pytest.raises(BadRequestError):
                _make_op(
                    object_type=allowed_types[0],
                    object_id=uuid.uuid4(),
                    permission_key=perm_key,
                )

    def test_global_only_permission_without_object_id_passes(self):
        for perm_key in GLOBAL_ONLY_PERMISSIONS:
            allowed_types = LEGACY_PERMISSION_CONSTRAINTS[perm_key]
            if isinstance(allowed_types, str):
                allowed_types = [allowed_types]
            op = _make_op(
                object_type=allowed_types[0],
                object_id=None,
                permission_key=perm_key,
            )
            assert op.permission_key == perm_key

    def test_deactivated_type_with_object_id_raises(self):
        for dt in DeactivatedObjectTypes:
            with pytest.raises(InvalidFieldValue):
                _make_op(
                    object_type=dt.value,
                    object_id=uuid.uuid4(),
                    permission_key="object_read",
                )

    def test_deactivated_type_without_object_id_passes(self):
        op = _make_op(
            object_type="Activity",
            object_id=None,
            permission_key="object_read",
        )
        assert op.object_id is None

    def test_object_create_with_object_id_raises(self):
        with pytest.raises(BadRequestError):
            _make_op(
                object_type="Course",
                object_id=uuid.uuid4(),
                permission_key="object_create",
            )

    def test_object_create_without_object_id_passes(self):
        op = _make_op(
            object_type="Course",
            object_id=None,
            permission_key="object_create",
        )
        assert op.permission_key == "object_create"

    def test_legacy_key_wrong_type_raises(self):
        """object_set_password only allowed for User type."""
        with pytest.raises(BadRequestError):
            _make_op(
                object_type="Course",
                object_id=None,
                permission_key="object_set_password",
            )

    def test_legacy_key_correct_type_passes(self):
        op = _make_op(
            object_type="User",
            object_id=uuid.uuid4(),
            permission_key="object_set_password",
        )
        assert op.permission_key == "object_set_password"

    def test_legacy_key_multi_type_passes(self):
        """object_actions_start allowed for both VirtualMachine and Event."""
        for obj_type in ["VirtualMachine", "Event"]:
            op = _make_op(
                object_type=obj_type,
                object_id=uuid.uuid4(),
                permission_key="object_actions_start",
            )
            assert op.permission_key == "object_actions_start"

    def test_invalid_permission_key_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_op(
                object_type="Course",
                object_id=uuid.uuid4(),
                permission_key="nonexistent_key",
            )


class TestObjectPermissionEnums:
    def test_object_permission_keys_values(self):
        expected = {
            "object_full",
            "object_read",
            "object_create",
            "object_delete",
            "object_update",
        }
        assert {k.value for k in ObjectPermissionKeys} == expected

    def test_deactivated_object_types_contains_expected(self):
        values = {t.value for t in DeactivatedObjectTypes}
        assert "Activity" in values
        assert "Changelog" in values
        assert "Tag" in values
        assert "System" in values

    def test_forbidden_combinations_structure(self):
        assert FORBIDDEN_COMBINATIONS["Tag"] is None
        assert "object_create" in FORBIDDEN_COMBINATIONS["Activity"]

    def test_global_only_permissions_list(self):
        assert "object_templates_update" in GLOBAL_ONLY_PERMISSIONS
        assert "object_users_read" in GLOBAL_ONLY_PERMISSIONS
