"""Integration tests for /v{x}/guacamole/ endpoints."""

import uuid

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_vm_for_guac(db_session, system_user):
    """Create a minimal VirtualMachine for GCP references."""
    from datetime import datetime, timezone

    from models import VirtualMachine

    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name="guac-test-vm",
        cpu=2,
        ram=4096,
        disk=20,
        status="running",
        ipv4="10.0.1.99",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vm)
    db_session.flush()
    return vm


@pytest.fixture()
def sample_gcp(db_session, system_user, sample_vm_for_guac):
    """Create a guacamole connection profile in the test DB."""
    from tests.factories.guacamole_factory import (
        GuacamoleConnectionProfileFactory,
    )

    return GuacamoleConnectionProfileFactory(
        objectId=sample_vm_for_guac.id,
        objectType="VirtualMachine",
        createdById=system_user.id,
        updatedById=system_user.id,
    )


@pytest.fixture()
def sample_guacamole(db_session, system_user, sample_gcp):
    """Create a guacamole entry in the test DB."""
    from tests.factories.guacamole_factory import GuacamoleFactory

    return GuacamoleFactory(
        connection_profile=sample_gcp.id,
        userId=system_user.id,
        createdById=system_user.id,
        updatedById=system_user.id,
    )


class TestCreateGuacamole:
    """POST /guacamole/ -- create a new guacamole connection."""

    def test_create_returns_201(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        active_user,
        sample_gcp,
    ):
        payload = {
            "name": "New Guacamole",
            "guacd_hostname": "guacd.local",
            "guacd_port": 4822,
            "guacd_encryption": True,
            "connection_profile": str(sample_gcp.id),
            "userId": str(active_user.id),
            "eventId": None,
        }
        resp = client.post(f"{API}/guacamole/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Guacamole"
        assert data["guacd_port"] == 4822
        assert data["guacd_encryption"] is True
        assert data["connection_profile"] == str(sample_gcp.id)
        assert data["userId"] == str(active_user.id)

    def test_create_unauthenticated_returns_401(self, client):
        payload = {
            "name": "Unauth Guacamole",
            "guacd_hostname": "guacd.local",
            "guacd_port": 4822,
            "guacd_encryption": True,
            "connection_profile": str(uuid.uuid4()),
            "userId": str(uuid.uuid4()),
            "eventId": None,
        }
        resp = client.post(f"{API}/guacamole/", json=payload)
        assert resp.status_code in (401, 403)

    def test_create_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, guacamoles_create is denied."""
        payload = {
            "name": "Denied Guacamole",
            "guacd_hostname": "guacd.local",
            "guacd_port": 4822,
            "guacd_encryption": True,
            "connection_profile": str(uuid.uuid4()),
            "userId": str(uuid.uuid4()),
            "eventId": None,
        }
        resp = client.post(f"{API}/guacamole/", json=payload, headers=auth_headers)
        assert resp.status_code == 403


class TestGetGuacamoles:
    """GET /guacamole/ -- list all guacamole connections."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_guacamole,
    ):
        resp = client.get(f"{API}/guacamole/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/guacamole/")
        assert resp.status_code in (401, 403)

    def test_without_permission_falls_through_to_auth(
        self, client, auth_headers, sample_guacamole
    ):
        """Without mock_permission_allow the list endpoint falls through
        to get_multi_auth which returns items filtered by object
        permissions (likely empty for the test user)."""
        resp = client.get(f"{API}/guacamole/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data


class TestGetGuacamoleById:
    """GET /guacamole/{id} -- get single guacamole connection."""

    def test_returns_guacamole(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_guacamole,
    ):
        resp = client.get(
            f"{API}/guacamole/{sample_guacamole.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_guacamole.id)
        assert data["name"] == sample_guacamole.name

    def test_not_found_returns_404(self, client, auth_headers, mock_permission_allow):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/guacamole/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/guacamole/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(
        self, client, auth_headers, sample_guacamole
    ):
        """Without mock_permission_allow, guacamoles_read is denied."""
        resp = client.get(
            f"{API}/guacamole/{sample_guacamole.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestDeleteGuacamole:
    """DELETE /guacamole/{id} -- delete guacamole connection."""

    def test_delete_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_guacamole,
    ):
        resp = client.delete(
            f"{API}/guacamole/{sample_guacamole.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/guacamole/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/guacamole/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_delete_permission_denied_returns_403(
        self, client, auth_headers, sample_guacamole
    ):
        """Without mock_permission_allow, guacamoles_delete is denied."""
        resp = client.delete(
            f"{API}/guacamole/{sample_guacamole.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403
