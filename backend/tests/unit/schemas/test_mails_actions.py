"""Tests for schemas/mails_actions.py - MailAction schema validation."""

from pydantic import ValidationError
import pytest

from schemas.mails_actions import MailActionCreate


class TestMailActionCreate:
    def test_valid_create(self):
        ma = MailActionCreate(
            name="Password Reset",
            description="Triggered on password reset",
            slug="password-reset",
        )
        assert ma.name == "Password Reset"
        assert ma.slug == "password-reset"

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            MailActionCreate(description="desc", slug="slug")

    def test_missing_slug_raises(self):
        with pytest.raises(ValidationError):
            MailActionCreate(name="Test", description="desc")

    def test_missing_description_raises(self):
        with pytest.raises(ValidationError):
            MailActionCreate(name="Test", slug="test")
