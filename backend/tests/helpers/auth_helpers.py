"""JWT token generation helpers for testing."""

from datetime import datetime, timedelta, timezone

from core.config import Settings
from jose import jwt

settings = Settings()


def create_test_token(user, *, token_type="bearer", lifetime_minutes=480):
    """Generate a valid JWT token for testing."""
    now = datetime.now(timezone.utc)
    payload = {
        "type": token_type,
        "exp": now + timedelta(minutes=lifetime_minutes),
        "iat": now,
        "nbf": now - timedelta(seconds=5),
        "sub": str(user.id),
        "aud": settings.project_name,
        "iss": settings.project_name,
        "user": {
            "username": user.username,
            "email": user.email,
            "name": user.name,
        },
    }
    return jwt.encode(
        payload,
        settings.auth_secret,
        algorithm=settings.auth_algorithm,
    )


def create_expired_token(user):
    """Generate an expired JWT token for testing."""
    return create_test_token(user, lifetime_minutes=-10)
