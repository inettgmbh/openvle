"""Tests for schemas/auth.py - Auth schema validation."""

from pydantic import ValidationError
import pytest

from schemas.auth import TokenResponse


class TestTokenResponse:
    def test_valid_token_response(self):
        t = TokenResponse(
            token_type="bearer",
            access_token="eyJ...",
        )
        assert t.token_type == "bearer"
        assert t.access_token == "eyJ..."
        assert t.outstanding_policies is None

    def test_with_outstanding_policies(self):
        t = TokenResponse(
            token_type="bearer",
            access_token="eyJ...",
            outstanding_policies=["policy-1", "policy-2"],
        )
        assert len(t.outstanding_policies) == 2

    def test_missing_token_type_raises(self):
        with pytest.raises(ValidationError):
            TokenResponse(access_token="eyJ...")

    def test_missing_access_token_raises(self):
        with pytest.raises(ValidationError):
            TokenResponse(token_type="bearer")
