"""Tests for schemas/sub_tasks.py - SubTask schema validation."""

import uuid

import pytest
from pydantic import ValidationError
from schemas.sub_tasks import SubTaskCreate, SubTaskStatus, SubTaskUpdate


class TestSubTaskStatus:
    def test_status_values(self):
        expected = {"queued", "processing", "failed", "success"}
        assert {s.value for s in SubTaskStatus} == expected


class TestSubTaskCreate:
    def test_valid_create(self):
        st = SubTaskCreate(
            name="Clone VM",
            object_type="VirtualMachine",
            action="clone",
            parent_task=uuid.uuid4(),
        )
        assert st.name == "Clone VM"
        assert st.status == "queued"
        assert st.attempt == 0
        assert st.object_id is None
        assert st.job_id is None

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            SubTaskCreate(
                object_type="VirtualMachine",
                action="clone",
                parent_task=uuid.uuid4(),
            )

    def test_missing_parent_task_raises(self):
        with pytest.raises(ValidationError):
            SubTaskCreate(
                name="Test",
                object_type="VirtualMachine",
                action="clone",
            )

    def test_description_optional(self):
        st = SubTaskCreate(
            name="Clone VM",
            object_type="VirtualMachine",
            action="clone",
            parent_task=uuid.uuid4(),
        )
        assert st.description is None

    def test_description_set(self):
        st = SubTaskCreate(
            name="Clone VM",
            object_type="VirtualMachine",
            action="clone",
            parent_task=uuid.uuid4(),
            description="Cloning step",
        )
        assert st.description == "Cloning step"


class TestSubTaskUpdate:
    def test_valid_update(self):
        u = SubTaskUpdate(status=SubTaskStatus.success, response_code=200)
        assert u.status == SubTaskStatus.success
        assert u.response_code == 200

    def test_all_optional(self):
        u = SubTaskUpdate()
        assert u.status is None
        assert u.job_id is None
        assert u.response_code is None

    def test_description_optional(self):
        u = SubTaskUpdate()
        assert u.description is None

    def test_description_set(self):
        u = SubTaskUpdate(description="Updated notes")
        assert u.description == "Updated notes"
