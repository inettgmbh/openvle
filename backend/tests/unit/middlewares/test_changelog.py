"""Tests for middlewares/changelog.py - ChangelogMiddleware."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from models import Vendor


class TestChangelogMiddleware:
    def _make_middleware(self, model=None):
        """Create a ChangelogMiddleware instance."""
        from middlewares.changelog import ChangelogMiddleware

        return ChangelogMiddleware(model or Vendor)

    def _make_mock_request(
        self, method="GET", path_params=None, body=None, user_id=None
    ):
        """Create a mock request object for ChangelogMiddleware."""
        request = MagicMock()
        request.method = method
        request.path_params = path_params or {}

        # Make request.json() an async function
        async def mock_json():
            return body or {}

        request.json = mock_json

        if user_id:
            request.user = MagicMock()
            request.user.id = user_id
        else:
            request.user = MagicMock()
            request.user.id = uuid.uuid4()

        return request

    @pytest.mark.anyio
    async def test_skips_get_request(self, monkeypatch):
        """GET method results in no changelog being created."""
        mock_session = MagicMock()
        monkeypatch.setattr("middlewares.changelog.SessionLocal", lambda: mock_session)

        middleware = self._make_middleware()
        request = self._make_mock_request(method="GET")

        result = await middleware(request)
        assert result is None
        mock_session.add.assert_not_called()

    @pytest.mark.anyio
    async def test_skips_delete_request(self, monkeypatch):
        """DELETE method results in no changelog being created."""
        mock_session = MagicMock()
        monkeypatch.setattr("middlewares.changelog.SessionLocal", lambda: mock_session)

        middleware = self._make_middleware()
        request = self._make_mock_request(method="DELETE")

        result = await middleware(request)
        assert result is None
        mock_session.add.assert_not_called()

    @pytest.mark.anyio
    async def test_skips_create_no_id(self, monkeypatch):
        """POST without id in path_params results in no changelog."""
        mock_session = MagicMock()
        monkeypatch.setattr("middlewares.changelog.SessionLocal", lambda: mock_session)

        middleware = self._make_middleware()
        request = self._make_mock_request(
            method="POST",
            path_params={},
            body={"name": "New Vendor"},
        )

        result = await middleware(request)
        assert result is None
        mock_session.add.assert_not_called()

    @pytest.mark.anyio
    async def test_creates_changelog_for_put(
        self, monkeypatch, db_session, system_user
    ):
        """PUT with changed values creates a Changelog row."""
        now = datetime.now(timezone.utc)
        vendor = Vendor(
            id=uuid.uuid4(),
            name="Old Name",
            description="Old Desc",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(vendor)
        db_session.flush()

        monkeypatch.setattr("middlewares.changelog.SessionLocal", lambda: db_session)

        middleware = self._make_middleware()
        request = self._make_mock_request(
            method="PUT",
            path_params={"id": str(vendor.id)},
            body={"name": "New Name"},
            user_id=system_user.id,
        )

        await middleware(request)

        # Verify a Changelog was committed
        from models.changelog import Changelog

        changelogs = db_session.query(Changelog).all()
        # Should have at least one changelog with the vendor's id
        matching = [cl for cl in changelogs if cl.objectId == vendor.id]
        assert len(matching) >= 1
        assert "New Name" in matching[0].valueNew

    @pytest.mark.anyio
    async def test_skips_password_changes(self, monkeypatch):
        """Request body with hashed_password results in no changelog."""
        mock_session = MagicMock()
        monkeypatch.setattr("middlewares.changelog.SessionLocal", lambda: mock_session)

        middleware = self._make_middleware()
        request = self._make_mock_request(
            method="PUT",
            path_params={"id": str(uuid.uuid4())},
            body={"hashed_password": "newhash"},
        )

        result = await middleware(request)
        assert result is None
        mock_session.add.assert_not_called()

    @pytest.mark.anyio
    async def test_skips_when_no_changes(self, monkeypatch, db_session, system_user):
        """Same values result in no changelog being created."""
        now = datetime.now(timezone.utc)
        vendor = Vendor(
            id=uuid.uuid4(),
            name="Same Name",
            description="Same Desc",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(vendor)
        db_session.flush()

        monkeypatch.setattr("middlewares.changelog.SessionLocal", lambda: db_session)

        middleware = self._make_middleware()
        request = self._make_mock_request(
            method="PUT",
            path_params={"id": str(vendor.id)},
            body={"name": "Same Name"},  # no change
            user_id=system_user.id,
        )

        await middleware(request)

        from models.changelog import Changelog

        changelogs = (
            db_session.query(Changelog).filter(Changelog.objectId == vendor.id).all()
        )
        assert len(changelogs) == 0

    @pytest.mark.anyio
    async def test_handles_attribute_error(self, monkeypatch, db_session, system_user):
        """Non-existent attribute in request body does not crash."""
        now = datetime.now(timezone.utc)
        vendor = Vendor(
            id=uuid.uuid4(),
            name="Test",
            description="Desc",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(vendor)
        db_session.flush()

        monkeypatch.setattr("middlewares.changelog.SessionLocal", lambda: db_session)

        middleware = self._make_middleware()
        request = self._make_mock_request(
            method="PUT",
            path_params={"id": str(vendor.id)},
            body={"nonexistent_field": "value"},
            user_id=system_user.id,
        )

        # Should not raise - returns early on AttributeError
        await middleware(request)
