"""Tests for schemas/apps.py - Application schema validation."""

import uuid

import pytest
from pydantic import ValidationError
from schemas.apps import (
    ApplicationCreate,
    ApplicationNested,
    ApplicationUpdate,
    ApplicationUpdateDocuments,
)


class TestApplicationCreate:
    def test_valid_create(self):
        a = ApplicationCreate(name="VS Code", key="vscode")
        assert a.name == "VS Code"
        assert a.key == "vscode"

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            ApplicationCreate(key="test")

    def test_missing_key_raises(self):
        with pytest.raises(ValidationError):
            ApplicationCreate(name="Test")

    def test_optional_fields(self):
        a = ApplicationCreate(name="Test", key="test")
        assert a.patch_level is None
        assert a.description is None


class TestApplicationUpdate:
    def test_valid_update(self):
        u = ApplicationUpdate(name="New Name")
        assert u.name == "New Name"

    def test_all_optional(self):
        u = ApplicationUpdate()
        assert u.name is None
        assert u.description is None
        assert u.vendor is None


class TestApplicationNested:
    def test_valid_nested(self):
        n = ApplicationNested(key="chrome")
        assert n.key == "chrome"


class TestApplicationUpdateDocuments:
    def test_valid_update(self):
        did = uuid.uuid4()
        u = ApplicationUpdateDocuments(documents=[{"id": did}])
        assert len(u.documents) == 1
        assert u.documents[0].id == did

    def test_none_documents(self):
        u = ApplicationUpdateDocuments(documents=None)
        assert u.documents is None

    def test_empty_list(self):
        u = ApplicationUpdateDocuments(documents=[])
        assert u.documents == []
