"""Tests for schemas/event_status.py - EventStatus schema validation."""

import pytest
from pydantic import ValidationError
from schemas.event_status import EventStatusCreate, EventStatusUpdate


class TestEventStatusCreate:
    def test_valid_create(self):
        es = EventStatusCreate(name="Active")
        assert es.name == "Active"

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            EventStatusCreate()


class TestEventStatusUpdate:
    def test_valid_update(self):
        u = EventStatusUpdate(name="Archived")
        assert u.name == "Archived"

    def test_name_optional(self):
        u = EventStatusUpdate()
        assert u.name is None
