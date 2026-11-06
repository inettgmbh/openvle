"""Tests for controllers/documents.py - CRUDDocument operations."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from controllers.documents import CRUDDocument
from core.exceptions import (
    BadRequestError,
    ModelAssociationNotFound,
    ModelNotFound,
    ObjectNotFound,
)
from models import Application, Changelog, Document, ObjectPermission, Vendor

from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def sample_vendor_doc(db_session, system_user):
    now = datetime.now(timezone.utc)
    vendor = Vendor(
        id=uuid.uuid4(),
        name="Doc Vendor",
        description="Vendor for doc tests",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


@pytest.fixture()
def sample_app_doc(db_session, system_user, sample_vendor_doc):
    now = datetime.now(timezone.utc)
    app = Application(
        id=uuid.uuid4(),
        key="doc-app",
        name="Doc App",
        vendor=sample_vendor_doc.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(app)
    db_session.flush()
    return app


@pytest.fixture()
def sample_document(db_session, active_user):
    now = datetime.now(timezone.utc)
    doc = Document(
        id=uuid.uuid4(),
        name="test-doc.pdf",
        description="A test document",
        path=None,
        createdAt=now,
        updatedAt=now,
        createdById=active_user.id,
        updatedById=active_user.id,
    )
    db_session.add(doc)
    db_session.flush()
    return doc


@pytest.fixture()
def sample_document_with_path(db_session, active_user):
    now = datetime.now(timezone.utc)
    doc = Document(
        id=uuid.uuid4(),
        name="existing-doc.pdf",
        description="Has a file already",
        path="./tmp/existing-doc.pdf",
        createdAt=now,
        updatedAt=now,
        createdById=active_user.id,
        updatedById=active_user.id,
    )
    db_session.add(doc)
    db_session.flush()
    return doc


class TestGetByName:
    def setup_method(self):
        self.crud = CRUDDocument(Document)

    def test_get_by_name_found(self, db_session, sample_document):
        result = self.crud.get_by_name(db_session, name="test-doc.pdf")
        assert result is not None
        assert result.name == "test-doc.pdf"

    def test_get_by_name_not_found(self, db_session, system_user):
        result = self.crud.get_by_name(db_session, name="nonexistent")
        assert result is None


class TestUpload:
    def setup_method(self):
        self.crud = CRUDDocument(Document)

    @patch("controllers.documents.os.path.exists", return_value=False)
    @patch("builtins.open", new_callable=MagicMock)
    def test_upload_valid_file(
        self, mock_open, mock_exists, db_session, active_user, sample_document
    ):
        request = create_mock_request(active_user)
        mock_file = MagicMock()
        mock_file.content_type = "application/pdf"
        mock_file.filename = "upload.pdf"
        mock_file.file.read.return_value = b"fake-pdf-content"

        result = self.crud.upload(
            sample_document.id, db_session, request, file_in=mock_file
        )
        assert result.path is not None
        assert result.path.endswith(".pdf")

    def test_upload_already_has_file_raises(
        self, db_session, active_user, sample_document_with_path
    ):
        request = create_mock_request(active_user)
        mock_file = MagicMock()
        mock_file.content_type = "application/pdf"
        mock_file.filename = "upload.pdf"

        with pytest.raises(BadRequestError):
            self.crud.upload(
                sample_document_with_path.id,
                db_session,
                request,
                file_in=mock_file,
            )

    def test_upload_wrong_creator_raises(
        self, db_session, system_user, sample_document
    ):
        """Only the creator of the document can upload."""
        request = create_mock_request(system_user)
        mock_file = MagicMock()
        mock_file.content_type = "application/pdf"

        with pytest.raises(BadRequestError):
            self.crud.upload(
                sample_document.id, db_session, request, file_in=mock_file
            )


class TestDelete:
    def setup_method(self):
        self.crud = CRUDDocument(Document)

    @patch("controllers.documents.os.path.exists", return_value=False)
    def test_delete_document(
        self, mock_exists, db_session, active_user, sample_document
    ):
        result = self.crud.delete(db_session, id=sample_document.id)
        assert "deleted" in result["detail"]

    @patch("controllers.documents.os.path.exists", return_value=False)
    def test_delete_cascades_changelogs(
        self, mock_exists, db_session, active_user, sample_document
    ):
        cl = Changelog(
            id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            valueOld="old",
            valueNew="new",
            object="Document",
            objectId=sample_document.id,
            userId=active_user.id,
        )
        db_session.add(cl)
        db_session.flush()

        self.crud.delete(db_session, id=sample_document.id)

        remaining = (
            db_session.query(Changelog)
            .filter(Changelog.objectId == sample_document.id)
            .all()
        )
        assert len(remaining) == 0

    @patch("controllers.documents.os.path.exists", return_value=False)
    def test_delete_cascades_object_permissions(
        self, mock_exists, db_session, active_user, sample_document
    ):
        now = datetime.now(timezone.utc)
        perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Document",
            object_id=sample_document.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(perm)
        db_session.flush()

        self.crud.delete(db_session, id=sample_document.id)

        remaining = (
            db_session.query(ObjectPermission)
            .filter(ObjectPermission.object_id == sample_document.id)
            .all()
        )
        assert len(remaining) == 0


class TestGetMultiForObject:
    def setup_method(self):
        self.crud = CRUDDocument(Document)

    def test_invalid_object_type_raises(self, db_session, system_user):
        with pytest.raises(ModelAssociationNotFound):
            self.crud.get_multi_for_object(
                object_type="Vendor",
                object_id=uuid.uuid4(),
                db=db_session,
            )

    def test_nonexistent_model_raises(self, db_session, system_user):
        with pytest.raises(ModelNotFound):
            self.crud.get_multi_for_object(
                object_type="FakeModel",
                object_id=uuid.uuid4(),
                db=db_session,
            )


class TestGetMultiForObjectAuth:
    def setup_method(self):
        self.crud = CRUDDocument(Document)

    def _create_app_with_vendor(self, db_session, user):
        now = datetime.now(timezone.utc)
        vendor = Vendor(
            id=uuid.uuid4(),
            name=f"Vendor-{uuid.uuid4().hex[:6]}",
            description="Test vendor",
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db_session.add(vendor)
        db_session.flush()

        app = Application(
            id=uuid.uuid4(),
            key=f"app-{uuid.uuid4().hex[:6]}",
            name="Auth App",
            vendor=vendor.id,
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db_session.add(app)
        db_session.flush()
        return app

    def _create_document_for_app(self, db_session, user, app, name=None):
        now = datetime.now(timezone.utc)
        doc = Document(
            id=uuid.uuid4(),
            name=name or f"authdoc-{uuid.uuid4().hex[:6]}.pdf",
            description="Auth test document",
            path=None,
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db_session.add(doc)
        db_session.flush()
        app.documents.append(doc)
        db_session.flush()
        return doc

    def _create_object_permission(self, db_session, user, doc):
        now = datetime.now(timezone.utc)
        perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Document",
            object_id=doc.id,
            entity_id=user.id,
            entity_type="User",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=user.id,
            updatedById=user.id,
        )
        db_session.add(perm)
        db_session.flush()
        return perm

    def test_invalid_object_type_raises(self, db_session, active_user):
        request = create_mock_request(active_user)
        with pytest.raises(ModelAssociationNotFound):
            self.crud.get_multi_for_object_auth(
                request=request,
                object_type="Vendor",
                object_id=uuid.uuid4(),
                db=db_session,
            )

    def test_nonexistent_model_raises(self, db_session, active_user):
        request = create_mock_request(active_user)
        with pytest.raises(ModelNotFound):
            self.crud.get_multi_for_object_auth(
                request=request,
                object_type="FakeModel",
                object_id=uuid.uuid4(),
                db=db_session,
            )

    def test_nonexistent_application_raises(self, db_session, active_user):
        request = create_mock_request(active_user)
        with pytest.raises(ObjectNotFound):
            self.crud.get_multi_for_object_auth(
                request=request,
                object_type="Application",
                object_id=uuid.uuid4(),
                db=db_session,
            )

    def test_nonexistent_os_raises(self, db_session, active_user):
        request = create_mock_request(active_user)
        with pytest.raises(ObjectNotFound):
            self.crud.get_multi_for_object_auth(
                request=request,
                object_type="OS",
                object_id=uuid.uuid4(),
                db=db_session,
            )

    def test_returns_permitted_documents_for_application(
        self, db_session, active_user
    ):
        app = self._create_app_with_vendor(db_session, active_user)
        doc = self._create_document_for_app(db_session, active_user, app)
        self._create_object_permission(db_session, active_user, doc)

        request = create_mock_request(active_user)
        result = self.crud.get_multi_for_object_auth(
            request=request,
            object_type="Application",
            object_id=app.id,
            db=db_session,
        )
        assert len(result["items"]) == 1
        assert result["items"][0].id == doc.id

    def test_filters_out_non_permitted_documents(
        self, db_session, active_user, system_user
    ):
        """User without permission should not see the document."""
        app = self._create_app_with_vendor(db_session, system_user)
        self._create_document_for_app(
            db_session, system_user, app, name="no-perm-doc.pdf"
        )
        # No ObjectPermission created for active_user

        request = create_mock_request(active_user)
        result = self.crud.get_multi_for_object_auth(
            request=request,
            object_type="Application",
            object_id=app.id,
            db=db_session,
        )
        assert len(result["items"]) == 0
