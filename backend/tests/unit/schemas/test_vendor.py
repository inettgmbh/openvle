"""Tests for schemas/vendor.py - Vendor schema validation."""

import pytest
from core.exceptions import FieldValueTooLong
from pydantic import ValidationError
from schemas.vendor import VendorCreate, VendorUpdate


class TestVendorCreate:
    def test_valid_create(self):
        v = VendorCreate(name="Microsoft")
        assert v.name == "Microsoft"
        assert v.description is None

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            VendorCreate()

    def test_with_description(self):
        v = VendorCreate(name="Apple", description="Tech company")
        assert v.description == "Tech company"


class TestVendorUpdate:
    def test_valid_update(self):
        u = VendorUpdate(name="Updated Vendor")
        assert u.name == "Updated Vendor"

    def test_all_optional(self):
        u = VendorUpdate()
        assert u.name is None
        assert u.description is None


class TestVendorColumnLengthEnforcement:
    # name: String(100), description: String(1000)

    def test_name_at_limit_create(self):
        VendorCreate(name="a" * 100)

    def test_name_exceeds_limit_create(self):
        with pytest.raises(FieldValueTooLong):
            VendorCreate(name="a" * 101)

    def test_description_at_limit_create(self):
        VendorCreate(name="Vendor", description="a" * 1000)

    def test_description_exceeds_limit_create(self):
        with pytest.raises(FieldValueTooLong):
            VendorCreate(name="Vendor", description="a" * 1001)

    def test_name_at_limit_update(self):
        VendorUpdate(name="a" * 100)

    def test_name_exceeds_limit_update(self):
        with pytest.raises(FieldValueTooLong):
            VendorUpdate(name="a" * 101)

    def test_description_at_limit_update(self):
        VendorUpdate(description="a" * 1000)

    def test_description_exceeds_limit_update(self):
        with pytest.raises(FieldValueTooLong):
            VendorUpdate(description="a" * 1001)
