"""Tests for schemas/policies.py - Policy schema validation."""

from pydantic import ValidationError
import pytest

from schemas.policies import PolicyCreate, PolicyUpdate, PolicyUserAgree


class TestPolicyCreate:
    def test_valid_create(self):
        p = PolicyCreate(
            name="Terms of Service",
            content="You must agree to these terms.",
        )
        assert p.name == "Terms of Service"
        assert p.content == "You must agree to these terms."
        assert p.description is None

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            PolicyCreate(content="content")

    def test_missing_content_raises(self):
        with pytest.raises(ValidationError):
            PolicyCreate(name="Test")

    def test_optional_description(self):
        p = PolicyCreate(name="Test", content="content", description="A policy")
        assert p.description == "A policy"


class TestPolicyUpdate:
    def test_valid_update(self):
        u = PolicyUpdate(name="Updated Policy")
        assert u.name == "Updated Policy"

    def test_all_optional(self):
        u = PolicyUpdate()
        assert u.name is None
        assert u.content is None
        assert u.active is None

    def test_update_active(self):
        u = PolicyUpdate(active=True)
        assert u.active is True


class TestPolicyUserAgree:
    def test_default_false(self):
        a = PolicyUserAgree()
        assert a.agree is False

    def test_agree_true(self):
        a = PolicyUserAgree(agree=True)
        assert a.agree is True
