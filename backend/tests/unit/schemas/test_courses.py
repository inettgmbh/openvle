"""Tests for schemas/courses.py - Course schema validation."""

import uuid

from pydantic import ValidationError
import pytest

from schemas.courses import CourseCreate, CourseUpdate, CourseUpdateTemplate


class TestCourseCreate:
    def test_valid_create(self):
        c = CourseCreate(name="Python 101", description="Intro to Python")
        assert c.name == "Python 101"
        assert c.description == "Intro to Python"
        assert c.guacamole is False

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            CourseCreate()

    def test_optional_description(self):
        c = CourseCreate(name="Test")
        assert c.description is None

    def test_guacamole_default_false(self):
        c = CourseCreate(name="Test")
        assert c.guacamole is False

    def test_guacamole_true(self):
        c = CourseCreate(name="Test", guacamole=True)
        assert c.guacamole is True


class TestCourseUpdate:
    def test_valid_update(self):
        u = CourseUpdate(name="Updated Name")
        assert u.name == "Updated Name"

    def test_all_optional(self):
        u = CourseUpdate()
        assert u.name is None
        assert u.description is None


class TestCourseUpdateTemplate:
    def test_valid_update(self):
        tid = uuid.uuid4()
        u = CourseUpdateTemplate(templates=[{"id": tid}])
        assert len(u.templates) == 1
        assert u.templates[0].id == tid

    def test_none_templates(self):
        u = CourseUpdateTemplate(templates=None)
        assert u.templates is None

    def test_empty_list(self):
        u = CourseUpdateTemplate(templates=[])
        assert u.templates == []
