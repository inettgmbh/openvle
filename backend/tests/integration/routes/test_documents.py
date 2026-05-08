"""Integration tests for /v{x}/documents/ endpoints."""

import uuid

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_document(db_session, system_user):
    """Create a document in the test DB."""
    from tests.factories.document_factory import DocumentFactory

    return DocumentFactory(
        name="Test Document",
        description="A test document",
        path="/docs/test_document.pdf",
        createdById=system_user.id,
        updatedById=system_user.id,
    )


class TestCreateDocument:
    """POST /documents/ -- create a new document."""

    def test_create_returns_201(
        self,
        client,
        auth_headers,
        mock_permission_allow,
    ):
        payload = {
            "name": "New Document",
            "description": "A brand new document",
        }
        resp = client.post(f"{API}/documents/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Document"
        assert data["description"] == "A brand new document"

    def test_create_unauthenticated_returns_401(self, client):
        payload = {
            "name": "Unauth Document",
            "description": "desc",
        }
        resp = client.post(f"{API}/documents/", json=payload)
        assert resp.status_code in (401, 403)

    def test_create_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, documents_create is denied."""
        payload = {
            "name": "Denied Document",
            "description": "desc",
        }
        resp = client.post(f"{API}/documents/", json=payload, headers=auth_headers)
        assert resp.status_code == 403


class TestGetDocuments:
    """GET /documents/ -- list all documents."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_document,
    ):
        resp = client.get(f"{API}/documents/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/documents/")
        assert resp.status_code in (401, 403)

    def test_without_permission_falls_through_to_auth(
        self, client, auth_headers, sample_document
    ):
        """Without mock_permission_allow the list endpoint falls through
        to get_multi_auth which returns items filtered by object
        permissions (likely empty for the test user)."""
        resp = client.get(f"{API}/documents/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data


class TestGetDocumentById:
    """GET /documents/{id} -- get single document."""

    def test_returns_document(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_document,
    ):
        resp = client.get(
            f"{API}/documents/{sample_document.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_document.id)
        assert data["name"] == "Test Document"
        assert data["description"] == "A test document"

    def test_not_found_returns_404(self, client, auth_headers, mock_permission_allow):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/documents/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/documents/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers, sample_document):
        """Without mock_permission_allow, documents_read is denied."""
        resp = client.get(
            f"{API}/documents/{sample_document.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestUpdateDocument:
    """PUT /documents/{id} -- update a document."""

    def test_update_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_document,
    ):
        payload = {"description": "Updated description"}
        resp = client.put(
            f"{API}/documents/{sample_document.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["description"] == "Updated description"

    def test_not_found_returns_404(self, client, auth_headers, mock_permission_allow):
        fake_id = uuid.uuid4()
        resp = client.put(
            f"{API}/documents/{fake_id}",
            json={"description": "Ghost"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        """Use non-existent ID so ChangelogMiddleware exits early
        (it runs before auth check and would 500 if it found the object)."""
        fake_id = uuid.uuid4()
        resp = client.put(
            f"{API}/documents/{fake_id}",
            json={"description": "No Auth"},
        )
        assert resp.status_code in (401, 403)


class TestDeleteDocument:
    """DELETE /documents/{id} -- delete a document."""

    def test_delete_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_document,
    ):
        resp = client.delete(
            f"{API}/documents/{sample_document.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/documents/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/documents/{fake_id}")
        assert resp.status_code in (401, 403)


class TestGetDocumentsForObject:
    """GET /documents/{object_type}/{object_id} -- documents for a specific object."""

    def test_returns_filtered_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        db_session,
        system_user,
    ):
        """Request documents for an OS object type.
        The controller only supports 'Application' and 'OS'."""
        from datetime import datetime, timezone

        from models import OS, Vendor

        now = datetime.now(timezone.utc)
        vendor = Vendor(
            id=uuid.uuid4(),
            name=f"DocVendor-{uuid.uuid4().hex[:6]}",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(vendor)
        db_session.flush()
        os_obj = OS(
            id=uuid.uuid4(),
            name=f"DocOS-{uuid.uuid4().hex[:6]}",
            key=f"docos-{uuid.uuid4().hex[:6]}",
            version="1.0",
            vendor=vendor.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(os_obj)
        db_session.flush()

        resp = client.get(
            f"{API}/documents/OS/{os_obj.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/documents/Application/{fake_id}")
        assert resp.status_code in (401, 403)
