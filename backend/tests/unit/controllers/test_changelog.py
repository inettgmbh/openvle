"""Tests for controllers/changelog.py - CRUDChangelog operations."""

import uuid
from datetime import datetime, timezone

import pytest

from controllers.changelog import CRUDChangelog
from models import Application, ObjectPermission, Vendor
from models.changelog import Changelog
from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def sample_vendor_for_cl(db_session, system_user):
    now = datetime.now(timezone.utc)
    vendor = Vendor(
        id=uuid.uuid4(),
        name="CL Vendor",
        description="Vendor for changelog tests",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


@pytest.fixture()
def sample_app_for_cl(db_session, system_user, sample_vendor_for_cl):
    now = datetime.now(timezone.utc)
    app = Application(
        id=uuid.uuid4(),
        key="cl-app",
        name="CL App",
        vendor=sample_vendor_for_cl.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(app)
    db_session.flush()
    return app


class TestCreateForChanges:
    def setup_method(self):
        self.crud = CRUDChangelog(Changelog)

    def test_creates_changelog_from_diffs(
        self, db_session, system_user, sample_app_for_cl
    ):
        changes = [
            {"field": "name", "value_old": "Old Name", "value_new": "New Name"},
            {"field": "key", "value_old": "old-key", "value_new": "new-key"},
        ]
        result = self.crud._create_for_changes(
            db_session,
            object_type="Application",
            object_id=sample_app_for_cl.id,
            changes=changes,
            user_id=system_user.id,
        )
        assert result.object == "Application"
        assert result.objectId == sample_app_for_cl.id
        assert "name" in result.valueOld
        assert "name" in result.valueNew


class TestGetMultiAuth:
    def setup_method(self):
        self.crud = CRUDChangelog(Changelog)

    def test_returns_changelogs_for_authorized_objects(
        self, db_session, active_user, sample_app_for_cl
    ):
        """User with ObjectPermission sees changelogs for that object."""
        # Grant user permission on the app
        now = datetime.now(timezone.utc)
        perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Application",
            object_id=sample_app_for_cl.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(perm)
        db_session.flush()

        # Create a changelog for the app
        cl = Changelog(
            id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            valueOld="old",
            valueNew="new",
            object="Application",
            objectId=sample_app_for_cl.id,
            userId=active_user.id,
        )
        db_session.add(cl)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_multi_auth(db_session, request)
        cl_ids = [c.id for c in result["items"]]
        assert cl.id in cl_ids

    def test_returns_empty_for_no_permissions(
        self, db_session, active_user, sample_app_for_cl
    ):
        """User without permissions sees empty results."""
        cl = Changelog(
            id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            valueOld="old",
            valueNew="new",
            object="Application",
            objectId=sample_app_for_cl.id,
            userId=active_user.id,
        )
        db_session.add(cl)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_multi_auth(db_session, request)
        assert len(result["items"]) == 0


class TestGetChangelogsObjectAuth:
    def setup_method(self):
        self.crud = CRUDChangelog(Changelog)

    def test_returns_changelogs_for_object(
        self, db_session, active_user, mock_permission_allow, sample_app_for_cl
    ):
        cl = Changelog(
            id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            valueOld="old",
            valueNew="new",
            object="Application",
            objectId=sample_app_for_cl.id,
            userId=active_user.id,
        )
        db_session.add(cl)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_changelogs_object_auth(
            request,
            objectId=sample_app_for_cl.id,
            objectType="Application",
            db=db_session,
        )
        assert len(result["items"]) == 1
        assert result["items"][0].id == cl.id

    def test_invalid_object_type_raises(self, db_session, active_user):
        from core.exceptions import ModelNotFound

        request = create_mock_request(active_user)
        with pytest.raises(ModelNotFound):
            self.crud.get_changelogs_object_auth(
                request,
                objectId=uuid.uuid4(),
                objectType="FakeModel",
                db=db_session,
            )


class TestCreateForChangesExtended:
    def setup_method(self):
        self.crud = CRUDChangelog(Changelog)

    def test_create_for_changes_multiple_fields(
        self, db_session, system_user, sample_app_for_cl
    ):
        """Multiple field changes in one call are recorded."""
        changes = [
            {"field": "name", "value_old": "App A", "value_new": "App B"},
            {"field": "key", "value_old": "app-a", "value_new": "app-b"},
            {"field": "description", "value_old": "", "value_new": "New description"},
        ]
        result = self.crud._create_for_changes(
            db_session,
            object_type="Application",
            object_id=sample_app_for_cl.id,
            changes=changes,
            user_id=system_user.id,
        )
        assert result is not None
        assert "name" in result.valueOld
        assert "key" in result.valueOld
        assert "description" in result.valueNew

    def test_create_for_changes_no_changes(
        self, db_session, system_user, sample_app_for_cl
    ):
        """Empty changes list creates a changelog with empty values."""
        result = self.crud._create_for_changes(
            db_session,
            object_type="Application",
            object_id=sample_app_for_cl.id,
            changes=[],
            user_id=system_user.id,
        )
        assert result is not None
        # Empty dicts serialized as strings
        assert result.valueOld == "{}"
        assert result.valueNew == "{}"


class TestGetMultiAuthPagination:
    def setup_method(self):
        self.crud = CRUDChangelog(Changelog)

    def test_get_multi_auth_pagination(
        self, db_session, active_user, sample_app_for_cl
    ):
        """Verify pagination works when requesting changelogs."""
        now = datetime.now(timezone.utc)
        # Grant user permission on the app
        perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Application",
            object_id=sample_app_for_cl.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(perm)
        db_session.flush()

        # Create multiple changelogs
        for i in range(5):
            cl = Changelog(
                id=uuid.uuid4(),
                timestamp=datetime.now(timezone.utc),
                valueOld=f"old_{i}",
                valueNew=f"new_{i}",
                object="Application",
                objectId=sample_app_for_cl.id,
                userId=active_user.id,
            )
            db_session.add(cl)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_multi_auth(db_session, request, limit=2, page=1)
        assert len(result["items"]) == 2
        assert result["pageDetails"]["totalCount"] == 5

    def test_changelog_truncates_long_values(
        self, db_session, system_user, sample_app_for_cl
    ):
        """Very long values are truncated to 1500 chars by _create_for_changes."""
        long_value = "x" * 3000
        changes = [
            {"field": "description", "value_old": long_value, "value_new": long_value},
        ]
        result = self.crud._create_for_changes(
            db_session,
            object_type="Application",
            object_id=sample_app_for_cl.id,
            changes=changes,
            user_id=system_user.id,
        )
        # The code does str(values_old)[:1500], so result should be <= 1500
        assert len(result.valueOld) <= 1500
        assert len(result.valueNew) <= 1500
