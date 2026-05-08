"""Integration tests for /v{x}/courses/ endpoints."""

import uuid
from datetime import datetime, timezone

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_course(db_session, system_user):
    """Create a course in the test DB."""
    from models import Course

    now = datetime.now(timezone.utc)
    course = Course(
        id=uuid.uuid4(),
        name="Test Course",
        description="A test course",
        guacamole=True,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(course)
    db_session.flush()
    return course


class TestCreateCourse:
    """POST /courses/ -- create a new course."""

    def test_create_course_returns_201(
        self, client, auth_headers, mock_permission_allow
    ):
        payload = {
            "name": "New Course",
            "description": "A brand new course",
            "guacamole": False,
        }
        resp = client.post(f"{API}/courses/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Course"
        assert data["description"] == "A brand new course"
        assert data["guacamole"] is False
        assert "id" in data

    def test_create_unauthenticated_returns_401(self, client):
        payload = {
            "name": "No Auth Course",
            "description": "desc",
        }
        resp = client.post(f"{API}/courses/", json=payload)
        assert resp.status_code in (401, 403)

    def test_create_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, courses_create is denied."""
        payload = {
            "name": "Denied Course",
            "description": "desc",
        }
        resp = client.post(f"{API}/courses/", json=payload, headers=auth_headers)
        assert resp.status_code == 403


class TestGetCourses:
    """GET /courses/ -- list all courses."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_course,
    ):
        resp = client.get(f"{API}/courses/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/courses/")
        assert resp.status_code in (401, 403)


class TestGetCourseById:
    """GET /courses/{id} -- get single course."""

    def test_returns_course(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_course,
    ):
        resp = client.get(f"{API}/courses/{sample_course.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_course.id)
        assert data["name"] == sample_course.name
        assert data["description"] == sample_course.description
        assert data["guacamole"] == sample_course.guacamole

    def test_not_found_returns_404(self, client, auth_headers, mock_permission_allow):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/courses/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/courses/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers, sample_course):
        """Without mock_permission_allow, courses_read is denied."""
        resp = client.get(f"{API}/courses/{sample_course.id}", headers=auth_headers)
        assert resp.status_code == 403


class TestUpdateCourse:
    """PUT /courses/{id} -- update a course."""

    def test_update_course_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_course,
    ):
        payload = {
            "name": "Updated Course",
            "description": "Updated description",
            "guacamole": False,
        }
        resp = client.put(
            f"{API}/courses/{sample_course.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Course"
        assert data["description"] == "Updated description"
        assert data["guacamole"] is False

    def test_update_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        payload = {"name": "Ghost Course", "description": "Does not exist"}
        resp = client.put(
            f"{API}/courses/{fake_id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_update_unauthenticated_returns_401(self, client):
        """Use non-existent ID so ChangelogMiddleware exits early
        (it runs as a dependency before auth check)."""
        fake_id = uuid.uuid4()
        payload = {"name": "No Auth Course"}
        resp = client.put(f"{API}/courses/{fake_id}", json=payload)
        assert resp.status_code in (401, 403)


class TestDeleteCourse:
    """DELETE /courses/{id} -- delete a course."""

    def test_delete_course_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_course,
    ):
        resp = client.delete(f"{API}/courses/{sample_course.id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/courses/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/courses/{fake_id}")
        assert resp.status_code in (401, 403)


class TestGetCourseTemplates:
    """GET /courses/{id}/templates -- list templates for a course."""

    def test_returns_empty_template_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_course,
    ):
        resp = client.get(
            f"{API}/courses/{sample_course.id}/templates",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert data["items"] == []

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/courses/{fake_id}/templates")
        assert resp.status_code in (401, 403)
