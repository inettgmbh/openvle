"""Integration tests for /v{x}/object-permissions/ endpoints."""

import uuid

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_object_permission(db_session, system_user, active_user):
    """Create an object permission in the test DB."""
    from tests.factories.permission_factory import ObjectPermissionFactory

    return ObjectPermissionFactory(
        object_type="Course",
        object_id=uuid.uuid4(),
        entity_type="User",
        entity_id=active_user.id,
        permission_key="object_full",
        createdById=system_user.id,
        updatedById=system_user.id,
    )


@pytest.fixture()
def sample_course_for_perm(db_session, system_user):
    """Create a course that can be referenced by object permissions."""
    from models import Course
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    course = Course(
        id=uuid.uuid4(),
        name="Permission Test Course",
        description="Course for object permission tests",
        guacamole=True,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(course)
    db_session.flush()
    return course


class TestCreateObjectPermission:
    """POST /object-permissions/ -- create a new object permission."""

    def test_create_returns_201(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        active_user,
        sample_course_for_perm,
    ):
        payload = {
            "object_type": "Course",
            "object_id": str(sample_course_for_perm.id),
            "entity_type": "User",
            "entity_id": str(active_user.id),
            "permission_key": "object_full",
        }
        resp = client.post(
            f"{API}/object-permissions/",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["object_type"] == "Course"
        assert data["permission_key"] == "object_full"
        assert data["entity_id"] == str(active_user.id)

    def test_create_unauthenticated_returns_401(self, client):
        payload = {
            "object_type": "Course",
            "object_id": str(uuid.uuid4()),
            "entity_type": "User",
            "entity_id": str(uuid.uuid4()),
            "permission_key": "object_full",
        }
        resp = client.post(f"{API}/object-permissions/", json=payload)
        assert resp.status_code in (401, 403)

    def test_create_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, object_permissions_create is denied."""
        payload = {
            "object_type": "Course",
            "object_id": str(uuid.uuid4()),
            "entity_type": "User",
            "entity_id": str(uuid.uuid4()),
            "permission_key": "object_full",
        }
        resp = client.post(
            f"{API}/object-permissions/",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestGetObjectPermissions:
    """GET /object-permissions/ -- list all object permissions."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_object_permission,
    ):
        resp = client.get(f"{API}/object-permissions/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/object-permissions/")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, object_permissions_read is denied."""
        resp = client.get(f"{API}/object-permissions/", headers=auth_headers)
        assert resp.status_code == 403


class TestGetObjectPermissionsByTypeAndId:
    """GET /object-permissions/{object_type}/{object_id} -- list for specific object."""

    def test_returns_filtered_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_object_permission,
    ):
        resp = client.get(
            f"{API}/object-permissions/Course/{sample_object_permission.object_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/object-permissions/Course/{fake_id}")
        assert resp.status_code in (401, 403)


class TestGetObjectPermissionById:
    """GET /object-permissions/{id} -- get single object permission."""

    def test_returns_permission(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_object_permission,
    ):
        resp = client.get(
            f"{API}/object-permissions/{sample_object_permission.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_object_permission.id)
        assert data["object_type"] == "Course"
        assert data["permission_key"] == "object_full"

    def test_not_found_returns_404(self, client, auth_headers, mock_permission_allow):
        fake_id = uuid.uuid4()
        resp = client.get(
            f"{API}/object-permissions/{fake_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/object-permissions/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(
        self, client, auth_headers, sample_object_permission
    ):
        """Without mock_permission_allow, object_permissions_read is denied."""
        resp = client.get(
            f"{API}/object-permissions/{sample_object_permission.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestDeleteObjectPermission:
    """DELETE /object-permissions/{id} -- delete object permission."""

    def test_delete_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_object_permission,
    ):
        resp = client.delete(
            f"{API}/object-permissions/{sample_object_permission.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(
            f"{API}/object-permissions/{fake_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/object-permissions/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_delete_permission_denied_returns_403(
        self, client, auth_headers, sample_object_permission
    ):
        """Without mock_permission_allow, object_permissions_delete is denied."""
        resp = client.delete(
            f"{API}/object-permissions/{sample_object_permission.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403
