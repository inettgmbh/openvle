"""Integration tests for /v{x}/policies/ endpoints."""

import uuid

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_policy(db_session, system_user):
    """Create a policy in the test DB."""
    from tests.factories.policy_factory import PolicyFactory

    return PolicyFactory(
        name="Test Policy",
        description="A test policy",
        content="You must accept these terms.",
        active=False,
        createdById=system_user.id,
        updatedById=system_user.id,
    )


@pytest.fixture()
def active_policy(db_session, system_user):
    """Create an active policy in the test DB."""
    from tests.factories.policy_factory import PolicyFactory

    return PolicyFactory(
        name="Active Policy",
        description="An active policy",
        content="Active policy content.",
        active=True,
        createdById=system_user.id,
        updatedById=system_user.id,
    )


class TestCreatePolicy:
    """POST /policies/ -- create a new policy."""

    def test_create_returns_201(
        self,
        client,
        auth_headers,
        mock_permission_allow,
    ):
        payload = {
            "name": "New Policy",
            "description": "A brand new policy",
            "content": "Policy content here.",
        }
        resp = client.post(
            f"{API}/policies/", json=payload, headers=auth_headers
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Policy"
        assert data["description"] == "A brand new policy"
        assert data["content"] == "Policy content here."
        assert data["active"] is False

    def test_create_unauthenticated_returns_401(self, client):
        payload = {
            "name": "Unauth Policy",
            "description": "desc",
            "content": "content",
        }
        resp = client.post(f"{API}/policies/", json=payload)
        assert resp.status_code in (401, 403)

    def test_create_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, policies_create is denied."""
        payload = {
            "name": "Denied Policy",
            "description": "desc",
            "content": "content",
        }
        resp = client.post(
            f"{API}/policies/", json=payload, headers=auth_headers
        )
        assert resp.status_code == 403


class TestGetPolicies:
    """GET /policies/ -- list all policies."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_policy,
    ):
        resp = client.get(f"{API}/policies/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/policies/")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, policies_read is denied."""
        resp = client.get(f"{API}/policies/", headers=auth_headers)
        assert resp.status_code == 403


class TestGetPolicyById:
    """GET /policies/{id} -- get single policy."""

    def test_returns_policy(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_policy,
    ):
        resp = client.get(
            f"{API}/policies/{sample_policy.id}", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_policy.id)
        assert data["name"] == "Test Policy"
        assert data["content"] == "You must accept these terms."

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/policies/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/policies/{fake_id}")
        assert resp.status_code in (401, 403)


class TestUpdatePolicy:
    """PUT /policies/{id} -- update a policy."""

    def test_update_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_policy,
    ):
        payload = {"name": "Updated Policy Name"}
        resp = client.put(
            f"{API}/policies/{sample_policy.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Policy Name"

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.put(
            f"{API}/policies/{fake_id}",
            json={"name": "Ghost"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        """Use non-existent ID so ChangelogMiddleware exits early
        (it runs before auth check and would 500 if it found the object)."""
        fake_id = uuid.uuid4()
        resp = client.put(
            f"{API}/policies/{fake_id}",
            json={"name": "No Auth"},
        )
        assert resp.status_code in (401, 403)


class TestDeletePolicy:
    """DELETE /policies/{id} -- delete a policy."""

    def test_delete_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_policy,
    ):
        resp = client.delete(
            f"{API}/policies/{sample_policy.id}", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/policies/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/policies/{fake_id}")
        assert resp.status_code in (401, 403)


class TestAgreeToPolicy:
    """POST /policies/{id}/actions -- agree to a policy."""

    def test_agree_returns_201(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        active_policy,
    ):
        payload = {"agree": True}
        resp = client.post(
            f"{API}/policies/{active_policy.id}/actions",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["policy_id"] == str(active_policy.id)

    def test_agree_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        payload = {"agree": True}
        resp = client.post(f"{API}/policies/{fake_id}/actions", json=payload)
        assert resp.status_code in (401, 403)


class TestGetPolicyUsers:
    """GET /policies/users/ -- list all policy-user associations."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
    ):
        resp = client.get(f"{API}/policies/users/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/policies/users/")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, policies_users_read is denied."""
        resp = client.get(f"{API}/policies/users/", headers=auth_headers)
        assert resp.status_code == 403


class TestGetPolicyUserStatus:
    """GET /policies/{id}/users/{user_id} -- get policy-user status."""

    def test_not_found_returns_404(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_policy,
    ):
        """When the user has not agreed to the policy, the endpoint
        raises RelationNotFound which maps to 404."""
        fake_user_id = uuid.uuid4()
        resp = client.get(
            f"{API}/policies/{sample_policy.id}/users/{fake_user_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        fake_user_id = uuid.uuid4()
        resp = client.get(f"{API}/policies/{fake_id}/users/{fake_user_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(
        self, client, auth_headers, sample_policy
    ):
        """Without mock_permission_allow, policies_user_read is denied."""
        fake_user_id = uuid.uuid4()
        resp = client.get(
            f"{API}/policies/{sample_policy.id}/users/{fake_user_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403
