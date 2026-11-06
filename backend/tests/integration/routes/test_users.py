"""Integration tests for /v{x}/users/ endpoints."""

import uuid
from datetime import datetime, timezone

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_user(db_session, system_user):
    """Create a separate user for testing (not the authenticated user)."""
    from models import User

    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        username=f"sampleuser_{uuid.uuid4().hex[:8]}",
        name="Sample User",
        email=f"sample_{uuid.uuid4().hex[:8]}@example.com",
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
    return user


# ------------------------------------------------------------------
# POST /users/ -- create a new user
# ------------------------------------------------------------------
class TestCreateUser:
    """POST /users/ -- create a new user."""

    def test_create_returns_201(
        self, client, auth_headers, mock_permission_allow
    ):
        payload = {
            "username": f"newuser_{uuid.uuid4().hex[:8]}",
            "email": f"newuser_{uuid.uuid4().hex[:8]}@example.com",
            "name": "New User",
            "password": "TestPassword123!!",
            "password_repeat": "TestPassword123!!",
        }
        resp = client.post(f"{API}/users/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New User"
        assert "id" in data
        leaked = SENSITIVE_USER_FIELDS & data.keys()
        assert not leaked, (
            f"Sensitive fields leaked in POST /users/ response: {leaked}"
        )

    def test_create_unauthenticated_returns_401(self, client):
        payload = {
            "username": "noauth_user",
            "email": "noauth@example.com",
            "name": "No Auth",
        }
        resp = client.post(f"{API}/users/", json=payload)
        assert resp.status_code in (401, 403)

    def test_create_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, users_create is denied."""
        payload = {
            "username": "denied_user",
            "email": "denied@example.com",
            "name": "Denied User",
        }
        resp = client.post(f"{API}/users/", json=payload, headers=auth_headers)
        assert resp.status_code == 403


# ------------------------------------------------------------------
# GET /users/ -- list all users
# ------------------------------------------------------------------
SENSITIVE_USER_FIELDS = {
    "hashed_password",
    "resetToken",
    "resetTokenCreatedAt",
    "twoFactorSecret",
    "mailValidateToken",
    "password",
}


class TestGetUsers:
    """GET /users/ -- list all users."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        resp = client.get(f"{API}/users/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_items_contain_user_type(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        """Every user in the list must include user_type."""
        resp = client.get(f"{API}/users/", headers=auth_headers)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1
        for item in items:
            assert "user_type" in item, (
                f"user_type missing for user {item.get('id')}"
            )
            assert item["user_type"] in ("internal", "external")

    def test_no_sensitive_fields_in_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        """Ensure hashed_password and other secrets are never exposed."""
        resp = client.get(f"{API}/users/", headers=auth_headers)
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            leaked = SENSITIVE_USER_FIELDS & item.keys()
            assert not leaked, (
                f"Sensitive fields leaked in GET /users/ response: {leaked}"
            )

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/users/")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, users_read is denied."""
        resp = client.get(f"{API}/users/", headers=auth_headers)
        assert resp.status_code == 403


# ------------------------------------------------------------------
# GET /users/ with users_search permission (limited access)
# ------------------------------------------------------------------
@pytest.fixture()
def mock_permission_search_only(monkeypatch):
    """Patch PermissionChecker so only users_search is granted."""
    from core.dependencies import PermissionChecker

    def _selective(self):
        return "users_search" in (self.permissions_required or [])

    monkeypatch.setattr(PermissionChecker, "has_permission", _selective)


class TestGetUsersSearch:
    """GET /users/ with users_search permission (limited access)."""

    def test_requires_search_field(
        self, client, auth_headers, mock_permission_search_only
    ):
        """Missing search_field returns 422."""
        resp = client.get(
            f"{API}/users/",
            params={"search_value": "test"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_requires_search_value(
        self, client, auth_headers, mock_permission_search_only
    ):
        """Missing search_value returns 422."""
        resp = client.get(
            f"{API}/users/",
            params={"search_field": "email"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_invalid_search_field_returns_422(
        self, client, auth_headers, mock_permission_search_only
    ):
        """search_field not in allowed list returns 422."""
        resp = client.get(
            f"{API}/users/",
            params={
                "search_field": "hashed_password",
                "search_value": "x",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_invalid_sort_by_returns_422(
        self, client, auth_headers, mock_permission_search_only
    ):
        """sort_by a field not visible in UserSearch returns 422."""
        resp = client.get(
            f"{API}/users/",
            params={
                "search_field": "email",
                "search_value": "test",
                "sort_by": "createdAt",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_returns_limited_schema(
        self,
        client,
        auth_headers,
        mock_permission_search_only,
        sample_user,
    ):
        """Response uses UserSearch schema (no roles, permissions, etc.)."""
        resp = client.get(
            f"{API}/users/",
            params={
                "search_field": "username",
                "search_value": sample_user.username,
                "sort_by": "username",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1
        item = data["items"][0]
        # Only UserSearch fields should be present
        assert "id" in item
        assert "username" in item
        # Full User fields must be absent
        assert "roles" not in item
        assert "permissions" not in item
        assert "status" not in item
        assert "hashed_password" not in item

    def test_limit_capped_at_25(
        self,
        client,
        auth_headers,
        mock_permission_search_only,
        sample_user,
    ):
        """Requesting limit>25 still returns at most 25 per page."""
        resp = client.get(
            f"{API}/users/",
            params={
                "search_field": "username",
                "search_value": sample_user.username,
                "sort_by": "username",
                "limit": 500,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pageDetails"]["perPage"] == 25

    def test_page_always_forced_to_1(
        self,
        client,
        auth_headers,
        mock_permission_search_only,
        sample_user,
    ):
        """Requesting page>1 still returns page 1."""
        resp = client.get(
            f"{API}/users/",
            params={
                "search_field": "username",
                "search_value": sample_user.username,
                "sort_by": "username",
                "page": 999,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pageDetails"]["page"] == 1

    def test_valid_sort_by_accepted(
        self, client, auth_headers, mock_permission_search_only, sample_user
    ):
        """sort_by a valid UserSearch field works."""
        for field in ("email", "username", "name", "id"):
            resp = client.get(
                f"{API}/users/",
                params={
                    "search_field": "username",
                    "search_value": sample_user.username,
                    "sort_by": field,
                },
                headers=auth_headers,
            )
            assert resp.status_code == 200, (
                f"sort_by={field} should be accepted"
            )


# ------------------------------------------------------------------
# GET /users/{id} -- get single user
# ------------------------------------------------------------------
class TestGetUserById:
    """GET /users/{id} -- get single user."""

    def test_returns_user(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        resp = client.get(f"{API}/users/{sample_user.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_user.id)
        assert data["name"] == sample_user.name

    def test_response_contains_user_type(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        """user_type must be present and correct for internal users."""
        resp = client.get(f"{API}/users/{sample_user.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "user_type" in data, (
            "user_type field missing from GET /users/{id}"
        )
        assert data["user_type"] == "internal"

    def test_no_sensitive_fields_in_response(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        """Ensure hashed_password and other secrets are never exposed."""
        resp = client.get(f"{API}/users/{sample_user.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        leaked = SENSITIVE_USER_FIELDS & data.keys()
        assert not leaked, (
            f"Sensitive fields leaked in GET /users/{{id}} response: {leaked}"
        )

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/users/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/users/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(
        self, client, auth_headers, sample_user
    ):
        """Without mock_permission_allow, users_read is denied."""
        resp = client.get(f"{API}/users/{sample_user.id}", headers=auth_headers)
        assert resp.status_code == 403


# ------------------------------------------------------------------
# PUT /users/{id} -- update a user
# ------------------------------------------------------------------
class TestUpdateUser:
    """PUT /users/{id} -- update a user."""

    def test_update_user_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        payload = {
            "name": "Updated Name",
            "email": sample_user.email,
            "status": "Active",
        }
        resp = client.put(
            f"{API}/users/{sample_user.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Name"

    def test_update_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        payload = {"name": "Ghost User", "email": "ghost@example.com"}
        resp = client.put(
            f"{API}/users/{fake_id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_update_unauthenticated_returns_401(self, client):
        """Use non-existent ID so ChangelogMiddleware exits early
        (it runs as a dependency before auth check)."""
        fake_id = uuid.uuid4()
        payload = {"name": "No Auth User"}
        resp = client.put(f"{API}/users/{fake_id}", json=payload)
        assert resp.status_code in (401, 403)

    def test_update_permission_denied_returns_403(
        self, client, auth_headers, sample_user
    ):
        """Without mock_permission_allow, users_update is denied."""
        payload = {"name": "Denied Update"}
        resp = client.put(
            f"{API}/users/{sample_user.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# DELETE /users/{id} -- delete a user
# ------------------------------------------------------------------
class TestDeleteUser:
    """DELETE /users/{id} -- delete a user."""

    def test_delete_user_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        mock_redis_queues,
        sample_user,
    ):
        resp = client.delete(
            f"{API}/users/{sample_user.id}", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/users/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/users/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_delete_permission_denied_returns_403(
        self, client, auth_headers, sample_user
    ):
        """Without mock_permission_allow, users_delete is denied."""
        resp = client.delete(
            f"{API}/users/{sample_user.id}", headers=auth_headers
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# GET /users/{id}/delete-preview -- preview cascade delete
# ------------------------------------------------------------------
class TestDeletePreview:
    """GET /users/{id}/delete-preview -- preview objects deleted with user."""

    def test_delete_preview_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        resp = client.get(
            f"{API}/users/{sample_user.id}/delete-preview",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_delete_preview_response_shape(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        resp = client.get(
            f"{API}/users/{sample_user.id}/delete-preview",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "stats" in data
        list_fields = (
            "virtual_machines",
            "connections",
            "mails",
            "changelogs",
            "object_permissions",
            "tags",
            "event_memberships",
        )
        for field in list_fields:
            assert field in data, f"missing list field '{field}'"
            assert "items" in data[field], f"'{field}' missing 'items' wrapper"
            assert "truncated" in data[field], (
                f"'{field}' missing 'truncated' wrapper"
            )

    def test_delete_preview_stats_shape(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        resp = client.get(
            f"{API}/users/{sample_user.id}/delete-preview",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        stats = resp.json()["stats"]
        assert "virtual_machines" in stats
        assert "connections" in stats
        assert "mails" in stats
        assert "changelogs" in stats
        assert "object_permissions" in stats
        assert "event_memberships" in stats
        assert "policy_memberships" in stats
        assert "tags" in stats

    def test_delete_preview_empty_user_has_zero_stats(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        resp = client.get(
            f"{API}/users/{sample_user.id}/delete-preview",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        stats = resp.json()["stats"]
        assert stats["virtual_machines"] == 0
        assert stats["mails"] == 0
        assert stats["tags"] == 0

    def test_delete_preview_not_found(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.get(
            f"{API}/users/{fake_id}/delete-preview",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_delete_preview_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/users/{fake_id}/delete-preview")
        assert resp.status_code in (401, 403)


# ------------------------------------------------------------------
# POST /users/{id}/password -- set user password
# ------------------------------------------------------------------
class TestSetPassword:
    """POST /users/{id}/password -- set a user's password."""

    def test_set_password_returns_201(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        payload = {
            "password_new": "SecurePass12!!",
            "password_new_repeat": "SecurePass12!!",
        }
        resp = client.post(
            f"{API}/users/{sample_user.id}/password",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 201

    def test_set_password_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        payload = {
            "password_new": "SomePass123",
            "password_new_repeat": "SomePass123",
        }
        resp = client.post(f"{API}/users/{fake_id}/password", json=payload)
        assert resp.status_code in (401, 403)

    def test_set_password_permission_denied_returns_403(
        self, client, auth_headers, sample_user
    ):
        """Without mock_permission_allow, users_set_password is denied."""
        payload = {
            "password_new": "SomePass123",
            "password_new_repeat": "SomePass123",
        }
        resp = client.post(
            f"{API}/users/{sample_user.id}/password",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# PUT /users/{id}/roles -- set (overwrite) user roles
# ------------------------------------------------------------------
class TestSetUserRoles:
    """PUT /users/{id}/roles -- set (overwrite) user roles."""

    def test_set_roles_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
        role_teacher,
    ):
        payload = {
            "roles": [{"key": role_teacher.key}],
        }
        resp = client.put(
            f"{API}/users/{sample_user.id}/roles",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        role_keys = [r["key"] for r in data.get("roles", [])]
        assert role_teacher.key in role_keys

    def test_set_roles_unauthenticated_returns_401(self, client):
        """Use non-existent ID so ChangelogMiddleware exits early (PUT)."""
        fake_id = uuid.uuid4()
        payload = {"roles": []}
        resp = client.put(f"{API}/users/{fake_id}/roles", json=payload)
        assert resp.status_code in (401, 403)

    def test_set_roles_permission_denied_returns_403(
        self, client, auth_headers, sample_user
    ):
        """Without mock_permission_allow, users_update is denied."""
        payload = {"roles": [{"key": "admin_full"}]}
        resp = client.put(
            f"{API}/users/{sample_user.id}/roles",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# POST /users/{id}/roles -- update (append) user roles
# ------------------------------------------------------------------
class TestUpdateUserRoles:
    """POST /users/{id}/roles -- append user roles."""

    def test_update_roles_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
        role_teacher,
    ):
        payload = {
            "roles": [{"key": role_teacher.key}],
        }
        resp = client.post(
            f"{API}/users/{sample_user.id}/roles",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        role_keys = [r["key"] for r in data.get("roles", [])]
        assert role_teacher.key in role_keys

    def test_update_roles_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        payload = {"roles": []}
        resp = client.post(f"{API}/users/{fake_id}/roles", json=payload)
        assert resp.status_code in (401, 403)

    def test_update_roles_permission_denied_returns_403(
        self, client, auth_headers, sample_user
    ):
        """Without mock_permission_allow, users_update is denied."""
        payload = {"roles": [{"key": "admin_full"}]}
        resp = client.post(
            f"{API}/users/{sample_user.id}/roles",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# GET /users/{id}/permissions -- get effective permissions
# ------------------------------------------------------------------
class TestGetUserPermissions:
    """GET /users/{id}/permissions -- get effective permissions."""

    def test_returns_permissions(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        resp = client.get(
            f"{API}/users/{sample_user.id}/permissions",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Returns a list of permission group objects
        assert isinstance(data, list)

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/users/{fake_id}/permissions")
        assert resp.status_code in (401, 403)


# ------------------------------------------------------------------
# GET /users/{id}/guacamole -- get user's guacamole connections
# ------------------------------------------------------------------
class TestGetUserGuacamole:
    """GET /users/{id}/guacamole -- get user's guacamole connections."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        resp = client.get(
            f"{API}/users/{sample_user.id}/guacamole",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert data["items"] == []

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/users/{fake_id}/guacamole")
        assert resp.status_code in (401, 403)


# ------------------------------------------------------------------
# GET /users/{id}/events -- get user's events
# ------------------------------------------------------------------
class TestGetUserEvents:
    """GET /users/{id}/events -- get user's events."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        resp = client.get(
            f"{API}/users/{sample_user.id}/events",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert data["items"] == []

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/users/{fake_id}/events")
        assert resp.status_code in (401, 403)


# ------------------------------------------------------------------
# GET /users/{id}/virtual-machines -- get user's VMs
# ------------------------------------------------------------------
class TestGetUserVirtualMachines:
    """GET /users/{id}/virtual-machines -- get user's VMs."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_user,
    ):
        resp = client.get(
            f"{API}/users/{sample_user.id}/virtual-machines",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert data["items"] == []

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/users/{fake_id}/virtual-machines")
        assert resp.status_code in (401, 403)
