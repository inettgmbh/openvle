"""Tests for controllers/mails_templates.py - CRUDMailTemplate operations."""

import uuid
from datetime import datetime, timezone

import pytest

from controllers.mails_templates import CRUDMailTemplate
from models import Language, MailTemplate, ObjectPermission
from schemas.mails_templates import MailTemplateCreate
from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def sample_language(db_session, system_user):
    """Return the seeded German language."""
    return db_session.query(Language).filter_by(key="de_DE").one()


class TestCRUDMailTemplateGetByName:
    def setup_method(self):
        self.crud = CRUDMailTemplate(MailTemplate)

    def test_get_by_name_found(self, db_session, system_user, sample_language):
        now = datetime.now(timezone.utc)
        tpl = MailTemplate(
            id=uuid.uuid4(),
            name="Welcome Template",
            subject="Welcome!",
            contentHTML="<p>Welcome</p>",
            contentPlain="Welcome",
            language=sample_language.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(tpl)
        db_session.flush()

        result = self.crud.get_by_name(db_session, name="Welcome Template")
        assert result is not None
        assert result.name == "Welcome Template"

    def test_get_by_name_not_found(self, db_session, system_user):
        result = self.crud.get_by_name(db_session, name="nonexistent")
        assert result is None


class TestCRUDMailTemplateCreate:
    def setup_method(self):
        self.crud = CRUDMailTemplate(MailTemplate)

    def test_create_mail_template(self, db_session, active_user, sample_language):
        request = create_mock_request(active_user)
        obj_in = MailTemplateCreate(
            name="New Template",
            subject="Hello",
            contentHTML="<p>Hello</p>",
            contentPlain="Hello",
            language=str(sample_language.id),
            protected=False,
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.name == "New Template"
        assert result.language == sample_language.id

    def test_create_creates_object_permission(
        self, db_session, active_user, sample_language
    ):
        request = create_mock_request(active_user)
        obj_in = MailTemplateCreate(
            name="ObjPerm Template",
            subject="Test",
            contentHTML="<p>Test</p>",
            contentPlain="Test",
            language=str(sample_language.id),
            protected=False,
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)

        obj_perm = (
            db_session.query(ObjectPermission)
            .filter(
                ObjectPermission.object_id == result.id,
                ObjectPermission.entity_id == active_user.id,
                ObjectPermission.permission_key == "object_full",
                ObjectPermission.object_type == "MailTemplate",
            )
            .first()
        )
        assert obj_perm is not None


class TestCRUDMailTemplateUpdate:
    def setup_method(self):
        self.crud = CRUDMailTemplate(MailTemplate)

    def test_update_mail_template(self, db_session, active_user, sample_language):
        """Update the subject of a MailTemplate."""
        request = create_mock_request(active_user)
        obj_in = MailTemplateCreate(
            name="Update Template",
            subject="Original Subject",
            contentHTML="<p>Content</p>",
            contentPlain="Content",
            language=str(sample_language.id),
            protected=False,
        )
        tpl = self.crud.create(db_session, request, obj_in=obj_in)

        updated = self.crud.update(
            tpl.id,
            db_session,
            request,
            obj_in={"subject": "Updated Subject"},
        )
        assert updated.subject == "Updated Subject"
        assert updated.name == "Update Template"


class TestCRUDMailTemplateDelete:
    def setup_method(self):
        self.crud = CRUDMailTemplate(MailTemplate)

    def test_delete_mail_template(self, db_session, active_user, sample_language):
        """Delete a MailTemplate and verify it is gone."""
        request = create_mock_request(active_user)
        obj_in = MailTemplateCreate(
            name="Delete Template",
            subject="To Delete",
            contentHTML="<p>Delete</p>",
            contentPlain="Delete",
            language=str(sample_language.id),
            protected=False,
        )
        tpl = self.crud.create(db_session, request, obj_in=obj_in)
        tpl_id = tpl.id

        self.crud.delete(db_session, tpl_id)

        fetched = db_session.get(MailTemplate, tpl_id)
        assert fetched is None


class TestCRUDMailTemplateGetMulti:
    def setup_method(self):
        self.crud = CRUDMailTemplate(MailTemplate)

    def test_get_multi_returns_all(self, db_session, active_user, sample_language):
        """Create several MailTemplates, get_multi returns all."""
        request = create_mock_request(active_user)
        for i in range(3):
            obj_in = MailTemplateCreate(
                name=f"MultiTemplate{i}",
                subject=f"Subject {i}",
                contentHTML=f"<p>Content {i}</p>",
                contentPlain=f"Content {i}",
                language=str(sample_language.id),
                protected=False,
            )
            self.crud.create(db_session, request, obj_in=obj_in)

        result = self.crud.get_multi(db_session)
        assert len(result["items"]) >= 3

    def test_get_by_name_case_sensitive(self, db_session, active_user, sample_language):
        """Verify get_by_name matches the correct case."""
        request = create_mock_request(active_user)
        obj_in = MailTemplateCreate(
            name="CaseTemplate",
            subject="Case Test",
            contentHTML="<p>Case</p>",
            contentPlain="Case",
            language=str(sample_language.id),
            protected=False,
        )
        self.crud.create(db_session, request, obj_in=obj_in)

        result = self.crud.get_by_name(db_session, name="CaseTemplate")
        assert result is not None
        assert result.name == "CaseTemplate"
