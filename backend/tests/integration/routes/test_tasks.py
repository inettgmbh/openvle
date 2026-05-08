"""Integration tests for /v{x}/tasks/ endpoints."""

import uuid

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_task(db_session, system_user):
    """Create a task in the test DB."""
    from tests.factories.task_factory import TaskFactory

    return TaskFactory(
        status="queued",
        createdById=system_user.id,
        updatedById=system_user.id,
    )


@pytest.fixture()
def sample_subtask(db_session, system_user, sample_task):
    """Create a subtask for sample_task."""
    from tests.factories.task_factory import SubTaskFactory

    return SubTaskFactory(
        parent_task=sample_task.id,
        status="queued",
        createdById=system_user.id,
        updatedById=system_user.id,
    )


class TestGetTasks:
    """GET /tasks/ — list all tasks."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_task,
    ):
        resp = client.get(f"{API}/tasks/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/tasks/")
        assert resp.status_code in (401, 403)

    def test_permission_denied(self, client, auth_headers):
        """Without mock_permission_allow, tasks_read is denied."""
        resp = client.get(f"{API}/tasks/", headers=auth_headers)
        assert resp.status_code == 403


class TestGetTaskById:
    """GET /tasks/{id} — get single task."""

    def test_returns_task(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_task,
    ):
        resp = client.get(f"{API}/tasks/{sample_task.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_task.id)
        assert data["name"] == sample_task.name

    def test_not_found_returns_404(self, client, auth_headers, mock_permission_allow):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/tasks/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404


class TestGetTaskSubTasks:
    """GET /tasks/{id}/sub-tasks — subtasks for a task."""

    def test_returns_subtasks(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_task,
        sample_subtask,
    ):
        resp = client.get(
            f"{API}/tasks/{sample_task.id}/sub-tasks",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_empty_subtasks(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_task,
    ):
        resp = client.get(
            f"{API}/tasks/{sample_task.id}/sub-tasks",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
