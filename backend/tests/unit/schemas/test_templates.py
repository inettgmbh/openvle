"""Tests for schemas/templates.py - Template schema validation."""

import uuid

import pytest
from core.exceptions import InvalidFieldValue
from schemas.templates import TemplateCreate, TemplateUpdate, TemplateUpdateApps


def _make_template(**kwargs):
    defaults = {
        "source_vm": uuid.uuid4(),
        "name": "my-template",
        "description": "A test template",
        "cpu": 4,
        "ram": 2048,
        "disk": 32,
    }
    defaults.update(kwargs)
    return TemplateCreate(**defaults)


class TestTemplateCreate:
    def test_valid_create(self):
        t = _make_template()
        assert t.name == "my-template"
        assert t.cpu == 4
        assert t.ram == 2048
        assert t.disk == 32
        assert t.prevent_delete is False

    def test_required_fields(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TemplateCreate(name="test", cpu=1, ram=1024)


class TestTemplateCreateNameValidation:
    def test_name_sanitized_spaces_replaced(self):
        t = _make_template(name="my template name")
        assert " " not in t.name
        assert t.name == "my-template-name"

    def test_name_sanitized_special_chars(self):
        t = _make_template(name="test@vm#1")
        assert t.name == "test-vm-1"

    def test_name_leading_trailing_dashes_stripped(self):
        t = _make_template(name="-test-")
        assert t.name == "test"

    def test_name_truncated_to_253(self):
        long_name = "a" * 300
        t = _make_template(name=long_name)
        assert len(t.name) <= 253


class TestTemplateCreateDescriptionValidation:
    def test_description_truncated_at_999(self):
        long_desc = "x" * 1500
        t = _make_template(description=long_desc)
        assert len(t.description) == 999

    def test_short_description_unchanged(self):
        t = _make_template(description="Short desc")
        assert t.description == "Short desc"


class TestTemplateCreateCpuValidation:
    def test_cpu_min_valid(self):
        t = _make_template(cpu=1)
        assert t.cpu == 1

    def test_cpu_max_valid(self):
        t = _make_template(cpu=24)
        assert t.cpu == 24

    def test_cpu_zero_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_template(cpu=0)

    def test_cpu_too_high_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_template(cpu=25)

    def test_cpu_negative_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_template(cpu=-1)


class TestTemplateCreateRamValidation:
    def test_ram_min_valid(self):
        t = _make_template(ram=1024)
        assert t.ram == 1024

    def test_ram_max_valid(self):
        t = _make_template(ram=268270)
        assert t.ram == 268270

    def test_ram_below_min_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_template(ram=512)

    def test_ram_above_max_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_template(ram=300000)


class TestTemplateUpdate:
    def test_valid_update(self):
        u = TemplateUpdate(name="updated", cpu=8, ram=4096)
        assert u.name == "updated"

    def test_update_cpu_invalid_raises(self):
        with pytest.raises(InvalidFieldValue):
            TemplateUpdate(cpu=0)

    def test_update_ram_invalid_raises(self):
        with pytest.raises(InvalidFieldValue):
            TemplateUpdate(ram=512)

    def test_update_name_sanitized(self):
        u = TemplateUpdate(name="my update name")
        assert u.name == "my-update-name"

    def test_update_description_truncated(self):
        u = TemplateUpdate(description="d" * 1500)
        assert len(u.description) == 999


class TestTemplateUpdateApps:
    def test_valid_update(self):
        u = TemplateUpdateApps(apps=[{"key": "chrome"}])
        assert len(u.apps) == 1
        assert u.apps[0].key == "chrome"

    def test_none_apps(self):
        u = TemplateUpdateApps(apps=None)
        assert u.apps is None

    def test_empty_list(self):
        u = TemplateUpdateApps(apps=[])
        assert u.apps == []
