"""Tests for core/auth_ldap.py - LDAP authentication."""

import ssl
from unittest.mock import MagicMock

import pytest
from core.exceptions import LdapConnectionError

from tests.helpers.mock_ldap import MockLDAPConnection


class TestLdapConnect:
    def test_successful_bind(self, monkeypatch):
        """Successful bind returns the connection object."""
        mock_conn = MockLDAPConnection()
        mock_conn.bind = MagicMock(return_value=True)
        mock_conn.start_tls = MagicMock()

        monkeypatch.setattr(
            "core.auth_ldap.Connection",
            lambda *args, **kwargs: mock_conn,
        )
        monkeypatch.setattr("core.auth_ldap.Server", MagicMock())

        from core.auth_ldap import ldap_connect

        result = ldap_connect("testuser", "testpass")
        assert result is mock_conn
        mock_conn.bind.assert_called_once()

    def test_failed_bind_raises_ldap_error(self, monkeypatch):
        """bind() returns False -> raises LdapConnectionError (caught by generic except)."""
        mock_conn = MockLDAPConnection()
        mock_conn.bind = MagicMock(return_value=False)
        mock_conn.start_tls = MagicMock()

        # When bind returns False, the code raises IncorrectCredentials(),
        # but the outer except catches ALL exceptions and raises LdapConnectionError.
        monkeypatch.setattr(
            "core.auth_ldap.Connection",
            lambda *args, **kwargs: mock_conn,
        )
        monkeypatch.setattr("core.auth_ldap.Server", MagicMock())

        from core.auth_ldap import ldap_connect

        with pytest.raises(LdapConnectionError):
            ldap_connect("testuser", "wrongpass")

    def test_ldap_verify_ssl_true(self, monkeypatch):
        """When ldap_verify_ssl is True, Tls uses CERT_REQUIRED."""
        captured_tls_args = {}

        class CaptureTls:
            def __init__(self, **kwargs):
                captured_tls_args.update(kwargs)

        mock_conn = MockLDAPConnection()
        mock_conn.start_tls = MagicMock()

        monkeypatch.setattr("core.auth_ldap.Tls", CaptureTls)
        monkeypatch.setattr(
            "core.auth_ldap.Connection",
            lambda *args, **kwargs: mock_conn,
        )
        monkeypatch.setattr("core.auth_ldap.Server", MagicMock())

        # Ensure settings have verify_ssl True
        mock_settings = MagicMock()
        mock_settings.ldap_verify_ssl = True
        mock_settings.ldap_host = "ldap.example.com"
        mock_settings.ldap_port = 636
        mock_settings.ldap_attr_user = "uid"
        mock_settings.ldap_dn_people = "ou=people,dc=example,dc=com"
        monkeypatch.setattr("core.auth_ldap.Settings", lambda: mock_settings)

        from core.auth_ldap import ldap_connect

        ldap_connect("testuser", "testpass")
        assert captured_tls_args.get("validate") == ssl.CERT_REQUIRED

    def test_ldap_verify_ssl_false(self, monkeypatch):
        """When ldap_verify_ssl is False, Tls uses CERT_NONE."""
        captured_tls_args = {}

        class CaptureTls:
            def __init__(self, **kwargs):
                captured_tls_args.update(kwargs)

        mock_conn = MockLDAPConnection()
        mock_conn.start_tls = MagicMock()

        monkeypatch.setattr("core.auth_ldap.Tls", CaptureTls)
        monkeypatch.setattr(
            "core.auth_ldap.Connection",
            lambda *args, **kwargs: mock_conn,
        )
        monkeypatch.setattr("core.auth_ldap.Server", MagicMock())

        mock_settings = MagicMock()
        mock_settings.ldap_verify_ssl = False
        mock_settings.ldap_host = "ldap.example.com"
        mock_settings.ldap_port = 636
        mock_settings.ldap_attr_user = "uid"
        mock_settings.ldap_dn_people = "ou=people,dc=example,dc=com"
        monkeypatch.setattr("core.auth_ldap.Settings", lambda: mock_settings)

        from core.auth_ldap import ldap_connect

        ldap_connect("testuser", "testpass")
        assert captured_tls_args.get("validate") == ssl.CERT_NONE

    def test_connection_error_raises_ldap_error(self, monkeypatch):
        """Connection raising Exception -> LdapConnectionError."""

        def raise_on_connect(*args, **kwargs):
            raise RuntimeError("Network unreachable")

        monkeypatch.setattr("core.auth_ldap.Connection", raise_on_connect)
        monkeypatch.setattr("core.auth_ldap.Server", MagicMock())

        from core.auth_ldap import ldap_connect

        with pytest.raises(LdapConnectionError):
            ldap_connect("testuser", "testpass")
