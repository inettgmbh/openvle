"""Integration tests for /v{x}/mailactions/ endpoints."""

import uuid

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_mail_action(db_session, system_user):
    """Create a mail action in the test DB."""
    from tests.factories.mail_factory import MailActionFactory

    return MailActionFactory(
        createdById=system_user.id, updatedById=system_user.id
    )


class TestGetMailActions:
    """GET /mailactions/ — list all mail actions."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_mail_action,
    ):
        resp = client.get(f"{API}/mailactions/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/mailactions/")
        assert resp.status_code in (401, 403)

    def test_permission_denied(self, client, auth_headers):
        """Without mock_permission_allow, mail_templates_read is denied."""
        resp = client.get(f"{API}/mailactions/", headers=auth_headers)
        assert resp.status_code == 403


class TestGetMailActionById:
    """GET /mailactions/{id} — get single mail action."""

    def test_returns_mail_action(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_mail_action,
    ):
        resp = client.get(
            f"{API}/mailactions/{sample_mail_action.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_mail_action.id)

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/mailactions/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404


class TestGetMailActionTemplates:
    """GET /mailactions/{id}/mail-templates — templates for a mail action."""

    def test_returns_templates_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_mail_action,
    ):
        resp = client.get(
            f"{API}/mailactions/{sample_mail_action.id}/mail-templates",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
