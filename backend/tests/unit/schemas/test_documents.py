"""Tests for schemas/documents.py - Document schema validation."""

from pydantic import ValidationError
import pytest

from schemas.documents import DocumentCreate, DocumentUpdate, allowed_mime_types


class TestDocumentCreate:
    def test_valid_create(self):
        d = DocumentCreate(name="Manual.pdf")
        assert d.name == "Manual.pdf"
        assert d.description is None

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            DocumentCreate()

    def test_optional_description(self):
        d = DocumentCreate(name="Test", description="A document")
        assert d.description == "A document"


class TestDocumentUpdate:
    def test_valid_update(self):
        u = DocumentUpdate(description="Updated description")
        assert u.description == "Updated description"

    def test_description_optional(self):
        u = DocumentUpdate()
        assert u.description is None


class TestAllowedMimeTypes:
    def test_contains_common_types(self):
        assert "application/pdf" in allowed_mime_types
        assert "text/plain" in allowed_mime_types
        assert "image/jpeg" in allowed_mime_types
        assert "image/png" in allowed_mime_types

    def test_count(self):
        assert len(allowed_mime_types) == 20
