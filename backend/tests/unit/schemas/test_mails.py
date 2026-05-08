"""Tests for schemas/mails.py - Mail schema validation."""

import uuid

from pydantic import ValidationError
import pytest

from schemas.mails import MailCreate, MailSystemCreate


class TestMailCreate:
    def test_valid_create(self):
        m = MailCreate(
            subject="Welcome",
            fromName="KVS",
            fromMail="noreply@example.com",
            toMail="user@example.com",
            templateId=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )
        assert m.subject == "Welcome"
        assert m.fromName == "KVS"
        assert m.replyTo is None

    def test_missing_subject_raises(self):
        with pytest.raises(ValidationError):
            MailCreate(
                fromName="KVS",
                fromMail="a@b.com",
                toMail="c@d.com",
                templateId=uuid.uuid4(),
                user_id=uuid.uuid4(),
            )

    def test_with_reply_to(self):
        m = MailCreate(
            subject="Test",
            fromName="KVS",
            fromMail="a@b.com",
            toMail="c@d.com",
            templateId=uuid.uuid4(),
            user_id=uuid.uuid4(),
            replyTo="reply@example.com",
        )
        assert m.replyTo == "reply@example.com"


class TestMailSystemCreate:
    def test_valid_system_create(self):
        m = MailSystemCreate(
            subject="System Mail",
            mail_action=uuid.uuid4(),
        )
        assert m.subject == "System Mail"

    def test_missing_subject_raises(self):
        with pytest.raises(ValidationError):
            MailSystemCreate(mail_action=uuid.uuid4())
