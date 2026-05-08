"""Integration tests for /v{x}/applications/ endpoints."""

import uuid
from datetime import datetime, timezone

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_vendor(db_session, system_user):
    """Create a vendor required as FK for Application records."""
    from models import Vendor

    now = datetime.now(timezone.utc)
    vendor = Vendor(
        id=uuid.uuid4(),
        name=f"App Test Vendor {uuid.uuid4().hex[:6]}",
        description="Vendor for application tests",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


@pytest.fixture()
def sample_app(db_session, system_user, sample_vendor):
    """Create an application in the test DB."""
    from models import Application

    now = datetime.now(timezone.utc)
    app = Application(
        id=uuid.uuid4(),
        name="Test Application",
        key=f"test-app-{uuid.uuid4().hex[:8]}",
        description="A test application",
        vendor=sample_vendor.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(app)
    db_session.flush()
    return app


class TestCreateApplication:
    """POST /applications/ -- create a new application."""

    def test_create_app_returns_201(
        self, client, auth_headers, mock_permission_allow, sample_vendor
    ):
        payload = {
            "name": "New App",
            "key": f"new-app-{uuid.uuid4().hex[:8]}",
            "vendor": str(sample_vendor.id),
            "description": "A brand new application",
        }
        resp = client.post(f"{API}/applications/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New App"
        assert data["vendor"] == str(sample_vendor.id)
        assert "id" in data

    def test_create_app_unauthenticated_returns_401(self, client):
        payload = {
            "name": "No Auth App",
            "key": "no-auth-app",
            "vendor": str(uuid.uuid4()),
        }
        resp = client.post(f"{API}/applications/", json=payload)
        assert resp.status_code in (401, 403)

    def test_create_app_permission_denied_returns_403(
        self, client, auth_headers, sample_vendor
    ):
        """Without mock_permission_allow, applications_create is denied."""
        payload = {
            "name": "Denied App",
            "key": "denied-app",
            "vendor": str(sample_vendor.id),
        }
        resp = client.post(f"{API}/applications/", json=payload, headers=auth_headers)
        assert resp.status_code == 403


class TestGetApplications:
    """GET /applications/ -- list all applications."""

    def test_returns_paginated_list(
        self, client, auth_headers, mock_permission_allow, sample_app
    ):
        resp = client.get(f"{API}/applications/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_pagination_params(
        self, client, auth_headers, mock_permission_allow, sample_app
    ):
        resp = client.get(
            f"{API}/applications/",
            params={"limit": 1, "page": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pageDetails"]["perPage"] == 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/applications/")
        assert resp.status_code in (401, 403)


class TestGetApplicationById:
    """GET /applications/{id} -- get single application."""

    def test_returns_application(
        self, client, auth_headers, mock_permission_allow, sample_app
    ):
        resp = client.get(f"{API}/applications/{sample_app.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_app.id)
        assert data["name"] == sample_app.name
        assert data["key"] == sample_app.key

    def test_not_found_returns_404(self, client, auth_headers, mock_permission_allow):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/applications/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/applications/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers, sample_app):
        """Without mock_permission_allow, applications_read is denied."""
        resp = client.get(f"{API}/applications/{sample_app.id}", headers=auth_headers)
        assert resp.status_code == 403


class TestUpdateApplication:
    """PUT /applications/{id} -- update an application."""

    def test_update_app_returns_200(
        self, client, auth_headers, mock_permission_allow, sample_app
    ):
        payload = {
            "name": "Updated App",
            "description": "Updated description",
        }
        resp = client.put(
            f"{API}/applications/{sample_app.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated App"
        assert data["description"] == "Updated description"

    def test_update_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        payload = {"name": "Ghost App", "description": "Does not exist"}
        resp = client.put(
            f"{API}/applications/{fake_id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_update_unauthenticated_returns_401(self, client):
        """Use non-existent ID so ChangelogMiddleware exits early
        (it runs as a dependency before auth check)."""
        fake_id = uuid.uuid4()
        payload = {"name": "No Auth App"}
        resp = client.put(f"{API}/applications/{fake_id}", json=payload)
        assert resp.status_code in (401, 403)


class TestDeleteApplication:
    """DELETE /applications/{id} -- delete an application."""

    def test_delete_app_returns_200(
        self, client, auth_headers, mock_permission_allow, sample_app
    ):
        resp = client.delete(
            f"{API}/applications/{sample_app.id}", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/applications/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/applications/{fake_id}")
        assert resp.status_code in (401, 403)
