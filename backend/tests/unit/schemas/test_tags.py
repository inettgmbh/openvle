"""Tests for schemas/tags.py - Tag schema validation."""

import uuid

import pytest
from core.exceptions import InvalidFieldValue
from schemas.tags import TagCreate


def _make_tag(**kwargs):
    defaults = {
        "key": "my-tag",
        "value": "some-value",
        "objectId": uuid.uuid4(),
        "objectType": "Course",
    }
    defaults.update(kwargs)
    return TagCreate(**defaults)


class TestTagCreate:
    def test_valid_create(self):
        tag = _make_tag()
        assert tag.key == "my-tag"
        assert tag.value == "some-value"

    def test_required_fields(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TagCreate(key="test")

    def test_description_optional(self):
        tag = _make_tag()
        assert tag.description is None

    def test_description_set(self):
        tag = _make_tag(description="A helpful label")
        assert tag.description == "A helpful label"


class TestTagKeyValidation:
    @pytest.mark.parametrize(
        "key",
        ["my-tag", "abc123", "a", "0", "abc-def-ghi", "123"],
    )
    def test_valid_keys(self, key):
        tag = _make_tag(key=key)
        assert tag.key == key

    def test_starts_with_dash_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_tag(key="-invalid")

    def test_ends_with_dash_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_tag(key="invalid-")

    def test_uppercase_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_tag(key="UPPER")

    def test_special_chars_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_tag(key="hello@world")

    def test_spaces_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_tag(key="hello world")

    def test_empty_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_tag(key="")


class TestTagValueValidation:
    @pytest.mark.parametrize(
        "value",
        ["my-value", "abc123", "a", "0"],
    )
    def test_valid_values(self, value):
        tag = _make_tag(value=value)
        assert tag.value == value

    def test_value_starts_with_dash_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_tag(value="-bad")

    def test_value_uppercase_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_tag(value="BAD")
