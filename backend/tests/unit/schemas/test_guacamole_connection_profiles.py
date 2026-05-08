"""Tests for schemas/guacamole_connection_profiles.py - Protocol validation."""

import uuid

import pytest

from core.exceptions import InvalidFieldValue
from schemas.guacamole_connection_profiles import (
    GuacamoleConnectionProfileClone,
    GuacamoleConnectionProfileCreate,
    GuacamoleConnectionProfileUpdate,
)


def _make_gcp(**kwargs):
    defaults = {
        "objectId": uuid.uuid4(),
        "objectType": "VirtualMachine",
    }
    defaults.update(kwargs)
    return GuacamoleConnectionProfileCreate(**defaults)


class TestGuacamoleConnectionProfileCreate:
    def test_valid_create_defaults(self):
        gcp = _make_gcp()
        assert gcp.port == 3389
        assert gcp.protocol == "RDP"
        assert gcp.username is None
        assert gcp.password is None

    @pytest.mark.parametrize(
        "protocol",
        ["rdp", "RDP", "vnc", "VNC", "ssh", "SSH", "k8s", "K8S"],
    )
    def test_valid_protocols(self, protocol):
        gcp = _make_gcp(protocol=protocol)
        assert gcp.protocol == protocol

    def test_invalid_protocol_raises(self):
        with pytest.raises(InvalidFieldValue):
            _make_gcp(protocol="telnet")

    def test_custom_port(self):
        gcp = _make_gcp(port=5900, protocol="vnc")
        assert gcp.port == 5900

    def test_required_fields(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GuacamoleConnectionProfileCreate(protocol="rdp")


class TestGuacamoleConnectionProfileClone:
    def test_valid_clone(self):
        clone = GuacamoleConnectionProfileClone(
            objectId=uuid.uuid4(), objectType="VirtualMachine"
        )
        assert clone.port == 3389
        assert clone.protocol == "RDP"

    def test_clone_invalid_protocol_raises(self):
        with pytest.raises(InvalidFieldValue):
            GuacamoleConnectionProfileClone(
                objectId=uuid.uuid4(),
                objectType="VirtualMachine",
                protocol="ftp",
            )


class TestGuacamoleConnectionProfileUpdate:
    def test_valid_update(self):
        u = GuacamoleConnectionProfileUpdate(port=22, protocol="ssh")
        assert u.port == 22
        assert u.protocol == "ssh"

    def test_update_all_optional(self):
        u = GuacamoleConnectionProfileUpdate()
        assert u.port is None
        assert u.protocol is None
