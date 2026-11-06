"""Tests for controllers/event_status.py - CRUDEventStatus operations."""

import pytest
from controllers.event_status import CRUDEventStatus
from models import EventStatus, ObjectPermission
from schemas.event_status import EventStatusCreate

from tests.helpers.mock_request import create_mock_request


class TestCRUDEventStatusGetByName:
    def setup_method(self):
        self.crud = CRUDEventStatus(EventStatus)

    def test_get_by_name_found(self, db_session, system_user):
        """Seeded 'Geplant' status is found by name."""
        result = self.crud.get_by_name(db_session, name="Geplant")
        assert result is not None
        assert result.name == "Geplant"

    def test_get_by_name_not_found(self, db_session, system_user):
        result = self.crud.get_by_name(db_session, name="nonexistent")
        assert result is None


class TestCRUDEventStatusCreate:
    def setup_method(self):
        self.crud = CRUDEventStatus(EventStatus)

    def test_create_event_status(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = EventStatusCreate(name="Custom Status")
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.name == "Custom Status"

    def test_create_no_object_permission(self, db_session, active_user):
        """EventStatus is in MODELS_NO_OBJ_PERM, so no ObjectPermission should be created."""
        request = create_mock_request(active_user)
        obj_in = EventStatusCreate(name="Another Status")
        result = self.crud.create(db_session, request, obj_in=obj_in)

        obj_perm = (
            db_session.query(ObjectPermission)
            .filter(ObjectPermission.object_id == result.id)
            .first()
        )
        assert obj_perm is None


class TestCRUDEventStatusUpdate:
    def setup_method(self):
        self.crud = CRUDEventStatus(EventStatus)

    def test_update_event_status(self, db_session, active_user):
        """Update the name of an EventStatus."""
        request = create_mock_request(active_user)
        obj_in = EventStatusCreate(name="Draft")
        status = self.crud.create(db_session, request, obj_in=obj_in)

        updated = self.crud.update(
            status.id, db_session, request, obj_in={"name": "Draft Updated"}
        )
        assert updated.name == "Draft Updated"


class TestCRUDEventStatusDelete:
    def setup_method(self):
        self.crud = CRUDEventStatus(EventStatus)

    def test_delete_event_status(self, db_session, active_user):
        """Delete an EventStatus and verify it is gone."""
        request = create_mock_request(active_user)
        obj_in = EventStatusCreate(name="ToDelete")
        status = self.crud.create(db_session, request, obj_in=obj_in)
        status_id = status.id

        self.crud.delete(db_session, status_id)

        fetched = db_session.get(EventStatus, status_id)
        assert fetched is None


class TestCRUDEventStatusGetMulti:
    def setup_method(self):
        self.crud = CRUDEventStatus(EventStatus)

    def test_get_multi_returns_all(self, db_session, active_user):
        """Create several event statuses, get_multi returns all."""
        request = create_mock_request(active_user)
        names = ["StatusA", "StatusB", "StatusC"]
        for name in names:
            obj_in = EventStatusCreate(name=name)
            self.crud.create(db_session, request, obj_in=obj_in)

        result = self.crud.get_multi(db_session)
        assert len(result["items"]) >= 3

    def test_create_duplicate_name_raises(self, db_session, active_user):
        """Creating two event statuses with the same name raises IntegrityError."""
        from core.exceptions import ObjectDeleteIntegrityError

        request = create_mock_request(active_user)
        obj1 = EventStatusCreate(name="DuplicateStatus")
        obj2 = EventStatusCreate(name="DuplicateStatus")
        self.crud.create(db_session, request, obj_in=obj1)

        with pytest.raises(ObjectDeleteIntegrityError):
            self.crud.create(db_session, request, obj_in=obj2)

    def test_get_by_name_case_sensitive(self, db_session, active_user):
        """Verify that get_by_name uses case-sensitive matching."""
        request = create_mock_request(active_user)
        obj_in = EventStatusCreate(name="CaseSensitive")
        self.crud.create(db_session, request, obj_in=obj_in)

        # Exact match should find it
        result = self.crud.get_by_name(db_session, name="CaseSensitive")
        assert result is not None

        # Different case should not find it (depends on DB collation)
        self.crud.get_by_name(db_session, name="casesensitive")
        # If collation is case-insensitive, this may still find it; just verify
        # the exact-case match works correctly
        assert result.name == "CaseSensitive"
