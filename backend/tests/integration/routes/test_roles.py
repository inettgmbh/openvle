"""Integration tests for /v{x}/roles/ endpoints."""

import uuid
from datetime import datetime, timezone

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_role(db_session, system_user):
    """Create a non-protected role in the test DB."""
    from models import Role

    now = datetime.now(timezone.utc)
    role = Role(
        id=uuid.uuid4(),
        name="Test Role",
        description="A test role",
        key=f"test_role_{uuid.uuid4().hex[:8]}",
        protected=False,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(role)
    db_session.flush()
    return role


@pytest.fixture()
def protected_role(db_session, system_user):
    """Create a protected (system) role in the test DB."""
    from models import Role

    now = datetime.now(timezone.utc)
    role = Role(
        id=uuid.uuid4(),
        name="Protected Role",
        description="A protected system role",
        key=f"protected_role_{uuid.uuid4().hex[:8]}",
        protected=True,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(role)
    db_session.flush()
    return role


class TestCreateRole:
    """POST /roles/ -- create a new role."""

    def test_create_role_returns_201(
        self, client, auth_headers, mock_permission_allow
    ):
        payload = {
            "name": "New Role",
            "description": "A brand new role",
            "key": f"new_role_{uuid.uuid4().hex[:8]}",
            "protected": False,
        }
        resp = client.post(f"{API}/roles/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Role"
        assert data["description"] == "A brand new role"
        assert data["protected"] is False
        assert "id" in data

    def test_create_unauthenticated_returns_401(self, client):
        payload = {
            "name": "No Auth Role",
            "description": "desc",
            "key": "no_auth_role",
        }
        resp = client.post(f"{API}/roles/", json=payload)
        assert resp.status_code in (401, 403)

    def test_create_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, roles_create is denied."""
        payload = {
            "name": "Denied Role",
            "description": "desc",
            "key": "denied_role",
        }
        resp = client.post(f"{API}/roles/", json=payload, headers=auth_headers)
        assert resp.status_code == 403


class TestGetRoles:
    """GET /roles/ -- list all roles."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_role,
    ):
        resp = client.get(f"{API}/roles/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/roles/")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, roles_read is denied."""
        resp = client.get(f"{API}/roles/", headers=auth_headers)
        assert resp.status_code == 403


class TestGetRoleById:
    """GET /roles/{id} -- get single role."""

    def test_returns_role(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_role,
    ):
        resp = client.get(f"{API}/roles/{sample_role.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_role.id)
        assert data["name"] == sample_role.name
        assert data["key"] == sample_role.key
        assert data["protected"] is False

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/roles/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/roles/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(
        self, client, auth_headers, sample_role
    ):
        """Without mock_permission_allow, roles_read is denied."""
        resp = client.get(f"{API}/roles/{sample_role.id}", headers=auth_headers)
        assert resp.status_code == 403


class TestUpdateRole:
    """PUT /roles/{id} -- update a role."""

    def test_update_role_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_role,
    ):
        payload = {
            "name": "Updated Role",
            "description": "Updated description",
        }
        resp = client.put(
            f"{API}/roles/{sample_role.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Role"
        assert data["description"] == "Updated description"

    def test_update_protected_returns_403(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        protected_role,
    ):
        payload = {"name": "Should Fail"}
        resp = client.put(
            f"{API}/roles/{protected_role.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_update_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        payload = {"name": "Ghost Role", "description": "Does not exist"}
        resp = client.put(
            f"{API}/roles/{fake_id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_update_unauthenticated_returns_401(self, client):
        """Use non-existent ID so ChangelogMiddleware exits early
        (it runs as a dependency before auth check)."""
        fake_id = uuid.uuid4()
        payload = {"name": "No Auth Role"}
        resp = client.put(f"{API}/roles/{fake_id}", json=payload)
        assert resp.status_code in (401, 403)


class TestDeleteRole:
    """DELETE /roles/{id} -- delete a role."""

    def test_delete_role_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_role,
    ):
        resp = client.delete(
            f"{API}/roles/{sample_role.id}", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_delete_protected_returns_403(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        protected_role,
    ):
        resp = client.delete(
            f"{API}/roles/{protected_role.id}", headers=auth_headers
        )
        assert resp.status_code == 403

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/roles/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/roles/{fake_id}")
        assert resp.status_code in (401, 403)


class TestGetRoleMembers:
    """GET /roles/{id}/members -- list users for a role."""

    def test_returns_members_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_role,
    ):
        resp = client.get(
            f"{API}/roles/{sample_role.id}/members",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/roles/{fake_id}/members")
        assert resp.status_code in (401, 403)
