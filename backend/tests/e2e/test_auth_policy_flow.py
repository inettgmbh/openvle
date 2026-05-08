"""
E2E workflow tests for authentication and policy acceptance flows.

Tests the full auth flow including login, token types, policy
acceptance, reauthentication, and edge cases.
"""

import uuid
from datetime import datetime, timezone


from tests.e2e.conftest import API


# ------------------------------------------------------------------
# Scenario A: Policy acceptance flow
# ------------------------------------------------------------------


class TestPolicyAcceptanceFlow:
    """Multi-step flow: create policy -> login -> agree -> reauth."""

    def test_policy_acceptance_full_flow(
        self,
        client,
        db_session,
        mock_permission_allow,
        login_user,
        auth_headers,
    ):
        """Create active policy, login gets policy_required token,
        agree to policy, reauthenticate gets bearer token."""
        # Step 1: Create an active policy via API
        policy_payload = {
            "name": f"Test Policy {uuid.uuid4().hex[:6]}",
            "description": "Must accept this",
            "content": "Terms and conditions apply.",
        }
        resp = client.post(
            f"{API}/policies/", json=policy_payload, headers=auth_headers
        )
        assert resp.status_code == 201
        policy_id = resp.json()["id"]

        # Step 2: Activate the policy
        resp = client.put(
            f"{API}/policies/{policy_id}",
            json={"active": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["active"] is True

        # Step 3: Login as login_user -> should get policy_required token
        resp = client.post(
            f"{API}/auth/login",
            data={
                "username": login_user.username,
                "password": "testpassword123",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_type"] == "bearer"
        assert "outstanding_policies" in data
        assert data["outstanding_policies"] is not None
        assert len(data["outstanding_policies"]) >= 1
        policy_required_token = data["access_token"]
        policy_headers = {"Authorization": f"Bearer {policy_required_token}"}

        # Step 4: Agree to policy using policy_required token
        resp = client.post(
            f"{API}/policies/{policy_id}/actions",
            json={"agree": True},
            headers=policy_headers,
        )
        assert resp.status_code == 201

        # Step 5: Reauthenticate -> should get normal bearer token
        resp = client.post(
            f"{API}/auth/reauthenticate",
            headers=policy_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_type"] == "bearer"
        # No outstanding policies after agreement
        outstanding = data.get("outstanding_policies")
        assert outstanding is None or len(outstanding) == 0

    def test_inactive_policy_not_outstanding(
        self,
        client,
        db_session,
        mock_permission_allow,
        login_user,
        auth_headers,
    ):
        """Inactive policy should NOT appear in outstanding_policies."""
        # Create inactive policy
        policy_payload = {
            "name": f"Inactive Policy {uuid.uuid4().hex[:6]}",
            "description": "Not active",
            "content": "Should not be outstanding.",
        }
        resp = client.post(
            f"{API}/policies/", json=policy_payload, headers=auth_headers
        )
        assert resp.status_code == 201
        policy_id = resp.json()["id"]
        # Policy is inactive by default from create

        # Login - should not have outstanding policies (from this policy)
        resp = client.post(
            f"{API}/auth/login",
            data={
                "username": login_user.username,
                "password": "testpassword123",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        data = resp.json()
        outstanding = data.get("outstanding_policies")
        if outstanding:
            assert policy_id not in [str(p) for p in outstanding]

    def test_agree_twice_returns_error(
        self,
        client,
        db_session,
        mock_permission_allow,
        login_user,
        auth_headers,
    ):
        """Agreeing to the same policy twice returns 400."""
        # Create and activate policy
        policy_payload = {
            "name": f"Double Agree Policy {uuid.uuid4().hex[:6]}",
            "description": "Agree once only",
            "content": "Terms.",
        }
        resp = client.post(
            f"{API}/policies/", json=policy_payload, headers=auth_headers
        )
        assert resp.status_code == 201
        policy_id = resp.json()["id"]

        resp = client.put(
            f"{API}/policies/{policy_id}",
            json={"active": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # Login to get policy_required token
        resp = client.post(
            f"{API}/auth/login",
            data={
                "username": login_user.username,
                "password": "testpassword123",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        policy_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

        # Agree first time
        resp = client.post(
            f"{API}/policies/{policy_id}/actions",
            json={"agree": True},
            headers=policy_headers,
        )
        assert resp.status_code == 201

        # Agree second time -> should fail
        resp = client.post(
            f"{API}/policies/{policy_id}/actions",
            json={"agree": True},
            headers=policy_headers,
        )
        assert resp.status_code == 400


# ------------------------------------------------------------------
# Scenario B: Policy lifecycle
# ------------------------------------------------------------------


class TestPolicyLifecycle:
    """Create, activate, deactivate, delete policies."""

    def test_create_activate_deactivate(
        self, client, db_session, mock_permission_allow, auth_headers
    ):
        """Create inactive -> activate -> deactivate."""
        # Create
        payload = {
            "name": f"Lifecycle Policy {uuid.uuid4().hex[:6]}",
            "description": "Lifecycle test",
            "content": "Content here.",
        }
        resp = client.post(f"{API}/policies/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        policy_id = resp.json()["id"]
        assert resp.json()["active"] is False

        # Activate
        resp = client.put(
            f"{API}/policies/{policy_id}",
            json={"active": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["active"] is True

        # Deactivate
        resp = client.put(
            f"{API}/policies/{policy_id}",
            json={"active": False},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["active"] is False

    def test_delete_policy_removes_user_agreements(
        self,
        client,
        db_session,
        mock_permission_allow,
        login_user,
        auth_headers,
    ):
        """Deleting a policy removes associated PoliciesUser records."""
        from models import PoliciesUser

        # Create + activate policy
        payload = {
            "name": f"Delete Policy {uuid.uuid4().hex[:6]}",
            "description": "Will be deleted",
            "content": "Content.",
        }
        resp = client.post(f"{API}/policies/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        policy_id = resp.json()["id"]

        resp = client.put(
            f"{API}/policies/{policy_id}",
            json={"active": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # Login and agree
        resp = client.post(
            f"{API}/auth/login",
            data={
                "username": login_user.username,
                "password": "testpassword123",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        policy_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

        resp = client.post(
            f"{API}/policies/{policy_id}/actions",
            json={"agree": True},
            headers=policy_headers,
        )
        assert resp.status_code == 201

        # Verify agreement exists in DB
        agreement = (
            db_session.query(PoliciesUser)
            .filter(
                PoliciesUser.policy_id == uuid.UUID(policy_id),
                PoliciesUser.user_id == login_user.id,
            )
            .first()
        )
        assert agreement is not None

        # Deactivate then delete policy
        resp = client.put(
            f"{API}/policies/{policy_id}",
            json={"active": False},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        resp = client.delete(f"{API}/policies/{policy_id}", headers=auth_headers)
        assert resp.status_code == 200

        # Verify agreement was deleted
        agreement = (
            db_session.query(PoliciesUser)
            .filter(
                PoliciesUser.policy_id == uuid.UUID(policy_id),
                PoliciesUser.user_id == login_user.id,
            )
            .first()
        )
        assert agreement is None

    def test_cannot_delete_active_policy(
        self, client, db_session, mock_permission_allow, auth_headers
    ):
        """Deleting an active policy returns 422."""
        payload = {
            "name": f"Active Policy {uuid.uuid4().hex[:6]}",
            "description": "Cannot delete while active",
            "content": "Content.",
        }
        resp = client.post(f"{API}/policies/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        policy_id = resp.json()["id"]

        # Activate
        resp = client.put(
            f"{API}/policies/{policy_id}",
            json={"active": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # Try to delete -> should fail
        resp = client.delete(f"{API}/policies/{policy_id}", headers=auth_headers)
        assert resp.status_code == 422

    def test_cannot_update_content_of_active_policy(
        self, client, db_session, mock_permission_allow, auth_headers
    ):
        """Updating name/description/content of active policy returns 422."""
        payload = {
            "name": f"Locked Policy {uuid.uuid4().hex[:6]}",
            "description": "Content locked",
            "content": "Original content.",
        }
        resp = client.post(f"{API}/policies/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        policy_id = resp.json()["id"]

        # Activate
        resp = client.put(
            f"{API}/policies/{policy_id}",
            json={"active": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # Try to update content -> should fail
        resp = client.put(
            f"{API}/policies/{policy_id}",
            json={"content": "Modified content"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ------------------------------------------------------------------
# Scenario C: Auth edge cases
# ------------------------------------------------------------------


class TestAuthEdgeCases:
    """Edge cases for authentication endpoints."""

    def test_expired_token_returns_401(self, client, expired_auth_headers):
        """Request with expired token returns 401."""
        resp = client.get(f"{API}/me", headers=expired_auth_headers)
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """Request with invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid-token-string"}
        resp = client.get(f"{API}/me", headers=headers)
        assert resp.status_code == 401

    def test_login_wrong_password_returns_401(self, client, db_session, login_user):
        """Login with wrong password returns 401."""
        resp = client.post(
            f"{API}/auth/login",
            data={
                "username": login_user.username,
                "password": "wrong-password",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 401

    def test_login_inactive_user_returns_400(self, client, db_session, system_user):
        """Login with inactive user returns 400."""
        from core.auth import get_password_hash
        from models import User

        now = datetime.now(timezone.utc)
        inactive_user = User(
            id=uuid.uuid4(),
            username=f"inactive_{uuid.uuid4().hex[:6]}",
            name="Inactive User",
            email=f"inactive_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password=get_password_hash("testpassword123"),
            status="Inactive",
            locale="de_DE",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(inactive_user)
        db_session.flush()

        resp = client.post(
            f"{API}/auth/login",
            data={
                "username": inactive_user.username,
                "password": "testpassword123",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 400

    def test_system_user_login_blocked(self, client, db_session, system_user):
        """Login as system user returns 403."""
        resp = client.post(
            f"{API}/auth/login",
            data={"username": "system", "password": "anything"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 403

    def test_get_own_user(self, client, auth_headers, active_user):
        """GET /me returns own user data."""
        resp = client.get(f"{API}/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == active_user.username
        assert data["email"] == active_user.email

    def test_get_own_permissions(self, client, auth_headers, active_user):
        """GET /me/permissions returns permission list."""
        resp = client.get(f"{API}/me/permissions", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_login_returns_valid_token(self, client, db_session, login_user):
        """Login returns a token that can be used for subsequent requests."""
        # Login
        resp = client.post(
            f"{API}/auth/login",
            data={
                "username": login_user.username,
                "password": "testpassword123",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        # Use token for authenticated request
        resp = client.get(
            f"{API}/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == login_user.username
