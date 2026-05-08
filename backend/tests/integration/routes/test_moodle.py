"""Integration tests for /v{x}/moodle/ endpoints."""

from unittest.mock import MagicMock

import pytest

from tests.helpers.mock_moodle import MockMoodleClient
from tests.integration.conftest import API


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def mock_moodle_enabled(monkeypatch):
    """Enable Moodle and inject a MockMoodleClient for the controller."""
    mock_settings = MagicMock()
    mock_settings.moodle_enabled = True
    mock_settings.moodle_sync_timeout = 10
    monkeypatch.setattr("controllers.moodle.settings", mock_settings)

    mock = MockMoodleClient()
    monkeypatch.setattr("controllers.moodle.moodle_connect", lambda **kw: mock)
    return mock


@pytest.fixture()
def mock_moodle_disabled(monkeypatch):
    """Disable Moodle integration."""
    mock_settings = MagicMock()
    mock_settings.moodle_enabled = False
    monkeypatch.setattr("controllers.moodle.settings", mock_settings)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestMoodleCoursesEndpoint:
    def test_no_auth_returns_401_or_403(self, client):
        resp = client.get(f"{API}/moodle/courses")
        assert resp.status_code in (401, 403)

    def test_no_permission_returns_403(
        self,
        client,
        auth_headers,
        monkeypatch,
    ):
        from core.dependencies import PermissionChecker

        monkeypatch.setattr(
            PermissionChecker,
            "has_permission",
            lambda self: False,
        )

        mock_settings = MagicMock()
        mock_settings.moodle_enabled = True
        mock_settings.moodle_sync_timeout = 10
        monkeypatch.setattr("controllers.moodle.settings", mock_settings)

        resp = client.get(f"{API}/moodle/courses", headers=auth_headers)
        assert resp.status_code == 403

    def test_happy_path_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        mock_moodle_enabled,
    ):
        mock_moodle_enabled.returns["search_courses"] = [
            {
                "id": 1,
                "fullname": "Test Course",
                "shortname": "TC",
                "categoryname": "Default",
                "startdate": 0,
                "enddate": 0,
                "visible": 1,
            },
        ]

        resp = client.get(
            f"{API}/moodle/courses?search=test",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "pageDetails" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["fullname"] == "Test Course"

    def test_search_by_id(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        mock_moodle_enabled,
    ):
        mock_moodle_enabled.returns["get_courses_by_field"] = [
            {
                "id": 42,
                "fullname": "Course 42",
                "shortname": "C42",
                "categoryname": "Cat",
                "startdate": 0,
                "enddate": 0,
                "visible": 1,
            },
        ]

        resp = client.get(
            f"{API}/moodle/courses?id=42",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"][0]["id"] == 42

    def test_search_param(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        mock_moodle_enabled,
    ):
        mock_moodle_enabled.returns["search_courses"] = []

        resp = client.get(
            f"{API}/moodle/courses?search=python",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    def test_moodle_disabled_returns_422(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        mock_moodle_disabled,
    ):
        resp = client.get(
            f"{API}/moodle/courses",
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_connection_error_returns_500(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        monkeypatch,
    ):
        mock_settings = MagicMock()
        mock_settings.moodle_enabled = True
        mock_settings.moodle_sync_timeout = 10
        monkeypatch.setattr("controllers.moodle.settings", mock_settings)
        monkeypatch.setattr(
            "controllers.moodle.moodle_connect",
            lambda **kw: False,
        )

        resp = client.get(
            f"{API}/moodle/courses?search=test",
            headers=auth_headers,
        )
        assert resp.status_code == 500
