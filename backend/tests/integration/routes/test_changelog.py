"""Integration tests for /v{x}/changelogs/ endpoints."""

import uuid
from datetime import datetime, timezone

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_changelog(db_session, system_user):
    """Create a changelog entry in the test DB."""
    from models.changelog import Changelog

    cl = Changelog(
        id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        valueOld="{'name': 'old'}",
        valueNew="{'name': 'new'}",
        object="Language",
        objectId=uuid.uuid4(),
        userId=system_user.id,
    )
    db_session.add(cl)
    db_session.flush()
    return cl


class TestGetChangelogs:
    """GET /changelogs/ — list all changelogs."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_changelog,
    ):
        """Returns 200 with paginated shape. Items may be empty because
        get_multi_auth filters by ObjectPermissions."""
        resp = client.get(f"{API}/changelogs/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/changelogs/")
        assert resp.status_code in (401, 403)

    def test_permission_denied(self, client, auth_headers):
        """Without mock_permission_allow, changelogs_read is denied."""
        resp = client.get(f"{API}/changelogs/", headers=auth_headers)
        assert resp.status_code == 403


class TestGetChangelogById:
    """GET /changelogs/{id} — get single changelog."""

    def test_returns_changelog(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_changelog,
    ):
        resp = client.get(
            f"{API}/changelogs/{sample_changelog.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_changelog.id)

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/changelogs/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404


class TestGetChangelogsForObject:
    """GET /changelogs/{objectType}/{objectId} — changelogs for an object."""

    def test_returns_filtered_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_changelog,
    ):
        resp = client.get(
            f"{API}/changelogs/Language/{sample_changelog.objectId}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/changelogs/Language/{fake_id}")
        assert resp.status_code in (401, 403)
