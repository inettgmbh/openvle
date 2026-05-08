"""Tests for core/auth.py - JWT, password hashing, authentication."""

import uuid
from datetime import datetime, timezone

import pytest
from jose import jwt

from core.auth import (
    authenticate,
    create_access_token,
    enrollment,
    get_password_hash,
    verify_password,
)
from core.config import Settings
from core.exceptions import BadRequestError, IncorrectCredentials
from models import User

settings = Settings()


class TestPasswordHashing:
    def test_hash_and_verify_success(self):
        password = "MySecretPassword123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)

    def test_verify_wrong_password_returns_false(self):
        hashed = get_password_hash("correct_password")
        assert not verify_password("wrong_password", hashed)

    def test_hash_is_not_plaintext(self):
        password = "MySecretPassword123!"
        hashed = get_password_hash(password)
        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_different_hashes_for_same_password(self):
        password = "SamePassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2  # Different salts

    def test_hash_returns_str(self):
        hashed = get_password_hash("password")
        assert isinstance(hashed, str)

    def test_verify_handles_unicode_password(self):
        password = "pässwörd-🔑-123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)
        assert not verify_password("password-🔑-123", hashed)

    def test_verify_invalid_hash_returns_false(self):
        # Direct bcrypt raises ValueError on malformed hash; we must not leak it.
        assert not verify_password("password", "not-a-bcrypt-hash")

    def test_verify_empty_inputs_return_false(self):
        assert not verify_password("", "")
        assert not verify_password("password", "")
        assert not verify_password("", get_password_hash("password"))

    def test_verify_fixed_bcrypt_hash(self):
        # Pre-computed $2b$ bcrypt hash of "testpassword123". passlib (now
        # removed) produced this same format, so existing DB rows hashed
        # before the migration must continue to verify.
        fixed_hash = "$2b$12$hWVjRPaaPt3hXGPmuSGqtenU.jU.2iJZ6F3I0L8FnecRwft.pd452"
        assert verify_password("testpassword123", fixed_hash)
        assert not verify_password("wrongpassword", fixed_hash)


class TestCreateAccessToken:
    def _make_user(self):
        return User(
            id=uuid.uuid4(),
            username="tokenuser",
            email="token@example.com",
            name="Token User",
            status="Active",
            locale="de_DE",
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
        )

    def test_creates_valid_jwt_format(self):
        user = self._make_user()
        token = create_access_token(user=user, type="bearer")
        # JWT has 3 dot-separated parts
        parts = token.split(".")
        assert len(parts) == 3

    def test_token_contains_user_id_as_sub(self):
        user = self._make_user()
        token = create_access_token(user=user, type="bearer")
        payload = jwt.decode(
            token,
            settings.auth_secret,
            algorithms=[settings.auth_algorithm],
            audience=settings.project_name,
        )
        assert payload["sub"] == str(user.id)

    def test_token_contains_correct_type(self):
        user = self._make_user()
        token = create_access_token(user=user, type="bearer")
        payload = jwt.decode(
            token,
            settings.auth_secret,
            algorithms=[settings.auth_algorithm],
            audience=settings.project_name,
        )
        assert payload["type"] == "bearer"

    def test_token_has_audience_and_issuer(self):
        user = self._make_user()
        token = create_access_token(user=user, type="bearer")
        payload = jwt.decode(
            token,
            settings.auth_secret,
            algorithms=[settings.auth_algorithm],
            audience=settings.project_name,
        )
        assert payload["aud"] == settings.project_name
        assert payload["iss"] == settings.project_name

    def test_token_has_user_details(self):
        user = self._make_user()
        token = create_access_token(user=user, type="bearer")
        payload = jwt.decode(
            token,
            settings.auth_secret,
            algorithms=[settings.auth_algorithm],
            audience=settings.project_name,
        )
        assert payload["user"]["username"] == user.username
        assert payload["user"]["email"] == user.email
        assert payload["user"]["name"] == user.name

    def test_token_expiry_set(self):
        user = self._make_user()
        token = create_access_token(user=user, type="bearer")
        payload = jwt.decode(
            token,
            settings.auth_secret,
            algorithms=[settings.auth_algorithm],
            audience=settings.project_name,
        )
        assert "exp" in payload
        assert "iat" in payload
        assert "nbf" in payload


class TestAuthenticate:
    def test_valid_local_credentials(self, db_session, system_user):
        password = "testpass123"
        hashed = get_password_hash(password)
        now = datetime.now(timezone.utc)
        user = User(
            id=uuid.uuid4(),
            username="authuser",
            email="auth@example.com",
            name="Auth User",
            hashed_password=hashed,
            status="Active",
            locale="de_DE",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(user)
        db_session.flush()

        result = authenticate(username="authuser", password=password, db=db_session)
        assert result is not None
        assert result.username == "authuser"

    def test_wrong_password_raises_incorrect_credentials(self, db_session, system_user):
        password = "correctpass"
        hashed = get_password_hash(password)
        now = datetime.now(timezone.utc)
        user = User(
            id=uuid.uuid4(),
            username="authuser2",
            email="auth2@example.com",
            name="Auth User 2",
            hashed_password=hashed,
            status="Active",
            locale="de_DE",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(user)
        db_session.flush()

        with pytest.raises(IncorrectCredentials):
            authenticate(username="authuser2", password="wrongpass", db=db_session)

    def test_nonexistent_user_raises_incorrect_credentials(self, db_session):
        with pytest.raises(IncorrectCredentials):
            authenticate(username="nonexistent", password="pass", db=db_session)

    def test_inactive_user_raises_bad_request(self, db_session, system_user):
        password = "testpass"
        hashed = get_password_hash(password)
        now = datetime.now(timezone.utc)
        user = User(
            id=uuid.uuid4(),
            username="inactive",
            email="inactive@example.com",
            name="Inactive User",
            hashed_password=hashed,
            status="Deactivated",
            locale="de_DE",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(user)
        db_session.flush()

        with pytest.raises(BadRequestError):
            authenticate(username="inactive", password=password, db=db_session)


class TestEnrollment:
    """Tests for enrollment() - creates new user from external auth."""

    def test_enrollment_creates_user(self, db_session, system_user):
        """Should create a new active user with given details."""
        user = enrollment(
            db_session,
            username="ldap_user",
            name="LDAP User",
            email="ldap@example.com",
        )
        assert user is not None
        assert user.username == "ldap_user"
        assert user.name == "LDAP User"
        assert user.email == "ldap@example.com"
        assert user.status == "Active"
        assert user.createdById == system_user.id

    def test_enrollment_user_persisted_in_db(self, db_session, system_user):
        """Enrolled user should be retrievable from DB."""
        user = enrollment(
            db_session,
            username="persisted_user",
            name="Persisted",
            email="persisted@example.com",
        )
        fetched = db_session.get(User, user.id)
        assert fetched is not None
        assert fetched.username == "persisted_user"

    def test_enrollment_duplicate_raises(self, db_session, system_user):
        """Should raise BadRequestError when enrollment fails (e.g. duplicate)."""
        enrollment(
            db_session,
            username="dup_user",
            name="First",
            email="dup@example.com",
        )
        with pytest.raises(BadRequestError):
            enrollment(
                db_session,
                username="dup_user",
                name="Second",
                email="dup2@example.com",
            )
