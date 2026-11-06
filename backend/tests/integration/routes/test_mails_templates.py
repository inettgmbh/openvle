"""Integration tests for /v{x}/mailtemplates/ endpoints."""

import uuid

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
    """Create a non-protected mail template in the test DB."""
    from tests.factories.mail_factory import MailTemplateFactory

    return MailTemplateFactory(
        language=sample_language.id,
        protected=False,
        createdById=system_user.id,
        updatedById=system_user.id,
    )


@pytest.fixture()
def protected_mail_template(db_session, system_user, sample_language):
    """Create a protected mail template in the test DB."""
    from tests.factories.mail_factory import MailTemplateFactory

    return MailTemplateFactory(
        name="Protected Template",
        language=sample_language.id,
        protected=True,
        createdById=system_user.id,
        updatedById=system_user.id,
    )


class TestCreateMailTemplate:
    """POST /mailtemplates/ -- create a new mail template."""

    def test_create_mail_template(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_language,
    ):
        payload = {
            "name": "New Template",
            "subject": "Welcome",
            "description": "Welcome email template",
            "fromName": "KVS Test",
            "fromMail": "kvs@example.com",
            "contentHTML": "<p>Hello</p>",
            "contentPlain": "Hello",
            "language": str(sample_language.id),
            "protected": False,
            "replyTo": None,
            "mail_action": None,
        }
        resp = client.post(
            f"{API}/mailtemplates/",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Template"
        assert data["subject"] == "Welcome"
        assert data["language"] == str(sample_language.id)

    def test_unauthenticated_returns_401(self, client):
        payload = {
            "name": "No Auth",
            "subject": "Subject",
            "contentHTML": "<p>x</p>",
            "contentPlain": "x",
            "language": str(uuid.uuid4()),
            "protected": False,
        }
        resp = client.post(f"{API}/mailtemplates/", json=payload)
        assert resp.status_code in (401, 403)

    def test_permission_denied(self, client, auth_headers, sample_language):
        """Without mock_permission_allow, mail_templates_create is denied."""
        payload = {
            "name": "Denied Template",
            "subject": "Denied",
            "contentHTML": "<p>x</p>",
            "contentPlain": "x",
            "language": str(sample_language.id),
            "protected": False,
        }
        resp = client.post(
            f"{API}/mailtemplates/",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestCreateMailTemplateSubjectValidation:
    """POST /mailtemplates/ -- subject RFC length validation."""

    def _payload(self, subject: str, language_id: str) -> dict:
        return {
            "name": f"Template {subject[:10]}",
            "subject": subject,
            "contentHTML": "<p>x</p>",
            "contentPlain": "x",
            "language": language_id,
            "protected": False,
        }

    def test_subject_at_max_length_accepted(
        self, client, auth_headers, mock_permission_allow, sample_language
    ):
        """75-char subject without placeholder → 201."""
        payload = self._payload("A" * 75, str(sample_language.id))
        resp = client.post(
            f"{API}/mailtemplates/", json=payload, headers=auth_headers
        )
        assert resp.status_code == 201

    def test_subject_over_max_length_rejected(
        self, client, auth_headers, mock_permission_allow, sample_language
    ):
        """76-char subject without placeholder → 422."""
        payload = self._payload("A" * 76, str(sample_language.id))
        resp = client.post(
            f"{API}/mailtemplates/", json=payload, headers=auth_headers
        )
        assert resp.status_code == 422

    def test_subject_with_slug_at_budget_accepted(
        self, client, auth_headers, mock_permission_allow, sample_language
    ):
        """67 remaining chars + {{event.slug}} → 201."""
        payload = self._payload(
            "A" * 67 + "{{event.slug}}", str(sample_language.id)
        )
        resp = client.post(
            f"{API}/mailtemplates/", json=payload, headers=auth_headers
        )
        assert resp.status_code == 201

    def test_subject_with_slug_over_budget_rejected(
        self, client, auth_headers, mock_permission_allow, sample_language
    ):
        """68 remaining chars + {{event.slug}} → 422."""
        payload = self._payload(
            "A" * 68 + "{{event.slug}}", str(sample_language.id)
        )
        resp = client.post(
            f"{API}/mailtemplates/", json=payload, headers=auth_headers
        )
        assert resp.status_code == 422

    def test_subject_with_whitespace_slug_at_budget_accepted(
        self, client, auth_headers, mock_permission_allow, sample_language
    ):
        """67 remaining chars + {{ event.slug }} → 201."""
        payload = self._payload(
            "A" * 67 + "{{ event.slug }}", str(sample_language.id)
        )
        resp = client.post(
            f"{API}/mailtemplates/", json=payload, headers=auth_headers
        )
        assert resp.status_code == 201

    def test_subject_with_whitespace_slug_over_budget_rejected(
        self, client, auth_headers, mock_permission_allow, sample_language
    ):
        """68 remaining chars + {{ event.slug }} → 422."""
        payload = self._payload(
            "A" * 68 + "{{ event.slug }}", str(sample_language.id)
        )
        resp = client.post(
            f"{API}/mailtemplates/", json=payload, headers=auth_headers
        )
        assert resp.status_code == 422

    def test_update_subject_over_max_rejected(
        self, client, auth_headers, mock_permission_allow, sample_mail_template
    ):
        """PUT with 76-char subject → 422."""
        resp = client.put(
            f"{API}/mailtemplates/{sample_mail_template.id}",
            json={"subject": "B" * 76},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestGetMailTemplates:
    """GET /mailtemplates/ -- list all mail templates."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_mail_template,
    ):
        resp = client.get(f"{API}/mailtemplates/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/mailtemplates/")
        assert resp.status_code in (401, 403)


class TestGetMailTemplateById:
    """GET /mailtemplates/{id} -- get single mail template."""

    def test_returns_mail_template(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_mail_template,
    ):
        resp = client.get(
            f"{API}/mailtemplates/{sample_mail_template.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_mail_template.id)
        assert data["name"] == sample_mail_template.name

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.get(
            f"{API}/mailtemplates/{fake_id}", headers=auth_headers
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/mailtemplates/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied(
        self, client, auth_headers, sample_mail_template
    ):
        """Without mock_permission_allow, mail_templates_read is denied."""
        resp = client.get(
            f"{API}/mailtemplates/{sample_mail_template.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestUpdateMailTemplate:
    """PUT /mailtemplates/{id} -- update a mail template."""

    def test_update_mail_template(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_mail_template,
    ):
        payload = {
            "name": "Updated Template",
            "subject": "Updated Subject",
        }
        resp = client.put(
            f"{API}/mailtemplates/{sample_mail_template.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Template"
        assert data["subject"] == "Updated Subject"

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.put(
            f"{API}/mailtemplates/{fake_id}",
            json={"name": "Ghost"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        """Use non-existent ID so ChangelogMiddleware exits early
        (it runs as a dependency before auth check)."""
        fake_id = uuid.uuid4()
        resp = client.put(
            f"{API}/mailtemplates/{fake_id}",
            json={"name": "No Auth"},
        )
        assert resp.status_code in (401, 403)


class TestDeleteMailTemplate:
    """DELETE /mailtemplates/{id} -- delete a mail template."""

    def test_delete_mail_template(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_mail_template,
    ):
        resp = client.delete(
            f"{API}/mailtemplates/{sample_mail_template.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_delete_protected_returns_403(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        protected_mail_template,
    ):
        resp = client.delete(
            f"{API}/mailtemplates/{protected_mail_template.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(
            f"{API}/mailtemplates/{fake_id}", headers=auth_headers
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/mailtemplates/{fake_id}")
        assert resp.status_code in (401, 403)
