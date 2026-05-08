"""Tests for controllers/system.py - CRUDSystemSetting operations."""

import uuid
from datetime import datetime, timezone

import pytest

from controllers.system import CRUDSystemSetting
from core.exceptions import InvalidFieldValue, ProtectedObjectError
from models import SystemSetting as SystemSettingModel
from schemas.system import (
    SystemSettingUpdate,
    SystemSettingValueType,
    SystemSettingVisibility,
)
from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def public_setting(db_session, system_user):
    now = datetime.now(timezone.utc)
    setting = SystemSettingModel(
        id=uuid.uuid4(),
        key="app.public.name",
        value="TestApp",
        visibility="public",
        description="Application name",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(setting)
    db_session.flush()
    return setting


@pytest.fixture()
def auth_setting(db_session, system_user):
    now = datetime.now(timezone.utc)
    setting = SystemSettingModel(
        id=uuid.uuid4(),
        key="app.auth.timeout",
        value="480",
        visibility="authenticated",
        description="Auth timeout",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(setting)
    db_session.flush()
    return setting


@pytest.fixture()
def internal_setting(db_session, system_user):
    now = datetime.now(timezone.utc)
    setting = SystemSettingModel(
        id=uuid.uuid4(),
        key="app.internal.secret",
        value="secret-value",
        visibility="internal",
        description="Internal secret",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(setting)
    db_session.flush()
    return setting


@pytest.fixture()
def admin_setting(db_session, system_user):
    now = datetime.now(timezone.utc)
    setting = SystemSettingModel(
        id=uuid.uuid4(),
        key="app.admin.feature",
        value="true",
        visibility="admins",
        description="Admin feature flag",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(setting)
    db_session.flush()
    return setting


class TestCRUDSystemSettingUpdate:
    def setup_method(self):
        self.crud = CRUDSystemSetting(SystemSettingModel)

    def test_update_value(self, db_session, active_user, public_setting):
        request = create_mock_request(active_user)
        obj_in = SystemSettingUpdate(value="NewAppName")
        result = self.crud.update(public_setting.id, db_session, request, obj_in=obj_in)
        assert result.value == "NewAppName"

    def test_update_prevents_type_change(self, db_session, active_user, auth_setting):
        """Updating a string value with a dict should raise."""
        request = create_mock_request(active_user)
        obj_in = SystemSettingUpdate(value={"nested": "object"})
        with pytest.raises(InvalidFieldValue):
            self.crud.update(auth_setting.id, db_session, request, obj_in=obj_in)

    def test_update_internal_raises(self, db_session, active_user, internal_setting):
        """Internal settings cannot be updated."""
        request = create_mock_request(active_user)
        obj_in = SystemSettingUpdate(value="hacked")
        with pytest.raises(ProtectedObjectError):
            self.crud.update(internal_setting.id, db_session, request, obj_in=obj_in)


class TestGetMultiVisibility:
    def setup_method(self):
        self.crud = CRUDSystemSetting(SystemSettingModel)

    def test_filters_public_only(
        self, db_session, system_user, public_setting, auth_setting
    ):
        result = self.crud.get_multi_visibility(
            db_session, allowed={SystemSettingVisibility.public}
        )
        keys = [item.key for item in result["items"]]
        assert "app.public.name" in keys
        assert "app.auth.timeout" not in keys

    def test_filters_public_and_authenticated(
        self, db_session, system_user, public_setting, auth_setting, internal_setting
    ):
        result = self.crud.get_multi_visibility(
            db_session,
            allowed={
                SystemSettingVisibility.public,
                SystemSettingVisibility.authenticated,
            },
        )
        keys = [item.key for item in result["items"]]
        assert "app.public.name" in keys
        assert "app.auth.timeout" in keys
        assert "app.internal.secret" not in keys


class TestGetFiltered:
    def setup_method(self):
        self.crud = CRUDSystemSetting(SystemSettingModel)

    def test_unauthenticated_sees_public_only(
        self, db_session, system_user, public_setting, auth_setting
    ):
        result = self.crud.get_filtered(db_session, current_user=False)
        keys = [item.key for item in result.items]
        assert "app.public.name" in keys
        assert "app.auth.timeout" not in keys

    def test_authenticated_sees_public_and_auth(
        self, db_session, active_user, public_setting, auth_setting, internal_setting
    ):
        result = self.crud.get_filtered(
            db_session, current_user=active_user, permissionSet=False
        )
        keys = [item.key for item in result.items]
        assert "app.public.name" in keys
        assert "app.auth.timeout" in keys
        assert "app.internal.secret" not in keys

    def test_admin_sees_all(
        self,
        db_session,
        active_user,
        public_setting,
        auth_setting,
        internal_setting,
        admin_setting,
    ):
        result = self.crud.get_filtered(
            db_session, current_user=active_user, permissionSet=True
        )
        keys = [item.key for item in result.items]
        assert "app.public.name" in keys
        assert "app.auth.timeout" in keys
        assert "app.internal.secret" in keys
        assert "app.admin.feature" in keys


class TestHelpers:
    def setup_method(self):
        self.crud = CRUDSystemSetting(SystemSettingModel)

    def test_json_type_string(self):
        assert self.crud._json_type("hello") == SystemSettingValueType.string

    def test_json_type_integer(self):
        assert self.crud._json_type("42") == SystemSettingValueType.integer

    def test_json_type_boolean(self):
        assert self.crud._json_type("true") == SystemSettingValueType.boolean

    def test_json_type_null(self):
        assert self.crud._json_type(None) == SystemSettingValueType.null

    def test_json_type_object(self):
        assert self.crud._json_type('{"key": "val"}') == SystemSettingValueType.object

    def test_json_type_array(self):
        assert self.crud._json_type("[1, 2]") == SystemSettingValueType.array

    def test_trim_value_string(self):
        assert self.crud._trim_value("  hello  ") == "hello"

    def test_trim_value_nested(self):
        result = self.crud._trim_value({"key": "  val  "})
        assert result == {"key": "val"}

    def test_pretty_format_object(self):
        result = self.crud._pretty_format(
            '{"key": "val"}', SystemSettingValueType.object
        )
        assert '"key"' in result
        assert '"val"' in result


class TestNormalizeResult:
    """Tests for CRUDSystemSetting._normalize_result()."""

    def setup_method(self):
        self.crud = CRUDSystemSetting(SystemSettingModel)

    def test_normalize_dict_with_items_and_page_details(self):
        """Should extract pageDetails and items from a dict result."""
        page_details = {"totalCount": 5, "pageCount": 1, "currentPage": 1}
        items = [{"key": "a"}, {"key": "b"}]
        result_dict = {"pageDetails": page_details, "items": items}

        pd, rows = self.crud._normalize_result(result_dict)
        assert pd == page_details
        assert rows == items

    def test_normalize_dict_with_none_items(self):
        """When items is None in a dict result, rows should default to empty list."""
        result_dict = {"pageDetails": {"totalCount": 0}, "items": None}

        pd, rows = self.crud._normalize_result(result_dict)
        assert pd == {"totalCount": 0}
        assert rows == []

    def test_normalize_dict_without_items_key(self):
        """When items key is missing, rows should default to empty list."""
        result_dict = {"pageDetails": {"totalCount": 0}}

        pd, rows = self.crud._normalize_result(result_dict)
        assert rows == []

    def test_normalize_dict_without_page_details(self):
        """When pageDetails key is missing, page_details should be None."""
        result_dict = {"items": [{"key": "a"}]}

        pd, rows = self.crud._normalize_result(result_dict)
        assert pd is None
        assert len(rows) == 1

    def test_normalize_object_with_attributes(self):
        """Should extract pageDetails and items from an object with attributes."""

        class MockResult:
            def __init__(self):
                self.pageDetails = {"totalCount": 3}
                self.items = ["item1", "item2", "item3"]

        result_obj = MockResult()
        pd, rows = self.crud._normalize_result(result_obj)
        assert pd == {"totalCount": 3}
        assert rows == ["item1", "item2", "item3"]

    def test_normalize_object_without_attributes(self):
        """Object without pageDetails or items attributes should return None and empty list."""

        class EmptyResult:
            pass

        result_obj = EmptyResult()
        pd, rows = self.crud._normalize_result(result_obj)
        assert pd is None
        assert rows == []

    def test_normalize_object_with_none_items(self):
        """Object with items=None should return empty list for rows."""

        class NoneItemsResult:
            def __init__(self):
                self.pageDetails = {"totalCount": 0}
                self.items = None

        result_obj = NoneItemsResult()
        pd, rows = self.crud._normalize_result(result_obj)
        assert rows == []


class TestToPublicItem:
    """Tests for CRUDSystemSetting._to_public_item()."""

    def setup_method(self):
        self.crud = CRUDSystemSetting(SystemSettingModel)

    def test_converts_setting_to_public_item(
        self, db_session, system_user, public_setting
    ):
        """Should convert a SystemSetting model instance to a SystemSettingWithoutAudit."""
        result = self.crud._to_public_item(public_setting)

        assert result.key == "app.public.name"
        assert result.value == "TestApp"
        assert result.type == SystemSettingValueType.string

    def test_public_item_excludes_audit_fields(
        self, db_session, system_user, public_setting
    ):
        """The public item should not contain audit fields like createdAt, updatedAt."""
        result = self.crud._to_public_item(public_setting)

        assert not hasattr(result, "createdAt")
        assert not hasattr(result, "updatedAt")
        assert not hasattr(result, "createdById")
        assert not hasattr(result, "updatedById")
        assert not hasattr(result, "visibility")
        assert not hasattr(result, "description")

    def test_public_item_with_integer_value(
        self, db_session, system_user, auth_setting
    ):
        """Should correctly handle integer-typed setting values."""
        result = self.crud._to_public_item(auth_setting)

        assert result.key == "app.auth.timeout"
        assert result.value == "480"
        assert result.type == SystemSettingValueType.integer

    def test_public_item_with_internal_setting(
        self, db_session, system_user, internal_setting
    ):
        """Should still produce a public item from an internal setting (visibility filtering is separate)."""
        result = self.crud._to_public_item(internal_setting)

        assert result.key == "app.internal.secret"
        assert result.value == "secret-value"

    def test_public_item_with_empty_value(self, db_session, system_user):
        """Should handle a setting with empty string value."""
        now = datetime.now(timezone.utc)
        setting = SystemSettingModel(
            id=uuid.uuid4(),
            key="app.empty.setting",
            value="",
            visibility="public",
            description="Empty value setting",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(setting)
        db_session.flush()

        result = self.crud._to_public_item(setting)
        assert result.key == "app.empty.setting"
        assert result.value == ""

    def test_public_item_returns_correct_schema_type(
        self, db_session, system_user, public_setting
    ):
        """The returned object should be an instance of SystemSettingWithoutAudit."""
        from schemas.system import SystemSettingWithoutAudit

        result = self.crud._to_public_item(public_setting)
        assert isinstance(result, SystemSettingWithoutAudit)
