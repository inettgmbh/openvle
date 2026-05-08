"""Integration tests for /v{x}/templates/ endpoints."""

import uuid
from datetime import datetime, timezone

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_template(db_session, system_user):
    """Create a template in the test DB."""
    from models import Template

    now = datetime.now(timezone.utc)
    template = Template(
        id=uuid.uuid4(),
        name="test-template",
        description="A test template",
        status="ready",
        cpu=2,
        ram=4096,
        disk=20,
        prevent_delete=False,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(template)
    db_session.flush()
    return template


class TestGetTemplates:
    """GET /templates/ -- list all templates."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_template,
    ):
        resp = client.get(f"{API}/templates/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/templates/")
        assert resp.status_code in (401, 403)


class TestGetTemplateById:
    """GET /templates/{id} -- get single template."""

    def test_returns_template(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_template,
    ):
        resp = client.get(
            f"{API}/templates/{sample_template.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_template.id)
        assert data["name"] == sample_template.name
        assert data["cpu"] == sample_template.cpu
        assert data["ram"] == sample_template.ram
        assert data["disk"] == sample_template.disk

    def test_not_found_returns_404(self, client, auth_headers, mock_permission_allow):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/templates/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/templates/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers, sample_template):
        """Without mock_permission_allow, templates_read is denied."""
        resp = client.get(
            f"{API}/templates/{sample_template.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestUpdateTemplate:
    """PUT /templates/{id} -- update a template."""

    def test_update_template_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        mock_redis_queues,
        sample_template,
    ):
        payload = {
            "name": "updated-template",
            "description": "Updated description",
            "cpu": 4,
            "ram": 8192,
        }
        resp = client.put(
            f"{API}/templates/{sample_template.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "updated-template"
        assert data["description"] == "Updated description"

    def test_update_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        payload = {"name": "ghost-template", "description": "Does not exist"}
        resp = client.put(
            f"{API}/templates/{fake_id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_update_unauthenticated_returns_401(self, client):
        """Use non-existent ID so ChangelogMiddleware exits early
        (it runs as a dependency before auth check)."""
        fake_id = uuid.uuid4()
        payload = {"name": "no-auth-template"}
        resp = client.put(f"{API}/templates/{fake_id}", json=payload)
        assert resp.status_code in (401, 403)


class TestDeleteTemplate:
    """DELETE /templates/{id} -- delete a template."""

    def test_delete_template_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        mock_redis_queues,
        sample_template,
    ):
        resp = client.delete(
            f"{API}/templates/{sample_template.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/templates/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/templates/{fake_id}")
        assert resp.status_code in (401, 403)


class TestGetTemplateApplications:
    """GET /templates/{id}/applications -- list apps for a template."""

    def test_returns_empty_apps_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_template,
    ):
        resp = client.get(
            f"{API}/templates/{sample_template.id}/applications",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert data["items"] == []

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/templates/{fake_id}/applications")
        assert resp.status_code in (401, 403)


class TestGetTemplateCourses:
    """GET /templates/{id}/courses -- list courses for a template."""

    def test_returns_empty_courses_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_template,
    ):
        resp = client.get(
            f"{API}/templates/{sample_template.id}/courses",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert data["items"] == []

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/templates/{fake_id}/courses")
        assert resp.status_code in (401, 403)


class TestGetTemplateVirtualMachines:
    """GET /templates/{id}/virtual-machines -- list VMs for a template."""

    def test_returns_empty_vm_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_template,
    ):
        resp = client.get(
            f"{API}/templates/{sample_template.id}/virtual-machines",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert data["items"] == []

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/templates/{fake_id}/virtual-machines")
        assert resp.status_code in (401, 403)
