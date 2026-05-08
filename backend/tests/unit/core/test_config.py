"""Tests for core/config.py - Settings / Pydantic BaseSettings defaults and overrides."""


class TestSettingsDefaults:
    """Test that default values in Settings match expected values."""

    def _make_settings(self, monkeypatch, **overrides):
        """Create a fresh Settings instance with optional env overrides."""
        for key, value in overrides.items():
            monkeypatch.setenv(key, str(value))
        from core.config import Settings

        return Settings()

    def test_default_values(self, monkeypatch):
        """Core defaults are set correctly."""
        s = self._make_settings(monkeypatch)
        assert s.app_env == "testing"  # Set by conftest
        assert s.project_name == "test_openvle"  # Set by conftest

    def test_env_override(self, monkeypatch):
        """monkeypatch.setenv overrides default values."""
        s = self._make_settings(monkeypatch, project_description="overridden")
        assert s.project_description == "overridden"

    def test_auth_settings_defaults(self, monkeypatch):
        """Auth-related settings have expected defaults."""
        s = self._make_settings(monkeypatch)
        assert s.auth_algorithm == "HS256"
        assert s.auth_access_token_expire_minutes == 480

    def test_mariadb_settings(self, monkeypatch):
        """MariaDB connection settings are populated."""
        s = self._make_settings(monkeypatch)
        assert s.mariadb_host == "localhost"
        assert s.mariadb_port == 3306
        assert s.mariadb_charset == "utf8mb4"
        assert s.mariadb_pool_min >= 1
        assert s.mariadb_pool_max >= s.mariadb_pool_min

    def test_smtp_settings(self, monkeypatch):
        """SMTP settings have sensible defaults."""
        s = self._make_settings(monkeypatch)
        assert isinstance(s.smtp_host, str)
        assert isinstance(s.smtp_port, int)
        assert s.smtp_method in ("ssl", "tls", "PLAIN", "NONE")

    def test_pve_settings(self, monkeypatch):
        """Proxmox settings are present."""
        s = self._make_settings(monkeypatch)
        assert isinstance(s.pve_hostname, str)
        assert isinstance(s.pve_user, str)
        assert isinstance(s.pve_token_name, str)
        assert isinstance(s.pve_token_value, str)

    def test_guacamole_settings(self, monkeypatch):
        """Guacamole settings are present."""
        s = self._make_settings(monkeypatch)
        assert isinstance(s.guacamole_url, str)
        assert isinstance(s.guacamole_user, str)
        assert isinstance(s.guacamole_password, str)

    def test_cors_settings(self, monkeypatch):
        """CORS settings have correct structure."""
        s = self._make_settings(monkeypatch)
        assert isinstance(s.cors_origins, list)
        assert isinstance(s.cors_methods, list)
        assert isinstance(s.cors_headers, list)
        assert isinstance(s.cors_credentials, bool)

    def test_events_settings(self, monkeypatch):
        """Event preparation time settings are integers."""
        s = self._make_settings(monkeypatch)
        assert isinstance(s.events_start_prep_time_days, int)
        assert s.events_start_prep_time_days == 7
        assert isinstance(s.events_end_prep_time_days, int)
        assert s.events_end_prep_time_days == 7

    def test_sentry_settings_disabled_by_default(self, monkeypatch):
        """Sentry is disabled by default in the test environment."""
        s = self._make_settings(monkeypatch)
        assert s.sentry_backend_enabled is False
        assert s.sentry_worker_enabled is False
