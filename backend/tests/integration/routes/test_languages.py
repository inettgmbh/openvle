"""Integration tests for /v{x}/languages/ endpoints."""

import uuid

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_language(db_session, system_user):
    """Create a language in the test DB."""
    from tests.factories.language_factory import LanguageFactory

    return LanguageFactory(createdById=system_user.id, updatedById=system_user.id)


class TestGetLanguages:
    """GET /languages/ — list all languages."""

    def test_returns_paginated_list(
        self, client, auth_headers, mock_permission_allow, sample_language
    ):
        resp = client.get(f"{API}/languages/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_pagination_params(
        self, client, auth_headers, mock_permission_allow, sample_language
    ):
        resp = client.get(
            f"{API}/languages/",
            params={"limit": 1, "page": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pageDetails"]["perPage"] == 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/languages/")
        assert resp.status_code in (401, 403)

    def test_expired_token_returns_401(self, client, expired_auth_headers):
        resp = client.get(f"{API}/languages/", headers=expired_auth_headers)
        assert resp.status_code in (401, 403)


class TestGetLanguageById:
    """GET /languages/{id} — get single language."""

    def test_returns_language(
        self, client, auth_headers, mock_permission_allow, sample_language
    ):
        resp = client.get(
            f"{API}/languages/{sample_language.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_language.id)
        assert data["nameEnglish"] == sample_language.nameEnglish

    def test_not_found_returns_404(self, client, auth_headers, mock_permission_allow):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/languages/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/languages/{fake_id}")
        assert resp.status_code in (401, 403)
