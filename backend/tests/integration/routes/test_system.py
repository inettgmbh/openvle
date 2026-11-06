"""Integration tests for /v{x}/system/ endpoints."""

import uuid

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_setting(db_session, system_user):
    """Create a public system setting in the test DB."""
    from tests.factories.system_factory import SystemSettingFactory

    return SystemSettingFactory(
        key="test.public.setting",
        value="hello",
        visibility="public",
        description="A public test setting",
        createdById=system_user.id,
        updatedById=system_user.id,
    )


@pytest.fixture()
def authenticated_setting(db_session, system_user):
    """Create an authenticated-visibility system setting."""
    from tests.factories.system_factory import SystemSettingFactory

    return SystemSettingFactory(
        key="test.auth.setting",
        value="auth-only",
        visibility="authenticated",
        description="Visible to authenticated users",
        createdById=system_user.id,
        updatedById=system_user.id,
    )


class TestGetSystemSettings:
    """GET /system/settings -- get system settings."""

    def test_returns_settings_with_permission(
        self, client, auth_headers, mock_permission_allow, sample_setting
    ):
        resp = client.get(f"{API}/system/settings", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data

    def test_returns_limited_settings_without_auth(
        self, client, sample_setting
    ):
        """Settings endpoint works without auth but returns limited data."""
        resp = client.get(f"{API}/system/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data

    def test_returns_limited_settings_without_permission(
        self, client, auth_headers, sample_setting
    ):
        """Without system_read permission, returns limited settings."""
        resp = client.get(f"{API}/system/settings", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data


class TestUpdateSystemSetting:
    """PUT /system/settings/{id} -- update system setting."""

    def test_update_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_setting,
    ):
        payload = {"value": "updated_value"}
        resp = client.put(
            f"{API}/system/settings/{sample_setting.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["value"] == "updated_value"
        assert data["key"] == "test.public.setting"

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        payload = {"value": "new_value"}
        resp = client.put(
            f"{API}/system/settings/{fake_id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        """Use non-existent ID so ChangelogMiddleware exits early."""
        fake_id = uuid.uuid4()
        payload = {"value": "test"}
        resp = client.put(f"{API}/system/settings/{fake_id}", json=payload)
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        fake_id = uuid.uuid4()
        payload = {"value": "test"}
        resp = client.put(
            f"{API}/system/settings/{fake_id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403
