"""Tests for schemas/events_user.py - EventsUser schema validation."""

import uuid

from pydantic import ValidationError
import pytest

from schemas.events_user import EventsUserCreate


class TestEventsUserCreate:
    def test_valid_create(self):
        eu = EventsUserCreate(
            user_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
        )
        assert eu.user_id is not None
        assert eu.role_id is not None

    def test_missing_user_id_raises(self):
        with pytest.raises(ValidationError):
            EventsUserCreate(role_id=uuid.uuid4())

    def test_missing_role_id_raises(self):
        with pytest.raises(ValidationError):
            EventsUserCreate(user_id=uuid.uuid4())
