"""
Integration test fixtures.

Provides FastAPI TestClient with full middleware stack and auth fixtures.
"""

import asyncio
import uuid
from datetime import datetime, timezone

import httpx
import pytest

from core.config import Settings

# Shared fixtures (system_user, active_user, mock_permission_allow, etc.)
# are registered via pytest_plugins in tests/conftest.py (root level).

_settings = Settings()
API = f"/v{str(_settings.project_version)[0]}"


class ASGIClient:
    """Sync test client for ASGI apps using httpx.ASGITransport.

    Bridges the incompatibility between Starlette 0.26.1 and httpx 0.28.1
    where Starlette's TestClient tries to pass ``app`` to httpx.Client
    which no longer accepts it.
    """

    def __init__(self, app, base_url="http://testserver"):
        self._app = app
        self._base_url = base_url

    def _request(self, method, url, **kwargs):
        async def _run():
            transport = httpx.ASGITransport(app=self._app)
            async with httpx.AsyncClient(
                transport=transport, base_url=self._base_url
            ) as client:
                return await client.request(method, url, **kwargs)

        return asyncio.run(_run())

    def get(self, url, **kwargs):
        return self._request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self._request("PUT", url, **kwargs)

    def delete(self, url, **kwargs):
        return self._request("DELETE", url, **kwargs)

    def patch(self, url, **kwargs):
        return self._request("PATCH", url, **kwargs)


@pytest.fixture()
def client(db_session, system_user, active_user, monkeypatch):
    """Create a test client with full middleware stack.

    Builds the app manually (not main.app) to avoid tasks_enqueue()
    and other module-level side effects.

    Monkeypatches SessionLocal everywhere so all DB access paths
    (get_db dependency, AuthenticationMiddleware, ChangelogMiddleware,
    activityLogging) use the SAVEPOINT-protected test session.
    """

    # Callable that returns the test session (replaces sessionmaker)
    def factory():
        return db_session

    # Patch SessionLocal in every module that captured its own reference
    import core.mariadb as mariadb_mod

    monkeypatch.setattr(mariadb_mod, "SessionLocal", factory)

    import middlewares.authentication as auth_mid

    monkeypatch.setattr(auth_mid, "SessionLocal", factory)

    import middlewares.changelog as changelog_mid

    monkeypatch.setattr(changelog_mid, "SessionLocal", factory)

    import middlewares.logging as logging_mid

    monkeypatch.setattr(logging_mid, "SessionLocal", factory)

    import core.dependencies as deps_mod

    monkeypatch.setattr(deps_mod, "SessionLocal", factory)

    # User schema's user_type property calls SessionLocal() directly
    import schemas.users as schemas_users_mod

    monkeypatch.setattr(schemas_users_mod, "SessionLocal", factory)

    # Build the FastAPI app
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi_pagination import add_pagination
    from starlette.exceptions import HTTPException
    from starlette.middleware.authentication import AuthenticationMiddleware
    from starlette.middleware.sessions import SessionMiddleware

    from core.dependencies import get_db
    from core.exception_handler import http_exception_handler
    from middlewares.authentication import AuthBackend
    from middlewares.language import LanguageMiddleware
    from middlewares.logging import activityLogging
    from routes import app_router, misc

    app = FastAPI()
    app.add_exception_handler(HTTPException, http_exception_handler)
    add_pagination(app)

    # Override get_db dependency
    def override_get_db():
        db_session.current_user_id = None
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Middleware stack (same order as main.py)
    app.add_middleware(LanguageMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.add_middleware(AuthenticationMiddleware, backend=AuthBackend())
    app.middleware("http")(activityLogging)
    app.add_middleware(SessionMiddleware, secret_key="test-session-secret")

    # Include routes
    app.include_router(app_router)
    app.include_router(misc.router)

    yield ASGIClient(app)


@pytest.fixture()
def auth_headers(active_user):
    """JWT Bearer token headers for the active_user."""
    from tests.helpers.auth_helpers import create_test_token

    token = create_test_token(active_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def expired_auth_headers(active_user):
    """Expired JWT Bearer token headers."""
    from tests.helpers.auth_helpers import create_expired_token

    token = create_expired_token(active_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_user(db_session, system_user, role_admin):
    """Create an admin user with admin_full role and all permissions."""
    from models import User
    from models.associations import user_role_association_table

    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        username="adminuser",
        name="Admin User",
        email="admin@example.com",
        hashed_password="$2b$12$dummyhashvalue",
        status="Active",
        locale="de_DE",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(user)
    db_session.flush()

    # Assign admin_full role
    db_session.execute(
        user_role_association_table.insert().values(
            user_id=user.id, role_id=role_admin.id
        )
    )
    db_session.flush()
    return user


@pytest.fixture()
def admin_headers(admin_user):
    """JWT Bearer token headers for the admin_user."""
    from tests.helpers.auth_helpers import create_test_token

    token = create_test_token(admin_user)
    return {"Authorization": f"Bearer {token}"}
