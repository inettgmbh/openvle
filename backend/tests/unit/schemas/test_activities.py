"""Tests for schemas/activities.py - Activity schema validation."""

from datetime import datetime, timezone

from schemas.activities import Activity, ActivityOwn, RequestUser


class TestRequestUser:
    def test_valid(self):
        u = RequestUser(id="abc123", username="admin")
        assert u.id == "abc123"
        assert u.username == "admin"

    def test_optional_fields(self):
        u = RequestUser()
        assert u.id is None
        assert u.username is None


class TestActivity:
    def test_valid_activity(self):
        a = Activity(
            id="abc123",
            timestamp=datetime.now(timezone.utc),
            requestClientIP="192.168.1.1",
            requestUser=RequestUser(id="1", username="admin"),
            requestMethod="GET",
            requestUrl="/v1/users",
            requestParameter={},
            requestHeaders={},
            responseCode=200,
            responseHeaders={},
        )
        assert a.requestMethod == "GET"
        assert a.responseCode == 200
        assert a.requestPermission is None


class TestActivityOwn:
    def test_valid_activity_own(self):
        a = ActivityOwn(
            id="def456",
            timestamp=datetime.now(timezone.utc),
            requestClientIP="10.0.0.1",
            requestMethod="POST",
            requestUrl="/v1/events",
            responseCode=201,
        )
        assert a.requestMethod == "POST"
        assert a.responseCode == 201
