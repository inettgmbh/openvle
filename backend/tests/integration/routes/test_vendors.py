"""Integration tests for /v{x}/vendors/ endpoints."""

import uuid
from datetime import datetime, timezone

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_vendor(db_session, system_user):
    """Create a vendor in the test DB."""
    from models import Vendor

    now = datetime.now(timezone.utc)
    vendor = Vendor(
        id=uuid.uuid4(),
        name="Test Vendor",
        description="A test vendor",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


@pytest.fixture()
def sample_vendor_with_os(db_session, system_user, sample_vendor):
    """Create a vendor that has an associated OS record."""
    from models import OS

    now = datetime.now(timezone.utc)
    os_entry = OS(
        id=uuid.uuid4(),
        name="Test OS",
        key=f"test-os-{uuid.uuid4().hex[:8]}",
        version="1.0",
        vendor=sample_vendor.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(os_entry)
    db_session.flush()
    return sample_vendor


@pytest.fixture()
def sample_vendor_with_app(db_session, system_user, sample_vendor):
    """Create a vendor that has an associated Application record."""
    from models import Application

    now = datetime.now(timezone.utc)
    app = Application(
        id=uuid.uuid4(),
        name="Test App",
        key=f"test-app-{uuid.uuid4().hex[:8]}",
        vendor=sample_vendor.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(app)
    db_session.flush()
    return sample_vendor


class TestCreateVendor:
    """POST /vendors/ -- create a new vendor."""

    def test_create_vendor_returns_201(
        self, client, auth_headers, mock_permission_allow
    ):
        payload = {"name": "New Vendor", "description": "Brand new vendor"}
        resp = client.post(f"{API}/vendors/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Vendor"
        assert data["description"] == "Brand new vendor"
        assert "id" in data

    def test_create_vendor_unauthenticated_returns_401(self, client):
        payload = {"name": "No Auth Vendor", "description": "desc"}
        resp = client.post(f"{API}/vendors/", json=payload)
        assert resp.status_code in (401, 403)

    def test_create_vendor_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, vendors_create is denied."""
        payload = {"name": "Denied Vendor", "description": "desc"}
        resp = client.post(f"{API}/vendors/", json=payload, headers=auth_headers)
        assert resp.status_code == 403


class TestGetVendors:
    """GET /vendors/ -- list all vendors."""

    def test_returns_paginated_list(
        self, client, auth_headers, mock_permission_allow, sample_vendor
    ):
        resp = client.get(f"{API}/vendors/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_pagination_params(
        self, client, auth_headers, mock_permission_allow, sample_vendor
    ):
        resp = client.get(
            f"{API}/vendors/",
            params={"limit": 1, "page": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pageDetails"]["perPage"] == 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/vendors/")
        assert resp.status_code in (401, 403)


class TestGetVendorById:
    """GET /vendors/{id} -- get single vendor."""

    def test_returns_vendor(
        self, client, auth_headers, mock_permission_allow, sample_vendor
    ):
        resp = client.get(f"{API}/vendors/{sample_vendor.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_vendor.id)
        assert data["name"] == sample_vendor.name

    def test_not_found_returns_404(self, client, auth_headers, mock_permission_allow):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/vendors/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/vendors/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers, sample_vendor):
        """Without mock_permission_allow, vendors_read is denied."""
        resp = client.get(f"{API}/vendors/{sample_vendor.id}", headers=auth_headers)
        assert resp.status_code == 403


class TestUpdateVendor:
    """PUT /vendors/{id} -- update a vendor."""

    def test_update_vendor_returns_200(
        self, client, auth_headers, mock_permission_allow, sample_vendor
    ):
        payload = {
            "name": "Updated Vendor",
            "description": "Updated description",
        }
        resp = client.put(
            f"{API}/vendors/{sample_vendor.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Vendor"
        assert data["description"] == "Updated description"

    def test_update_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        payload = {"name": "Ghost", "description": "Does not exist"}
        resp = client.put(
            f"{API}/vendors/{fake_id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_update_unauthenticated_returns_401(self, client):
        """Use non-existent ID so ChangelogMiddleware exits early
        (it runs as a dependency before auth check)."""
        fake_id = uuid.uuid4()
        payload = {"name": "No Auth"}
        resp = client.put(f"{API}/vendors/{fake_id}", json=payload)
        assert resp.status_code in (401, 403)


class TestDeleteVendor:
    """DELETE /vendors/{id} -- delete a vendor."""

    def test_delete_vendor_returns_200(
        self, client, auth_headers, mock_permission_allow, sample_vendor
    ):
        resp = client.delete(f"{API}/vendors/{sample_vendor.id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/vendors/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/vendors/{fake_id}")
        assert resp.status_code in (401, 403)


class TestGetVendorOperatingSystems:
    """GET /vendors/{id}/operating-systems -- list OS for vendor."""

    def test_returns_os_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_vendor_with_os,
    ):
        resp = client.get(
            f"{API}/vendors/{sample_vendor_with_os.id}/operating-systems",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_empty_os_list(
        self, client, auth_headers, mock_permission_allow, sample_vendor
    ):
        resp = client.get(
            f"{API}/vendors/{sample_vendor.id}/operating-systems",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/vendors/{fake_id}/operating-systems")
        assert resp.status_code in (401, 403)


class TestGetVendorApplications:
    """GET /vendors/{id}/applications -- list apps for vendor."""

    def test_returns_apps_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_vendor_with_app,
    ):
        resp = client.get(
            f"{API}/vendors/{sample_vendor_with_app.id}/applications",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_empty_apps_list(
        self, client, auth_headers, mock_permission_allow, sample_vendor
    ):
        resp = client.get(
            f"{API}/vendors/{sample_vendor.id}/applications",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/vendors/{fake_id}/applications")
        assert resp.status_code in (401, 403)
