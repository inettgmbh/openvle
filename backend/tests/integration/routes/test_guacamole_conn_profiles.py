"""Integration tests for /v{x}/guacamole-connection-profiles/ endpoints."""

import uuid

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_gcp(db_session, system_user):
    """Create a guacamole connection profile in the test DB."""
    from tests.factories.guacamole_factory import (
        GuacamoleConnectionProfileFactory,
    )

    return GuacamoleConnectionProfileFactory(
        port=3389,
        protocol="RDP",
        username="admin",
        password="password",
        objectId=uuid.uuid4(),
        objectType="VirtualMachine",
        createdById=system_user.id,
        updatedById=system_user.id,
    )


class TestCreateGuacamoleConnectionProfile:
    """POST /guacamole-connection-profiles/ -- create a new profile."""

    def test_create_returns_201(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_course,
    ):
        """The controller validates that objectId exists in DB,
        so we use a real Course object."""
        payload = {
            "port": 3389,
            "protocol": "RDP",
            "username": "admin",
            "password": "pass",
            "objectId": str(sample_course.id),
            "objectType": "Course",
        }
        resp = client.post(
            f"{API}/guacamole-connection-profiles/",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["port"] == 3389
        assert data["protocol"] == "RDP"
        assert data["username"] == "admin"
        assert data["objectType"] == "Course"

    def test_create_unauthenticated_returns_401(self, client):
        payload = {
            "port": 3389,
            "protocol": "RDP",
            "username": "admin",
            "password": "pass",
            "objectId": str(uuid.uuid4()),
            "objectType": "VirtualMachine",
        }
        resp = client.post(
            f"{API}/guacamole-connection-profiles/", json=payload
        )
        assert resp.status_code in (401, 403)

    def test_create_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, guacamole_connection_profiles_create is denied."""
        payload = {
            "port": 3389,
            "protocol": "RDP",
            "username": "admin",
            "password": "pass",
            "objectId": str(uuid.uuid4()),
            "objectType": "VirtualMachine",
        }
        resp = client.post(
            f"{API}/guacamole-connection-profiles/",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestGetGuacamoleConnectionProfiles:
    """GET /guacamole-connection-profiles/ -- list all profiles."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_gcp,
    ):
        resp = client.get(
            f"{API}/guacamole-connection-profiles/",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_pagination_params(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_gcp,
    ):
        resp = client.get(
            f"{API}/guacamole-connection-profiles/",
            params={"limit": 1, "page": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pageDetails"]["perPage"] == 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/guacamole-connection-profiles/")
        assert resp.status_code in (401, 403)

    def test_without_permission_falls_through_to_auth(
        self, client, auth_headers, sample_gcp
    ):
        """Without mock_permission_allow the list endpoint falls through
        to get_multi_auth which returns items filtered by object
        permissions (likely empty for the test user)."""
        resp = client.get(
            f"{API}/guacamole-connection-profiles/",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data


class TestGetGuacamoleConnectionProfileById:
    """GET /guacamole-connection-profiles/{id} -- get single profile."""

    def test_returns_profile(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_gcp,
    ):
        resp = client.get(
            f"{API}/guacamole-connection-profiles/{sample_gcp.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_gcp.id)
        assert data["port"] == sample_gcp.port
        assert data["protocol"] == sample_gcp.protocol

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.get(
            f"{API}/guacamole-connection-profiles/{fake_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/guacamole-connection-profiles/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(
        self, client, auth_headers, sample_gcp
    ):
        """Without mock_permission_allow, guacamole_connection_profiles_read is denied."""
        resp = client.get(
            f"{API}/guacamole-connection-profiles/{sample_gcp.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestDeleteGuacamoleConnectionProfile:
    """DELETE /guacamole-connection-profiles/{id} -- delete profile."""

    def test_delete_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_gcp,
    ):
        resp = client.delete(
            f"{API}/guacamole-connection-profiles/{sample_gcp.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(
            f"{API}/guacamole-connection-profiles/{fake_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/guacamole-connection-profiles/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_delete_permission_denied_returns_403(
        self, client, auth_headers, sample_gcp
    ):
        """Without mock_permission_allow, guacamole_connection_profiles_delete is denied."""
        resp = client.delete(
            f"{API}/guacamole-connection-profiles/{sample_gcp.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403
