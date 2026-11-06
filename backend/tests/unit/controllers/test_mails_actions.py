"""Tests for controllers/mails_actions.py - CRUDMailAction operations."""

import uuid
from datetime import datetime, timezone

import pytest
from controllers.mails_actions import CRUDMailAction
from models import MailAction, ObjectPermission
from schemas.mails_actions import MailActionCreate

from tests.helpers.mock_request import create_mock_request


class TestCRUDMailActionGetBySlug:
    def setup_method(self):
        self.crud = CRUDMailAction(MailAction)

    def test_get_by_slug_found(self, db_session, system_user):
        now = datetime.now(timezone.utc)
        action = MailAction(
            id=uuid.uuid4(),
            name="Password Reset",
            description="Send a password reset mail",
            slug="password_reset",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(action)
        db_session.flush()

        result = self.crud.get_by_slug(db_session, slug="password_reset")
        assert result is not None
        assert result.slug == "password_reset"
        assert result.name == "Password Reset"

    def test_get_by_slug_not_found(self, db_session, system_user):
        result = self.crud.get_by_slug(db_session, slug="nonexistent")
        assert result is None


class TestCRUDMailActionCreate:
    def setup_method(self):
        self.crud = CRUDMailAction(MailAction)

    def test_create_mail_action(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = MailActionCreate(
            name="Welcome",
            description="Welcome email action",
            slug="welcome",
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.name == "Welcome"
        assert result.slug == "welcome"

    def test_create_no_object_permission(self, db_session, active_user):
        """MailAction is NOT in MODELS_NO_OBJ_PERM, so ObjectPermission should be created."""
        request = create_mock_request(active_user)
        obj_in = MailActionCreate(
            name="Verify Email",
            description="Email verification action",
            slug="verify_email",
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)

        obj_perm = (
            db_session.query(ObjectPermission)
            .filter(
                ObjectPermission.object_id == result.id,
                ObjectPermission.entity_id == active_user.id,
                ObjectPermission.permission_key == "object_full",
            )
            .first()
        )
        assert obj_perm is not None


class TestCRUDMailActionUpdate:
    def setup_method(self):
        self.crud = CRUDMailAction(MailAction)

    def test_update_mail_action(self, db_session, active_user):
        """Update name and slug on a MailAction."""
        request = create_mock_request(active_user)
        obj_in = MailActionCreate(
            name="Original Action",
            description="Original desc",
            slug="original_action",
        )
        action = self.crud.create(db_session, request, obj_in=obj_in)

        updated = self.crud.update(
            action.id,
            db_session,
            request,
            obj_in={"name": "Updated Action", "slug": "updated_action"},
        )
        assert updated.name == "Updated Action"
        assert updated.slug == "updated_action"


class TestCRUDMailActionDelete:
    def setup_method(self):
        self.crud = CRUDMailAction(MailAction)

    def test_delete_mail_action(self, db_session, active_user):
        """Delete a MailAction and verify it is gone."""
        request = create_mock_request(active_user)
        obj_in = MailActionCreate(
            name="Delete Action",
            description="Will be deleted",
            slug="delete_action",
        )
        action = self.crud.create(db_session, request, obj_in=obj_in)
        action_id = action.id

        self.crud.delete(db_session, action_id)

        fetched = db_session.get(MailAction, action_id)
        assert fetched is None


class TestCRUDMailActionGetMulti:
    def setup_method(self):
        self.crud = CRUDMailAction(MailAction)

    def test_get_multi_returns_all(self, db_session, active_user):
        """Create several MailActions, get_multi returns all."""
        request = create_mock_request(active_user)
        for i in range(3):
            obj_in = MailActionCreate(
                name=f"Action{i}",
                description=f"Desc {i}",
                slug=f"action_{i}",
            )
            self.crud.create(db_session, request, obj_in=obj_in)

        result = self.crud.get_multi(db_session)
        assert len(result["items"]) >= 3

    def test_create_duplicate_slug_raises(self, db_session, active_user):
        """Creating two MailActions with the same slug raises IntegrityError (unique constraint)."""
        from core.exceptions import ObjectDeleteIntegrityError

        request = create_mock_request(active_user)
        obj_in1 = MailActionCreate(
            name="DupSlug Action 0",
            description="Dup slug test",
            slug="duplicate_slug",
        )
        self.crud.create(db_session, request, obj_in=obj_in1)

        obj_in2 = MailActionCreate(
            name="DupSlug Action 1",
            description="Dup slug test",
            slug="duplicate_slug",
        )
        with pytest.raises(ObjectDeleteIntegrityError):
            self.crud.create(db_session, request, obj_in=obj_in2)
