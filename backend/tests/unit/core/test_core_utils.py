"""Tests for core/core_utils.py - Utility functions."""

import uuid
from datetime import datetime, timezone

import pytest

from core.core_utils import (
    convert_to_slug,
    db_save,
    get_system_user,
    request_user_validation,
    sanitize_dns_name,
    vm_ip_in_subnet,
)
from models import Role


class TestDbSave:
    """Tests for db_save() - generic commit helper."""

    def test_saves_new_object(self, db_session, system_user):
        """Should persist a new object to the database."""
        now = datetime.now(timezone.utc)
        role = Role(
            id=uuid.uuid4(),
            name="test_db_save",
            key="test_db_save",
            protected=False,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(role)
        db_session.flush()

        role.name = "updated_db_save"
        result = db_save(db_session, role)
        assert result is not None
        assert result.name == "updated_db_save"

    def test_returns_refreshed_object(self, db_session, system_user):
        """Returned object should be refreshed from DB."""
        now = datetime.now(timezone.utc)
        role = Role(
            id=uuid.uuid4(),
            name="refresh_test",
            key="refresh_test_key",
            protected=False,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(role)
        db_session.flush()

        result = db_save(db_session, role)
        fetched = db_session.get(Role, result.id)
        assert fetched is not None
        assert fetched.name == "refresh_test"


class TestConvertToSlug:
    @pytest.mark.parametrize(
        "input_name,expected",
        [
            ("Hello World", "hello-world"),
            ("UPPER CASE", "upper-case"),
            ("Ärger mit Übung", "aerger-mit-uebung"),
            ("Große Straße", "grosse-strasse"),
            ("hello", "hello"),
            ("a--b", "a-b"),
            ("special!@#chars", "special-chars"),
            ("  leading trailing  ", "leading-trailing"),
            ("123 Numbers", "123-numbers"),
        ],
    )
    def test_slug_conversion(self, input_name, expected):
        assert convert_to_slug(input_name) == expected

    def test_max_length_truncation(self):
        long_name = "a" * 200
        result = convert_to_slug(long_name, max_length=50)
        assert len(result) <= 50

    def test_custom_split_char(self):
        result = convert_to_slug("Hello World", split_char="_")
        assert result == "hello_world"


class TestSanitizeDnsName:
    def test_basic_name(self):
        assert sanitize_dns_name("myhost") == "myhost"

    def test_special_chars_replaced(self):
        result = sanitize_dns_name("my host!")
        assert " " not in result
        assert "!" not in result

    def test_leading_trailing_dashes_stripped(self):
        result = sanitize_dns_name("-myhost-")
        assert not result.startswith("-")
        assert not result.endswith("-")

    def test_label_max_63_chars(self):
        long_label = "a" * 100
        result = sanitize_dns_name(long_label)
        for label in result.split("."):
            assert len(label) <= 63

    def test_total_max_253_chars(self):
        long_name = ("a" * 60 + ".") * 10
        result = sanitize_dns_name(long_name)
        assert len(result) <= 253

    def test_preserves_dots(self):
        result = sanitize_dns_name("host.example.com")
        assert result == "host.example.com"

    def test_empty_labels_removed(self):
        result = sanitize_dns_name("host..example")
        assert ".." not in result


class TestVmIpInSubnet:
    """Test with pve_vm_subnet=10.0.0.0/24 from test env."""

    def test_ip_in_subnet(self):
        interfaces = [{"ip-addresses": [{"ip-address": "10.0.0.50"}]}]
        assert vm_ip_in_subnet(interfaces) == "10.0.0.50"

    def test_ip_not_in_subnet(self):
        interfaces = [{"ip-addresses": [{"ip-address": "192.168.1.100"}]}]
        assert vm_ip_in_subnet(interfaces) is False

    def test_empty_interfaces(self):
        assert vm_ip_in_subnet([]) is False

    def test_interface_without_ip_addresses(self):
        interfaces = [{"name": "lo"}]
        assert vm_ip_in_subnet(interfaces) is False

    def test_interface_missing_ip_address_field(self):
        interfaces = [
            {
                "ip-addresses": [
                    {"ip-address-type": "ipv4"}  # Missing "ip-address"
                ]
            }
        ]
        assert vm_ip_in_subnet(interfaces) is False

    def test_multiple_interfaces_finds_correct_one(self):
        interfaces = [
            {"ip-addresses": [{"ip-address": "192.168.1.1"}]},
            {"ip-addresses": [{"ip-address": "10.0.0.99"}]},
        ]
        assert vm_ip_in_subnet(interfaces) == "10.0.0.99"


class TestGetSystemUser:
    def test_returns_system_user_from_db(self, db_session, system_user):
        result = get_system_user(db=db_session)
        assert result is not None
        assert result.username == "system"
        assert result.id == system_user.id

    def test_returns_system_user_without_fixture(self, db_session):
        """System user exists from seed data even without fixture."""
        result = get_system_user(db=db_session)
        assert result is not None
        assert result.username == "system"


class TestRequestUserValidation:
    def test_returns_request_user_id(self, db_session, mock_request, active_user):
        result = request_user_validation(db_session, mock_request)
        assert result == active_user.id

    def test_falls_back_to_system_user(self, db_session, system_user):
        result = request_user_validation(db_session, request=None)
        assert result == system_user.id
