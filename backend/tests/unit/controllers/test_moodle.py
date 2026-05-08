"""Tests for controllers/moodle.py - search_courses controller."""

from unittest.mock import MagicMock

import pytest

from core.exceptions import (
    MoodleConnectionError,
    MoodleNotEnabledError,
    MoodleRequestError,
)
from core.moodlelib import MoodleAPIError
from tests.helpers.mock_moodle import MockMoodleClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def mock_moodle_enabled(monkeypatch):
    """Patch settings to enable Moodle."""
    mock_settings = MagicMock()
    mock_settings.moodle_enabled = True
    mock_settings.moodle_sync_timeout = 10
    monkeypatch.setattr("controllers.moodle.settings", mock_settings)
    return mock_settings


@pytest.fixture()
def mock_moodle_disabled(monkeypatch):
    """Patch settings to disable Moodle."""
    mock_settings = MagicMock()
    mock_settings.moodle_enabled = False
    monkeypatch.setattr("controllers.moodle.settings", mock_settings)
    return mock_settings


@pytest.fixture()
def mock_moodle_client(monkeypatch):
    """Create and inject a MockMoodleClient."""
    mock = MockMoodleClient()
    monkeypatch.setattr(
        "controllers.moodle.moodle_connect",
        lambda **kw: mock,
    )
    return mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestMoodleSearchCourses:
    def test_search_by_text(self, mock_moodle_enabled, mock_moodle_client):
        mock_moodle_client.returns["search_courses"] = [
            {
                "id": 1,
                "fullname": "Python 101",
                "shortname": "PY101",
                "categoryname": "IT",
                "startdate": 0,
                "enddate": 0,
                "visible": 1,
            },
        ]

        from controllers.moodle import search_courses

        result = search_courses(search="Python")

        assert len(result.items) == 1
        assert result.items[0].fullname == "Python 101"

    def test_search_by_id(self, mock_moodle_enabled, mock_moodle_client):
        mock_moodle_client.returns["get_courses_by_field"] = [
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

        from controllers.moodle import search_courses

        result = search_courses(id=42)

        assert len(result.items) == 1
        assert result.items[0].id == 42

    def test_empty_search_string(self, mock_moodle_enabled, mock_moodle_client):
        mock_moodle_client.returns["search_courses"] = []

        from controllers.moodle import search_courses

        result = search_courses(search="")

        assert len(result.items) == 0
        assert result.pageDetails.totalCount == 0

    def test_moodle_disabled_raises(self, mock_moodle_disabled):
        from controllers.moodle import search_courses

        with pytest.raises(MoodleNotEnabledError):
            search_courses(search="test")

    def test_connection_error_raises(self, mock_moodle_enabled, monkeypatch):
        monkeypatch.setattr(
            "controllers.moodle.moodle_connect",
            lambda **kw: False,
        )

        from controllers.moodle import search_courses

        with pytest.raises(MoodleConnectionError):
            search_courses(search="test")

    def test_api_error_raises_request_error(
        self,
        mock_moodle_enabled,
        mock_moodle_client,
    ):
        mock_moodle_client._errors["search_courses"] = MoodleAPIError(
            "invalidparam", "Bad search param"
        )

        from controllers.moodle import search_courses

        with pytest.raises(MoodleRequestError):
            search_courses(search="test")

    def test_unexpected_error_raises_request_error(
        self,
        mock_moodle_enabled,
        mock_moodle_client,
    ):
        mock_moodle_client._errors["search_courses"] = RuntimeError("boom")

        from controllers.moodle import search_courses

        with pytest.raises(MoodleRequestError):
            search_courses(search="test")

    def test_client_closed_on_success(
        self,
        mock_moodle_enabled,
        mock_moodle_client,
    ):
        mock_moodle_client.returns["search_courses"] = []

        from controllers.moodle import search_courses

        search_courses(search="test")

        assert mock_moodle_client._closed is True

    def test_client_closed_on_error(
        self,
        mock_moodle_enabled,
        mock_moodle_client,
    ):
        mock_moodle_client._errors["search_courses"] = MoodleAPIError("err", "fail")

        from controllers.moodle import search_courses

        with pytest.raises(MoodleRequestError):
            search_courses(search="test")

        assert mock_moodle_client._closed is True

    def test_invalid_course_dicts_filtered(
        self,
        mock_moodle_enabled,
        mock_moodle_client,
    ):
        mock_moodle_client.returns["search_courses"] = [
            {
                "id": 1,
                "fullname": "Valid",
                "shortname": "V",
                "categoryname": "Cat",
                "startdate": 0,
                "enddate": 0,
                "visible": 1,
            },
            "not a dict",
            {"no_id_key": True},
        ]

        from controllers.moodle import search_courses

        result = search_courses(search="test")

        assert len(result.items) == 1

    def test_pagination_details_correct(
        self,
        mock_moodle_enabled,
        mock_moodle_client,
    ):
        mock_moodle_client.returns["search_courses"] = [
            {
                "id": i,
                "fullname": f"Course {i}",
                "shortname": f"C{i}",
                "categoryname": "Cat",
                "startdate": 0,
                "enddate": 0,
                "visible": 1,
            }
            for i in range(3)
        ]

        from controllers.moodle import search_courses

        result = search_courses(search="test")

        assert result.pageDetails.page == 1
        assert result.pageDetails.perPage == 3
        assert result.pageDetails.pageCount == 1
        assert result.pageDetails.totalCount == 3
