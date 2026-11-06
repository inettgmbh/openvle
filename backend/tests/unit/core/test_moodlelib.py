"""Tests for core/moodlelib.py - Moodle Web Services HTTP client."""

from unittest.mock import MagicMock

import httpx
import pytest
from core.moodlelib import MoodleAPIError, MoodleClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_response(json_data, status_code=200):
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
    return resp


def _patch_post(monkeypatch, response):
    """Monkeypatch httpx.Client.post to return a fixed response."""
    captured = {}

    def fake_post(self, url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return response

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    return captured


# ---------------------------------------------------------------------------
# TestMoodleClientInit
# ---------------------------------------------------------------------------
class TestMoodleClientInit:
    def test_url_trailing_slash_stripped(self):
        client = MoodleClient(
            url="https://moodle.example.com/",
            token="tok",
        )
        assert client.url == "https://moodle.example.com"
        client.close()

    def test_endpoint_constructed(self):
        client = MoodleClient(
            url="https://moodle.example.com",
            token="tok",
        )
        assert client.endpoint == (
            "https://moodle.example.com/webservice/rest/server.php"
        )
        client.close()

    def test_custom_timeout(self):
        client = MoodleClient(
            url="https://moodle.example.com",
            token="tok",
            timeout=60,
        )
        assert client.client.timeout == httpx.Timeout(60)
        client.close()


# ---------------------------------------------------------------------------
# TestMoodleClientCall
# ---------------------------------------------------------------------------
class TestMoodleClientCall:
    def test_post_with_correct_params(self, monkeypatch):
        resp = _make_response({"sitename": "Test Moodle"})
        captured = _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="my-token")
        result = client._call("core_webservice_get_site_info")

        assert captured["url"] == "https://m.test/webservice/rest/server.php"
        data = captured["kwargs"]["data"]
        assert data["wstoken"] == "my-token"
        assert data["wsfunction"] == "core_webservice_get_site_info"
        assert data["moodlewsrestformat"] == "json"
        assert result == {"sitename": "Test Moodle"}
        client.close()

    def test_returns_parsed_json(self, monkeypatch):
        resp = _make_response([{"id": 1}, {"id": 2}])
        _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        result = client._call("core_course_get_courses")
        assert result == [{"id": 1}, {"id": 2}]
        client.close()

    def test_raises_moodle_api_error_on_exception_response(self, monkeypatch):
        resp = _make_response(
            {
                "exception": "moodle_exception",
                "errorcode": "invalidtoken",
                "message": "Invalid token",
            }
        )
        _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="bad")
        with pytest.raises(MoodleAPIError) as exc_info:
            client._call("core_webservice_get_site_info")
        assert exc_info.value.error_code == "invalidtoken"
        assert "Invalid token" in exc_info.value.message
        client.close()

    def test_raises_http_error_on_500(self, monkeypatch):
        resp = _make_response({}, status_code=500)
        _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        with pytest.raises(httpx.HTTPStatusError):
            client._call("core_webservice_get_site_info")
        client.close()

    def test_extra_params_sent(self, monkeypatch):
        resp = _make_response({"courses": []})
        captured = _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        client._call(
            "core_course_search_courses",
            criterianame="search",
            criteriavalue="python",
        )
        data = captured["kwargs"]["data"]
        assert data["criterianame"] == "search"
        assert data["criteriavalue"] == "python"
        client.close()


