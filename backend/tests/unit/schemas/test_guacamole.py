"""Tests for schemas/guacamole.py - Guacamole schema validation."""

import uuid

from pydantic import ValidationError
import pytest

from schemas.guacamole import GuacamoleCreate, GuacamoleUpdate


class TestGuacamoleCreate:
    def test_valid_create(self):
        g = GuacamoleCreate(
            name="My Connection",
            connection_profile=uuid.uuid4(),
            userId=uuid.uuid4(),
        )
        assert g.name == "My Connection"
        assert g.guacd_port == 4822
        assert g.guacd_encryption is True
        assert g.eventId is None

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            GuacamoleCreate(
                connection_profile=uuid.uuid4(),
                userId=uuid.uuid4(),
            )

    def test_missing_connection_profile_raises(self):
        with pytest.raises(ValidationError):
            GuacamoleCreate(
                name="Test",
                userId=uuid.uuid4(),
            )

    def test_custom_port_and_encryption(self):
        g = GuacamoleCreate(
            name="Test",
            connection_profile=uuid.uuid4(),
            userId=uuid.uuid4(),
            guacd_port=9999,
            guacd_encryption=False,
        )
        assert g.guacd_port == 9999
        assert g.guacd_encryption is False

    def test_description_optional(self):
        g = GuacamoleCreate(
            name="Test",
            connection_profile=uuid.uuid4(),
            userId=uuid.uuid4(),
        )
        assert g.description is None

    def test_description_set(self):
        g = GuacamoleCreate(
            name="Test",
            connection_profile=uuid.uuid4(),
            userId=uuid.uuid4(),
            description="A guacamole connection",
        )
        assert g.description == "A guacamole connection"


class TestGuacamoleUpdate:
    def test_valid_update(self):
        u = GuacamoleUpdate(name="Updated")
        assert u.name == "Updated"

    def test_defaults(self):
        u = GuacamoleUpdate()
        assert u.guacd_port == 4822
        assert u.guacd_encryption is True

    def test_description_optional(self):
        u = GuacamoleUpdate()
        assert u.description is None

    def test_description_set(self):
        u = GuacamoleUpdate(description="Updated description")
        assert u.description == "Updated description"
