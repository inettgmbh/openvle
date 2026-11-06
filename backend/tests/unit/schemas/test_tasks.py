"""Tests for schemas/tasks.py - Task schema validation."""

import uuid

import pytest
from pydantic import ValidationError
from schemas.tasks import TaskCreate, TaskStatus


class TestTaskStatus:
    def test_status_values(self):
        expected = {"queued", "processing", "failed", "success"}
        assert {s.value for s in TaskStatus} == expected


class TestTaskCreate:
    def test_valid_create(self):
        t = TaskCreate(name="Start Event")
        assert t.name == "Start Event"
        assert t.status == "queued"
        assert t.event_id is None

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            TaskCreate()

    def test_with_event_id(self):
        eid = uuid.uuid4()
        t = TaskCreate(name="Test", event_id=eid)
        assert t.event_id == eid

    def test_custom_status(self):
        t = TaskCreate(name="Test", status="processing")
        assert t.status == "processing"

    def test_description_optional(self):
        t = TaskCreate(name="Test")
        assert t.description is None

    def test_description_set(self):
        t = TaskCreate(name="Test", description="Task notes here")
        assert t.description == "Task notes here"