# ---------------------------------------------------------------------------
# TestMoodleClientCourses
# ---------------------------------------------------------------------------
class TestMoodleClientCourses:
    def test_get_courses_no_ids(self, monkeypatch):
        resp = _make_response([{"id": 1}])
        captured = _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        result = client.get_courses()
        assert result == [{"id": 1}]
        data = captured["kwargs"]["data"]
        assert "options[ids][0]" not in data
        client.close()

    def test_get_courses_with_ids(self, monkeypatch):
        resp = _make_response([{"id": 1}, {"id": 2}])
        captured = _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        client.get_courses([1, 2])
        data = captured["kwargs"]["data"]
        assert data["options[ids][0]"] == 1
        assert data["options[ids][1]"] == 2
        client.close()

    def test_search_courses_extracts_courses_key(self, monkeypatch):
        resp = _make_response({"courses": [{"id": 10}], "total": 1})
        _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        result = client.search_courses("python")
        assert result == [{"id": 10}]
        client.close()

    def test_search_courses_returns_raw_if_no_courses_key(self, monkeypatch):
        resp = _make_response([{"id": 10}])
        _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        result = client.search_courses("python")
        assert result == [{"id": 10}]
        client.close()

    def test_get_courses_by_field_params(self, monkeypatch):
        resp = _make_response({"courses": [{"id": 5}]})
        captured = _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        client.get_courses_by_field("shortname", "CS101")
        data = captured["kwargs"]["data"]
        assert data["field"] == "shortname"
        assert data["value"] == "CS101"
        client.close()

    def test_create_courses_array_serialisation(self, monkeypatch):
        resp = _make_response([{"id": 99, "shortname": "NEW"}])
        captured = _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        client.create_courses(
            [{"fullname": "New Course", "shortname": "NEW", "categoryid": 1}]
        )
        data = captured["kwargs"]["data"]
        assert data["courses[0][fullname]"] == "New Course"
        assert data["courses[0][shortname]"] == "NEW"
        client.close()

    def test_update_courses_array_serialisation(self, monkeypatch):
        resp = _make_response(None)
        captured = _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        client.update_courses([{"id": 5, "visible": 0}])
        data = captured["kwargs"]["data"]
        assert data["courses[0][id]"] == 5
        assert data["courses[0][visible]"] == 0
        client.close()

    def test_delete_courses_array_serialisation(self, monkeypatch):
        resp = _make_response(None)
        captured = _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        client.delete_courses([10, 20])
        data = captured["kwargs"]["data"]
        assert data["courseids[0]"] == 10
        assert data["courseids[1]"] == 20
        client.close()

    def test_duplicate_course_params(self, monkeypatch):
        resp = _make_response({"id": 100, "shortname": "DUP"})
        captured = _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        client.duplicate_course(
            course_id=5,
            fullname="Dup Course",
            shortname="DUP",
            categoryid=1,
            visible=False,
        )
        data = captured["kwargs"]["data"]
        assert data["courseid"] == 5
        assert data["fullname"] == "Dup Course"
        assert data["visible"] == 0  # int(False)
        client.close()


# ---------------------------------------------------------------------------
# TestMoodleClientUsers
# ---------------------------------------------------------------------------
class TestMoodleClientUsers:
    def test_get_users_by_field_params(self, monkeypatch):
        resp = _make_response([{"id": 42, "username": "jdoe"}])
        captured = _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        client.get_users_by_field("email", ["jdoe@example.com"])
        data = captured["kwargs"]["data"]
        assert data["field"] == "email"
        assert data["values[0]"] == "jdoe@example.com"
        client.close()

    def test_create_users_array_serialisation(self, monkeypatch):
        resp = _make_response([{"id": 50, "username": "new"}])
        captured = _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        client.create_users(
            [
                {
                    "username": "new",
                    "firstname": "New",
                    "lastname": "User",
                    "email": "new@example.com",
                    "auth": "ldap",
                }
            ]
        )
        data = captured["kwargs"]["data"]
        assert data["users[0][username]"] == "new"
        assert data["users[0][auth]"] == "ldap"
        client.close()


# ---------------------------------------------------------------------------
# TestMoodleClientEnrolment
# ---------------------------------------------------------------------------
class TestMoodleClientEnrolment:
    def test_enrol_users_serialisation(self, monkeypatch):
        resp = _make_response(None)
        captured = _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        client.enrol_users([{"roleid": 5, "userid": 42, "courseid": 10}])
        data = captured["kwargs"]["data"]
        assert data["enrolments[0][roleid]"] == 5
        assert data["enrolments[0][userid]"] == 42
        assert data["enrolments[0][courseid]"] == 10
        client.close()

    def test_unenrol_users_serialisation(self, monkeypatch):
        resp = _make_response(None)
        captured = _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        client.unenrol_users([{"roleid": 5, "userid": 42, "courseid": 10}])
        data = captured["kwargs"]["data"]
        assert data["enrolments[0][roleid]"] == 5
        client.close()

    def test_unassign_roles_default_contextlevel(self, monkeypatch):
        resp = _make_response(None)
        captured = _patch_post(monkeypatch, resp)

        client = MoodleClient(url="https://m.test", token="t")
        client.unassign_roles([{"roleid": 3, "userid": 42, "instanceid": 10}])
        data = captured["kwargs"]["data"]
        assert data["unassignments[0][contextlevel]"] == "course"
        client.close()


# ---------------------------------------------------------------------------
# TestMoodleClientClose
# ---------------------------------------------------------------------------
class TestMoodleClientClose:
    def test_close_closes_httpx_client(self, monkeypatch):
        closed = {"called": False}

        def fake_close(self):
            closed["called"] = True

        monkeypatch.setattr(httpx.Client, "close", fake_close)

        client = MoodleClient(url="https://m.test", token="t")
        client.close()
        assert closed["called"] is True
