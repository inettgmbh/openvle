"""Integration tests for /v{x}/os/ endpoints."""

import uuid
from datetime import datetime, timezone

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_vendor(db_session, system_user):
    """Create a vendor required as FK for OS records."""
    from models import Vendor

    now = datetime.now(timezone.utc)
    vendor = Vendor(
        id=uuid.uuid4(),
        name=f"OS Test Vendor {uuid.uuid4().hex[:6]}",
        description="Vendor for OS tests",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


@pytest.fixture()
def sample_os(db_session, system_user, sample_vendor):
    """Create an OS in the test DB."""
    from models import OS

    now = datetime.now(timezone.utc)
    os_entry = OS(
        id=uuid.uuid4(),
        name="Test OS",
        key=f"test-os-{uuid.uuid4().hex[:8]}",
        version="10.0",
        description="A test operating system",
        vendor=sample_vendor.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(os_entry)
    db_session.flush()
    return os_entry


class TestCreateOS:
    """POST /os/ -- create a new operating system."""

    def test_create_os_returns_201(
        self, client, auth_headers, mock_permission_allow, sample_vendor
    ):
        payload = {
            "name": "New OS",
            "key": f"new-os-{uuid.uuid4().hex[:8]}",
            "version": "2.0",
            "vendor": str(sample_vendor.id),
            "description": "A brand new OS",
        }
        resp = client.post(f"{API}/os/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New OS"
        assert data["version"] == "2.0"
        assert data["vendor"] == str(sample_vendor.id)
        assert "id" in data

    def test_create_os_unauthenticated_returns_401(self, client):
        payload = {
            "name": "No Auth OS",
            "key": "no-auth-os",
            "version": "1.0",
            "vendor": str(uuid.uuid4()),
        }
        resp = client.post(f"{API}/os/", json=payload)
        assert resp.status_code in (401, 403)

    def test_create_os_permission_denied_returns_403(
        self, client, auth_headers, sample_vendor
    ):
        """Without mock_permission_allow, os_create is denied."""
        payload = {
            "name": "Denied OS",
            "key": "denied-os",
            "version": "1.0",
            "vendor": str(sample_vendor.id),
        }
        resp = client.post(f"{API}/os/", json=payload, headers=auth_headers)
        assert resp.status_code == 403


class TestGetOperatingSystems:
    """GET /os/ -- list all operating systems."""

    def test_returns_paginated_list(
        self, client, auth_headers, mock_permission_allow, sample_os
    ):
        resp = client.get(f"{API}/os/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_pagination_params(
        self, client, auth_headers, mock_permission_allow, sample_os
    ):
        resp = client.get(
            f"{API}/os/",
            params={"limit": 1, "page": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pageDetails"]["perPage"] == 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/os/")
        assert resp.status_code in (401, 403)


class TestGetOSById:
    """GET /os/{id} -- get single operating system."""

    def test_returns_os(
        self, client, auth_headers, mock_permission_allow, sample_os
    ):
        resp = client.get(f"{API}/os/{sample_os.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_os.id)
        assert data["name"] == sample_os.name
        assert data["key"] == sample_os.key

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/os/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/os/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(
        self, client, auth_headers, sample_os
    ):
        """Without mock_permission_allow, os_read is denied."""
        resp = client.get(f"{API}/os/{sample_os.id}", headers=auth_headers)
        assert resp.status_code == 403


class TestUpdateOS:
    """PUT /os/{id} -- update an operating system."""

    def test_update_os_returns_200(
        self, client, auth_headers, mock_permission_allow, sample_os
    ):
        payload = {
            "name": "Updated OS",
            "description": "Updated description",
            "version": "11.0",
        }
        resp = client.put(
            f"{API}/os/{sample_os.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated OS"
        assert data["description"] == "Updated description"

    def test_update_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        payload = {"name": "Ghost OS", "version": "99.0"}
        resp = client.put(
            f"{API}/os/{fake_id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_update_unauthenticated_returns_401(self, client):
        """Use non-existent ID so ChangelogMiddleware exits early
        (it runs as a dependency before auth check)."""
        fake_id = uuid.uuid4()
        payload = {"name": "No Auth OS"}
        resp = client.put(f"{API}/os/{fake_id}", json=payload)
        assert resp.status_code in (401, 403)


class TestDeleteOS:
    """DELETE /os/{id} -- delete an operating system."""

    def test_delete_os_returns_200(
        self, client, auth_headers, mock_permission_allow, sample_os
    ):
        resp = client.delete(f"{API}/os/{sample_os.id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/os/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/os/{fake_id}")
        assert resp.status_code in (401, 403)
