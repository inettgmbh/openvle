"""Integration tests for /v{x}/activities/ endpoints.

Activities are stored in MongoDB which is fully mocked (MagicMock) in
the test environment.  Auth/permission tests (401/403) are safe because
they fail before touching MongoDB.  For the "own" endpoint (no explicit
permission check), the mock chain returns an empty list which may or may
not work depending on how ``count_documents`` interacts with
``paginate``.
"""

from tests.integration.conftest import API

FAKE_OBJECT_ID = "507f1f77bcf86cd799439011"


# -- Own activities ----------------------------------------------------


class TestGetOwnActivities:
    """GET /activities/own -- get own activities (auth only, no perm)."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/activities/own")
        assert resp.status_code in (401, 403)


# -- Single activity by ID --------------------------------------------


class TestGetActivityById:
    """GET /activities/{id} -- get single activity by MongoDB ObjectId."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/activities/{FAKE_OBJECT_ID}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        resp = client.get(
            f"{API}/activities/{FAKE_OBJECT_ID}", headers=auth_headers
        )
        assert resp.status_code == 403

    def test_invalid_id_format_returns_422(self, client, auth_headers):
        """MongoDB ObjectId must be exactly 24 hex chars."""
        resp = client.get(
            f"{API}/activities/not-a-valid-id", headers=auth_headers
        )
        assert resp.status_code == 422


# -- List all activities -----------------------------------------------


class TestGetAllActivities:
    """GET /activities/ -- list all activities."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/activities/")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers):
        resp = client.get(f"{API}/activities/", headers=auth_headers)
        assert resp.status_code == 403
