"""Tests for controllers/apps.py - CRUDApplication operations."""

import uuid
from datetime import datetime, timezone

import pytest
from controllers.apps import CRUDApplication
from core.exceptions import ObjectNotFound
from models import Application, Document, ObjectPermission, Vendor
from schemas.apps import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationUpdateDocuments,
)

from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def sample_vendor(db_session, system_user):
    """Create a sample vendor for application tests."""
    now = datetime.now(timezone.utc)
    vendor = Vendor(
        id=uuid.uuid4(),
        name="Test Vendor",
        description="A test vendor",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


class TestCRUDApplicationGetByKey:
    def setup_method(self):
        self.crud = CRUDApplication(Application)

    def test_get_by_key_found(self, db_session, active_user):
        """Seeded 'chrome' app is found by key."""
        result = self.crud.get_by_key(db_session, key="chrome")
        assert result is not None
        assert result.key == "chrome"

    def test_get_by_key_not_found(self, db_session, system_user):
        result = self.crud.get_by_key(db_session, key="nonexistent")
        assert result is None


class TestCRUDApplicationCreate:
    def setup_method(self):
        self.crud = CRUDApplication(Application)

    def test_create_application(self, db_session, active_user, sample_vendor):
        request = create_mock_request(active_user)
        obj_in = ApplicationCreate(
            name="Test App New",
            key="test_app_new",
            description="A test application",
            vendor=str(sample_vendor.id),
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.name == "Test App New"
        assert result.key == "test_app_new"
        assert result.vendor == sample_vendor.id

    def test_create_creates_object_permission(
        self, db_session, active_user, sample_vendor
    ):
        request = create_mock_request(active_user)
        obj_in = ApplicationCreate(
            name="VS Code",
            key="vscode",
            description="Editor",
            vendor=str(sample_vendor.id),
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


class TestCRUDApplicationUpdate:
    def setup_method(self):
        self.crud = CRUDApplication(Application)

    def test_update_name(self, db_session, active_user, sample_vendor):
        now = datetime.now(timezone.utc)
        app = Application(
            id=uuid.uuid4(),
            key="old_app",
            name="Old App",
            vendor=sample_vendor.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(app)
        db_session.flush()

        request = create_mock_request(active_user)
        obj_in = ApplicationUpdate(name="Updated App")
        result = self.crud.update(app.id, db_session, request, obj_in=obj_in)
        assert result.name == "Updated App"


class TestCRUDApplicationUpdateDocuments:
    def setup_method(self):
        self.crud = CRUDApplication(Application)

    def _create_app(self, db_session, user, vendor):
        now = datetime.now(timezone.utc)
        app = Application(
            id=uuid.uuid4(),
            key=f"app-{uuid.uuid4().hex[:6]}",
            name="Test App",
            vendor=vendor.id,
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db_session.add(app)
        db_session.flush()
        return app

    def _create_document(self, db_session, user, name=None):
        now = datetime.now(timezone.utc)
        doc = Document(
            id=uuid.uuid4(),
            name=name or f"doc-{uuid.uuid4().hex[:6]}.pdf",
            description="A test document",
            path=None,
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db_session.add(doc)
        db_session.flush()
        return doc

    def test_update_documents_appends(
        self, db_session, active_user, sample_vendor
    ):
        app = self._create_app(db_session, active_user, sample_vendor)
        doc = self._create_document(db_session, active_user)

        request = create_mock_request(active_user)
        obj_in = ApplicationUpdateDocuments(documents=[{"id": str(doc.id)}])
        result = self.crud.update_documents(
            app.id, db_session, request, obj_in=obj_in
        )
        assert len(result.documents) == 1
        assert result.documents[0].id == doc.id

    def test_update_documents_appends_to_existing(
        self, db_session, active_user, sample_vendor
    ):
        app = self._create_app(db_session, active_user, sample_vendor)
        doc1 = self._create_document(db_session, active_user, name="doc1.pdf")
        doc2 = self._create_document(db_session, active_user, name="doc2.pdf")

        request = create_mock_request(active_user)
        # Add first document
        obj_in1 = ApplicationUpdateDocuments(documents=[{"id": str(doc1.id)}])
        self.crud.update_documents(app.id, db_session, request, obj_in=obj_in1)
        # Append second document
        obj_in2 = ApplicationUpdateDocuments(documents=[{"id": str(doc2.id)}])
        result = self.crud.update_documents(
            app.id, db_session, request, obj_in=obj_in2
        )
        assert len(result.documents) == 2

    def test_update_documents_nonexistent_doc_raises(
        self, db_session, active_user, sample_vendor
    ):
        app = self._create_app(db_session, active_user, sample_vendor)

        request = create_mock_request(active_user)
        obj_in = ApplicationUpdateDocuments(
            documents=[{"id": str(uuid.uuid4())}]
        )
        with pytest.raises(ObjectNotFound):
            self.crud.update_documents(
                app.id, db_session, request, obj_in=obj_in
            )

    def test_update_documents_nonexistent_app_raises(
        self, db_session, active_user
    ):
        request = create_mock_request(active_user)
        obj_in = ApplicationUpdateDocuments(
            documents=[{"id": str(uuid.uuid4())}]
        )
        with pytest.raises(ObjectNotFound):
            self.crud.update_documents(
                uuid.uuid4(), db_session, request, obj_in=obj_in
            )


class TestCRUDApplicationSetDocuments:
    def setup_method(self):
        self.crud = CRUDApplication(Application)

    def _create_app(self, db_session, user, vendor):
        now = datetime.now(timezone.utc)
        app = Application(
            id=uuid.uuid4(),
            key=f"app-{uuid.uuid4().hex[:6]}",
            name="Test App",
            vendor=vendor.id,
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db_session.add(app)
        db_session.flush()
        return app

    def _create_document(self, db_session, user, name=None):
        now = datetime.now(timezone.utc)
        doc = Document(
            id=uuid.uuid4(),
            name=name or f"doc-{uuid.uuid4().hex[:6]}.pdf",
            description="A test document",
            path=None,
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db_session.add(doc)
        db_session.flush()
        return doc

    def test_set_documents_sets(self, db_session, active_user, sample_vendor):
        app = self._create_app(db_session, active_user, sample_vendor)
        doc1 = self._create_document(
            db_session, active_user, name="set-doc1.pdf"
        )
        doc2 = self._create_document(
            db_session, active_user, name="set-doc2.pdf"
        )

        request = create_mock_request(active_user)
        obj_in = ApplicationUpdateDocuments(
            documents=[{"id": str(doc1.id)}, {"id": str(doc2.id)}]
        )
        result = self.crud.set_documents(
            app.id, db_session, request, obj_in=obj_in
        )
        assert len(result.documents) == 2
        doc_ids = {d.id for d in result.documents}
        assert doc1.id in doc_ids
        assert doc2.id in doc_ids

    def test_set_documents_empty_list(
        self, db_session, active_user, sample_vendor
    ):
        app = self._create_app(db_session, active_user, sample_vendor)
        doc = self._create_document(
            db_session, active_user, name="set-empty.pdf"
        )

        request = create_mock_request(active_user)
        # Add a document first
        obj_in1 = ApplicationUpdateDocuments(documents=[{"id": str(doc.id)}])
        self.crud.set_documents(app.id, db_session, request, obj_in=obj_in1)
        assert len(app.documents) == 1

        # Set to empty
        obj_in2 = ApplicationUpdateDocuments(documents=[])
        result = self.crud.set_documents(
            app.id, db_session, request, obj_in=obj_in2
        )
        assert len(result.documents) == 0

    def test_set_documents_nonexistent_doc_raises(
        self, db_session, active_user, sample_vendor
    ):
        app = self._create_app(db_session, active_user, sample_vendor)

        request = create_mock_request(active_user)
        obj_in = ApplicationUpdateDocuments(
            documents=[{"id": str(uuid.uuid4())}]
        )
        with pytest.raises(ObjectNotFound):
            self.crud.set_documents(app.id, db_session, request, obj_in=obj_in)

    def test_set_documents_nonexistent_app_raises(
        self, db_session, active_user
    ):
        request = create_mock_request(active_user)
        obj_in = ApplicationUpdateDocuments(
            documents=[{"id": str(uuid.uuid4())}]
        )
        with pytest.raises(ObjectNotFound):
            self.crud.set_documents(
                uuid.uuid4(), db_session, request, obj_in=obj_in
            )
