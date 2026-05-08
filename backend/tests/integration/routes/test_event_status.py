"""Integration tests for /v{x}/status/events/ endpoints."""

import uuid


from tests.integration.conftest import API


class TestGetEventStatuses:
    """GET /status/events/ — list all event statuses."""

    def test_returns_paginated_list(
        self, client, auth_headers, mock_permission_allow, event_statuses
    ):
        resp = client.get(f"{API}/status/events/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) == 10  # 10 seeded statuses

    def test_pagination_params(
        self, client, auth_headers, mock_permission_allow, event_statuses
    ):
        resp = client.get(
            f"{API}/status/events/",
            params={"limit": 2, "page": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pageDetails"]["perPage"] == 2
        assert len(data["items"]) == 2

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/status/events/")
        assert resp.status_code in (401, 403)


class TestGetEventStatusById:
    """GET /status/events/{id} — get single event status."""

    def test_returns_status(
        self, client, auth_headers, mock_permission_allow, event_statuses
    ):
        status = event_statuses["Geplant"]
        resp = client.get(f"{API}/status/events/{status.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(status.id)
        assert data["name"] == "Geplant"

    def test_not_found_returns_404(self, client, auth_headers, mock_permission_allow):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/status/events/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/status/events/{fake_id}")
        assert resp.status_code in (401, 403)
