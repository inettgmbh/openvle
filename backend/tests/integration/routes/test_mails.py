"""Integration tests for /v{x}/mails/ endpoints."""

import uuid
from datetime import datetime, timezone

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_language(db_session, system_user):
    """Create a language in the test DB."""
    from tests.factories.language_factory import LanguageFactory

    return LanguageFactory(
        createdById=system_user.id, updatedById=system_user.id
    )


@pytest.fixture()
def sample_mail_template(db_session, system_user, sample_language):
    """Create a mail template for use in mail tests."""
    from tests.factories.mail_factory import MailTemplateFactory

    return MailTemplateFactory(
        language=sample_language.id,
        protected=False,
        createdById=system_user.id,
        updatedById=system_user.id,
    )


@pytest.fixture()
def sample_mail(db_session, system_user, active_user, sample_mail_template):
    """Create a mail entry in the test DB."""
    from models.mails import Mail

    now = datetime.now(timezone.utc)
    mail = Mail(
        id=uuid.uuid4(),
        subject="Test Mail Subject",
        fromName="Test KVS",
        fromMail="test@example.com",
        toMail="recipient@example.com",
        sendStatus="queued",
        templateId=sample_mail_template.id,
        replyTo="noreply@example.com",
        content_rendered="<p>Hello</p>",
        event=None,
        user_id=active_user.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(mail)
    db_session.flush()
    return mail


class TestCreateMail:
    """POST /mails/ -- create (send) a new mail."""

    def test_create_mail(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        mock_redis_queues,
        sample_mail_template,
        active_user,
    ):
        payload = {
            "subject": "New Mail",
            "fromName": "KVS Test",
            "fromMail": "kvs@example.com",
            "toMail": "user@example.com",
            "templateId": str(sample_mail_template.id),
            "replyTo": "noreply@example.com",
            "user_id": str(active_user.id),
        }
        resp = client.post(
            f"{API}/mails/",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["subject"] == "New Mail"
        assert data["sendStatus"] == "queued"
        assert data["templateId"] == str(sample_mail_template.id)

    def test_unauthenticated_returns_401(self, client):
        payload = {
            "subject": "No Auth",
            "fromName": "Test",
            "fromMail": "test@example.com",
            "toMail": "user@example.com",
            "templateId": str(uuid.uuid4()),
            "replyTo": "noreply@example.com",
            "user_id": str(uuid.uuid4()),
        }
        resp = client.post(f"{API}/mails/", json=payload)
        assert resp.status_code in (401, 403)

    def test_permission_denied(
        self,
        client,
        auth_headers,
        sample_mail_template,
        active_user,
    ):
        """Without mock_permission_allow, mails_send is denied."""
        payload = {
            "subject": "Denied",
            "fromName": "Test",
            "fromMail": "test@example.com",
            "toMail": "user@example.com",
            "templateId": str(sample_mail_template.id),
            "replyTo": "noreply@example.com",
            "user_id": str(active_user.id),
        }
        resp = client.post(
            f"{API}/mails/",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestGetMails:
    """GET /mails/ -- list all mails."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_mail,
    ):
        resp = client.get(f"{API}/mails/", headers=auth_headers)
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
        sample_mail,
    ):
        resp = client.get(
            f"{API}/mails/",
            params={"limit": 1, "page": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pageDetails"]["perPage"] == 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/mails/")
        assert resp.status_code in (401, 403)


class TestGetMailById:
    """GET /mails/{id} -- get single mail."""

    def test_returns_mail(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_mail,
    ):
        resp = client.get(
            f"{API}/mails/{sample_mail.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_mail.id)
        assert data["subject"] == sample_mail.subject
        assert data["toMail"] == sample_mail.toMail

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/mails/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/mails/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied(self, client, auth_headers, sample_mail):
        """Without mock_permission_allow, mails_read is denied."""
        resp = client.get(
            f"{API}/mails/{sample_mail.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403
