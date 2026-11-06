"""Tests for schemas/system.py - SystemSetting schema validation."""

import pytest
from pydantic import ValidationError
from schemas.system import (
    SystemSettingCreate,
    SystemSettingUpdate,
    SystemSettingValueType,
    SystemSettingVisibility,
    SystemSettingWithoutAudit,
)


class TestSystemSettingCreate:
    def test_valid_create(self):
        s = SystemSettingCreate(
            key="my.setting", value="hello", visibility="public"
        )
        assert s.key == "my.setting"
        assert s.value == "hello"
        assert s.visibility == SystemSettingVisibility.public

    def test_valid_key_patterns(self):
        for key in ["my.setting", "app_config", "v1.0", "feature.flags.beta"]:
            s = SystemSettingCreate(key=key, visibility="public")
            assert s.key == key

    def test_key_required(self):
        with pytest.raises(ValidationError):
            SystemSettingCreate(visibility="public")

    def test_value_none_default(self):
        s = SystemSettingCreate(key="test.key", visibility="public")
        assert s.value is None

    def test_value_string(self):
        s = SystemSettingCreate(
            key="str.key", value="hello", visibility="public"
        )
        assert s.value == "hello"

    def test_description_default_none(self):
        s = SystemSettingCreate(key="test.key", visibility="public")
        assert s.description is None

    def test_description_set(self):
        s = SystemSettingCreate(
            key="test.key",
            visibility="public",
            description="A setting",
        )
        assert s.description == "A setting"


class TestSystemSettingVisibility:
    def test_visibility_values(self):
        expected = {"public", "authenticated", "admins", "internal"}
        assert {v.value for v in SystemSettingVisibility} == expected

    def test_visibility_normalization_uppercase(self):
        s = SystemSettingCreate(key="test.key", visibility="PUBLIC")
        assert s.visibility == SystemSettingVisibility.public

    def test_visibility_normalization_mixed_case(self):
        s = SystemSettingCreate(key="test.key", visibility="Admins")
        assert s.visibility == SystemSettingVisibility.admins


class TestSystemSettingValueType:
    def test_value_type_members(self):
        expected = {
            "string",
            "integer",
            "float",
            "boolean",
            "object",
            "array",
            "null",
        }
        assert {v.value for v in SystemSettingValueType} == expected


class TestSystemSettingUpdate:
    def test_valid_update(self):
        u = SystemSettingUpdate(value="new-value")
        assert u.value == "new-value"

    def test_update_value_none(self):
        u = SystemSettingUpdate(value=None)
        assert u.value is None


class TestSystemSettingWithoutAudit:
    def test_valid(self):
        s = SystemSettingWithoutAudit(
            key="app.mode", value="production", type="string"
        )
        assert s.key == "app.mode"
        assert s.type == SystemSettingValueType.string
