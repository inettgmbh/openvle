"""Tests for schemas/os.py - OS schema validation."""

import uuid

from pydantic import ValidationError
import pytest

from schemas.os import OSCreate, OSUpdate, OSUpdateDocuments


class TestOSCreate:
    def test_valid_create(self):
        o = OSCreate(name="Ubuntu", key="ubuntu-22.04", version="22.04")
        assert o.name == "Ubuntu"
        assert o.key == "ubuntu-22.04"
        assert o.version == "22.04"

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            OSCreate(key="test", version="1.0")

    def test_missing_key_raises(self):
        with pytest.raises(ValidationError):
            OSCreate(name="Test", version="1.0")

    def test_missing_version_raises(self):
        with pytest.raises(ValidationError):
            OSCreate(name="Test", key="test")

    def test_optional_fields(self):
        o = OSCreate(name="Test", key="test", version="1.0")
        assert o.patch_level is None
        assert o.description is None


class TestOSUpdate:
    def test_valid_update(self):
        u = OSUpdate(name="Updated OS", version="2.0")
        assert u.name == "Updated OS"

    def test_all_optional(self):
        u = OSUpdate()
        assert u.name is None
        assert u.description is None
        assert u.version is None
        assert u.vendor is None


class TestOSUpdateDocuments:
    def test_valid_update(self):
        did = uuid.uuid4()
        u = OSUpdateDocuments(documents=[{"id": did}])
        assert len(u.documents) == 1
        assert u.documents[0].id == did

    def test_none_documents(self):
        u = OSUpdateDocuments(documents=None)
        assert u.documents is None

    def test_empty_list(self):
        u = OSUpdateDocuments(documents=[])
        assert u.documents == []
