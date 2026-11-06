"""Tests for core/mail.py - Email construction and template rendering."""

import uuid
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart

import pytest
from core.exceptions import MailGenerationError
from core.mail import mail_construct
from models import User


@pytest.fixture()
def recipient_user(db_session, system_user):
    """Create a recipient user that mail_construct can look up by email."""
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        username="recipient",
        name="Recipient User",
        email="recipient@example.com",
        hashed_password=None,
        status="Active",
        locale="de_DE",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(user)
    db_session.flush()
    return user


class TestMailConstruct:
    def test_constructs_basic_email(self, db_session, system_user, monkeypatch):
        """mail_construct returns a MIMEMultipart message with correct From/To/Subject."""
        monkeypatch.setattr("core.mail.SessionLocal", lambda: db_session)

        msg = mail_construct(
            to_mail="someone@example.com",
            subject="Test Subject",
            content_plain="Hello plain",
            from_name="Sender",
            from_mail="sender@example.com",
        )

        assert isinstance(msg, MIMEMultipart)
        assert msg["Subject"] == "Test Subject"
        assert "sender@example.com" in msg["From"]
        assert msg["To"] == "someone@example.com"

    def test_renders_template_with_user_context(
        self, db_session, system_user, recipient_user, monkeypatch
    ):
        """Template variables like {{ user.name }} are rendered with user data."""
        monkeypatch.setattr("core.mail.SessionLocal", lambda: db_session)

        msg = mail_construct(
            to_mail=recipient_user.email,
            subject="Hello",
            content_plain="Hello {{ user.name }}, your username is {{ user.username }}.",
            from_name="KVS",
            from_mail="kvs@example.com",
        )

        payload = msg.get_payload()
        plain_part = payload[0].get_payload()
        assert "Recipient User" in plain_part
        assert "recipient" in plain_part

    def test_renders_html_and_plain(self, db_session, system_user, monkeypatch):
        """Both HTML and plain text parts are attached when contentHTML is provided."""
        monkeypatch.setattr("core.mail.SessionLocal", lambda: db_session)

        msg = mail_construct(
            to_mail="test@example.com",
            subject="Multi",
            content_plain="Plain text body",
            content_html="<p>HTML body</p>",
            from_name="KVS",
            from_mail="kvs@example.com",
        )

        payload = msg.get_payload()
        assert len(payload) == 2
        content_types = [part.get_content_type() for part in payload]
        assert "text/plain" in content_types
        assert "text/html" in content_types

    def test_plain_text_only_when_no_html(
        self, db_session, system_user, monkeypatch
    ):
        """Only plain text is attached when contentHTML is empty."""
        monkeypatch.setattr("core.mail.SessionLocal", lambda: db_session)

        msg = mail_construct(
            to_mail="test@example.com",
            subject="Plain only",
            content_plain="Just plain text",
            content_html="",
            from_name="KVS",
            from_mail="kvs@example.com",
        )

        payload = msg.get_payload()
        assert len(payload) == 1
        assert payload[0].get_content_type() == "text/plain"

    def test_context_objects_added(
        self,
        db_session,
        system_user,
        recipient_user,
        event_statuses,
        sample_course,
        monkeypatch,
    ):
        """Context objects like Event are serialized into template context."""
        from models import Event

        monkeypatch.setattr("core.mail.SessionLocal", lambda: db_session)

        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name="Test Event",
            slug="tst-evt",
            dateStart=now.date(),
            dateEnd=now.date(),
            guacamole=True,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(event)
        db_session.flush()

        msg = mail_construct(
            to_mail=recipient_user.email,
            subject="Event Mail",
            content_plain="Event: {{ event.name }}, Slug: {{ event.slug }}",
            context_objects=[event],
            from_name="KVS",
            from_mail="kvs@example.com",
        )

        payload = msg.get_payload()
        plain_text = payload[0].get_payload()
        assert "Test Event" in plain_text
        assert "tst-evt" in plain_text

    def test_unknown_recipient_uses_defaults(
        self, db_session, system_user, monkeypatch
    ):
        """When user is not found by email, uses 'unknown' as name and username."""
        monkeypatch.setattr("core.mail.SessionLocal", lambda: db_session)

        msg = mail_construct(
            to_mail="nobody@nowhere.com",
            subject="Hello",
            content_plain="Hello {{ user.name }}, username={{ user.username }}",
            from_name="KVS",
            from_mail="kvs@example.com",
        )

        payload = msg.get_payload()
        plain_text = payload[0].get_payload()
        assert "unknown" in plain_text

    def test_template_render_error_raises(
        self, db_session, system_user, monkeypatch
    ):
        """Invalid Jinja2 template raises MailGenerationError."""
        monkeypatch.setattr("core.mail.SessionLocal", lambda: db_session)

        with pytest.raises(MailGenerationError):
            mail_construct(
                to_mail="test@example.com",
                subject="Bad Template",
                content_plain="{{ invalid | nonexistent_filter }}",
                from_name="KVS",
                from_mail="kvs@example.com",
            )
