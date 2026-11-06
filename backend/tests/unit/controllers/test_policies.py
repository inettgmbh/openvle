"""Tests for controllers/policies.py - CRUDPolicy operations."""

import uuid
from datetime import datetime, timezone

import pytest
from controllers.policies import CRUDPolicy
from core.exceptions import (
    BadRequestError,
    InvalidStatusError,
    RelationNotFound,
)
from models import ObjectPermission, PoliciesUser, Policy
from schemas.policies import PolicyCreate, PolicyUpdate, PolicyUserAgree

from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def inactive_policy(db_session, system_user):
    """Create an inactive policy."""
    now = datetime.now(timezone.utc)
    policy = Policy(
        id=uuid.uuid4(),
        name="Test Policy",
        description="A test policy",
        content="Policy content here",
        active=False,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(policy)
    db_session.flush()
    return policy


@pytest.fixture()
def active_policy(db_session, system_user):
    """Create an active policy."""
    now = datetime.now(timezone.utc)
    policy = Policy(
        id=uuid.uuid4(),
        name="Active Policy",
        description="An active policy",
        content="Active content",
        active=True,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(policy)
    db_session.flush()
    return policy


class TestCRUDPolicyGetByName:
    def setup_method(self):
        self.crud = CRUDPolicy(Policy)

    def test_get_by_name_found(self, db_session, inactive_policy):
        result = self.crud.get_by_name(db_session, name="Test Policy")
        assert result is not None
        assert result.name == "Test Policy"

    def test_get_by_name_not_found(self, db_session, system_user):
        result = self.crud.get_by_name(db_session, name="nonexistent")
        assert result is None


class TestCRUDPolicyCreate:
    def setup_method(self):
        self.crud = CRUDPolicy(Policy)

    def test_create_policy(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = PolicyCreate(
            name="New Policy",
            description="New policy description",
            content="New policy content",
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.name == "New Policy"
        assert result.active is False  # Always inactive initially

    def test_create_creates_object_permission(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = PolicyCreate(
            name="Perm Policy",
            description="Has perm",
            content="Content",
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)

        obj_perm = (
            db_session.query(ObjectPermission)
            .filter(
                ObjectPermission.object_id == result.id,
                ObjectPermission.entity_id == active_user.id,
                ObjectPermission.permission_key == "object_full",
                ObjectPermission.object_type == "Policy",
            )
            .first()
        )
        assert obj_perm is not None


class TestCRUDPolicyUpdate:
    def setup_method(self):
        self.crud = CRUDPolicy(Policy)

    def test_update_inactive_ok(self, db_session, active_user, inactive_policy):
        request = create_mock_request(active_user)
        obj_in = PolicyUpdate(name="Updated Policy")
        result = self.crud.update(
            inactive_policy.id, db_session, request, obj_in=obj_in
        )
        assert result.name == "Updated Policy"

    def test_update_active_content_raises(
        self, db_session, active_user, active_policy
    ):
        request = create_mock_request(active_user)
        obj_in = PolicyUpdate(name="Changed Name")
        with pytest.raises(InvalidStatusError):
            self.crud.update(
                active_policy.id, db_session, request, obj_in=obj_in
            )

    def test_activate_policy(self, db_session, active_user, inactive_policy):
        request = create_mock_request(active_user)
        obj_in = PolicyUpdate(active=True)
        result = self.crud.update(
            inactive_policy.id, db_session, request, obj_in=obj_in
        )
        assert result.active is True


class TestCRUDPolicyAgreement:
    def setup_method(self):
        self.crud = CRUDPolicy(Policy)

    def test_agree_to_policy(self, db_session, active_user, active_policy):
        request = create_mock_request(active_user)
        obj_in = PolicyUserAgree(agree=True)
        result = self.crud.agree_to_policy(
            active_policy.id, db_session, request, obj_in=obj_in
        )
        assert result.user_id == active_user.id
        assert result.policy_id == active_policy.id

    def test_duplicate_agreement_raises(
        self, db_session, active_user, active_policy
    ):
        request = create_mock_request(active_user)
        obj_in = PolicyUserAgree(agree=True)
        self.crud.agree_to_policy(
            active_policy.id, db_session, request, obj_in=obj_in
        )

        with pytest.raises(BadRequestError):
            self.crud.agree_to_policy(
                active_policy.id, db_session, request, obj_in=obj_in
            )


class TestCRUDPolicyGetOutstanding:
    def setup_method(self):
        self.crud = CRUDPolicy(Policy)

    def test_returns_outstanding_policies(
        self, db_session, active_user, active_policy
    ):
        result = self.crud.get_outstanding(db_session, user_id=active_user.id)
        assert active_policy.id in result

    def test_excludes_agreed_policies(
        self, db_session, active_user, active_policy
    ):
        request = create_mock_request(active_user)
        obj_in = PolicyUserAgree(agree=True)
        self.crud.agree_to_policy(
            active_policy.id, db_session, request, obj_in=obj_in
        )

        result = self.crud.get_outstanding(db_session, user_id=active_user.id)
        assert active_policy.id not in result

    def test_excludes_inactive_policies(
        self, db_session, active_user, inactive_policy
    ):
        result = self.crud.get_outstanding(db_session, user_id=active_user.id)
        assert inactive_policy.id not in result


class TestCRUDPolicyGetPolicyUser:
    def setup_method(self):
        self.crud = CRUDPolicy(Policy)

    def test_get_policy_user_returns_relation(
        self, db_session, active_user, active_policy
    ):
        now = datetime.now(timezone.utc)
        pu = PoliciesUser(
            id=uuid.uuid4(),
            user_id=active_user.id,
            policy_id=active_policy.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(pu)
        db_session.flush()

        result = self.crud.get_policy_user(
            db_session, id=active_policy.id, user_id=active_user.id
        )
        assert result is not None
        assert result.user_id == active_user.id
        assert result.policy_id == active_policy.id

    def test_get_policy_user_raises_when_not_found(
        self, db_session, active_user, active_policy
    ):
        with pytest.raises(RelationNotFound):
            self.crud.get_policy_user(
                db_session, id=active_policy.id, user_id=active_user.id
            )

    def test_get_policy_user_raises_with_wrong_user(
        self, db_session, active_user, system_user, active_policy
    ):
        now = datetime.now(timezone.utc)
        pu = PoliciesUser(
            id=uuid.uuid4(),
            user_id=active_user.id,
            policy_id=active_policy.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(pu)
        db_session.flush()

        with pytest.raises(RelationNotFound):
            self.crud.get_policy_user(
                db_session, id=active_policy.id, user_id=system_user.id
            )


class TestCRUDPolicyDelete:
    def setup_method(self):
        self.crud = CRUDPolicy(Policy)

    def test_delete_inactive_ok(self, db_session, system_user, inactive_policy):
        result = self.crud.delete(db_session, id=inactive_policy.id)
        assert "deleted" in result["detail"]

    def test_delete_active_raises(self, db_session, system_user, active_policy):
        with pytest.raises(InvalidStatusError):
            self.crud.delete(db_session, id=active_policy.id)

    def test_delete_cascades_policy_users(
        self, db_session, system_user, active_user, inactive_policy
    ):
        """Deleting a policy removes PoliciesUser records."""
        now = datetime.now(timezone.utc)
        pu = PoliciesUser(
            id=uuid.uuid4(),
            user_id=active_user.id,
            policy_id=inactive_policy.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(pu)
        db_session.flush()

        self.crud.delete(db_session, id=inactive_policy.id)

        remaining = (
            db_session.query(PoliciesUser)
            .filter(PoliciesUser.policy_id == inactive_policy.id)
            .all()
        )
        assert len(remaining) == 0
