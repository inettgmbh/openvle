"""Integration tests for /v{x}/tags/ endpoints."""

import uuid
from datetime import datetime, timezone

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_tag(db_session, system_user, sample_course):
    """Create a tag attached to sample_course in the test DB."""
    from models import Tag

    now = datetime.now(timezone.utc)
    tag = Tag(
        id=uuid.uuid4(),
        key="env",
        value="prod",
        objectId=sample_course.id,
        objectType="Course",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(tag)
    db_session.flush()
    return tag


@pytest.fixture()
def extra_tag(db_session, system_user, sample_course):
    """Create a second tag with a different key on the same course."""
    from models import Tag

    now = datetime.now(timezone.utc)
    tag = Tag(
        id=uuid.uuid4(),
        key="region",
        value="eu-west",
        objectId=sample_course.id,
        objectType="Course",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(tag)
    db_session.flush()
    return tag


class TestCreateTag:
    """POST /tags/ -- create a new tag."""

    def test_create_returns_201(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_course,
    ):
        payload = {
            "key": "tier",
            "value": "premium",
            "objectId": str(sample_course.id),
            "objectType": "Course",
        }
        resp = client.post(f"{API}/tags/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["key"] == "tier"
        assert data["value"] == "premium"
        assert data["objectId"] == str(sample_course.id)
        assert data["objectType"] == "Course"

    def test_create_unauthenticated_returns_401(self, client):
        payload = {
            "key": "env",
            "value": "dev",
            "objectId": str(uuid.uuid4()),
            "objectType": "Course",
        }
        resp = client.post(f"{API}/tags/", json=payload)
        assert resp.status_code in (401, 403)

    def test_create_permission_denied_returns_403(
        self, client, auth_headers, sample_course
    ):
        """Without mock_permission_allow, courses_update is denied."""
        payload = {
            "key": "env",
            "value": "staging",
            "objectId": str(sample_course.id),
            "objectType": "Course",
        }
        resp = client.post(f"{API}/tags/", json=payload, headers=auth_headers)
        assert resp.status_code == 403


class TestGetTags:
    """GET /tags/ -- list all tags (filtered by object permissions)."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_tag,
    ):
        resp = client.get(f"{API}/tags/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/tags/")
        assert resp.status_code in (401, 403)


class TestGetTagById:
    """GET /tags/{id} -- get single tag."""

    def test_returns_tag(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_tag,
    ):
        resp = client.get(f"{API}/tags/{sample_tag.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_tag.id)
        assert data["key"] == "env"
        assert data["value"] == "prod"
        assert data["objectType"] == "Course"

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/tags/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/tags/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(
        self, client, auth_headers, sample_tag
    ):
        """Without mock_permission_allow, courses_read is denied for the tagged object."""
        resp = client.get(f"{API}/tags/{sample_tag.id}", headers=auth_headers)
        assert resp.status_code == 403


class TestDeleteTag:
    """DELETE /tags/{id} -- delete tag."""

    def test_delete_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        mock_redis_queues,
        sample_tag,
    ):
        resp = client.delete(
            f"{API}/tags/{sample_tag.id}", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/tags/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/tags/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_delete_permission_denied_returns_403(
        self, client, auth_headers, sample_tag
    ):
        """Without mock_permission_allow, courses_update is denied for the tagged object."""
        resp = client.delete(
            f"{API}/tags/{sample_tag.id}", headers=auth_headers
        )
        assert resp.status_code == 403


class TestGetTagsForObject:
    """GET /tags/{objectType}/{objectId} -- tags for a specific object."""

    def test_returns_filtered_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_tag,
        sample_course,
    ):
        resp = client.get(
            f"{API}/tags/Course/{sample_course.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/tags/Course/{fake_id}")
        assert resp.status_code in (401, 403)


class TestGetTagsByKey:
    """GET /tags/{key}/ -- list tags by key."""

    def test_returns_tags_with_key(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_tag,
    ):
        resp = client.get(f"{API}/tags/env/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/tags/env/")
        assert resp.status_code in (401, 403)


class TestGetTagsByKeyValue:
    """GET /tags/{key}/{value}/ -- list tags by key and value."""

    def test_returns_tags_with_key_value(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_tag,
    ):
        resp = client.get(f"{API}/tags/env/prod/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/tags/env/prod/")
        assert resp.status_code in (401, 403)
