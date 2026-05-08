"""Integration tests for /v{x}/sub-tasks/ endpoints."""

import uuid

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def task_for_subtask(db_session, system_user):
    """Create a parent task."""
    from tests.factories.task_factory import TaskFactory

    return TaskFactory(
        status="queued",
        createdById=system_user.id,
        updatedById=system_user.id,
    )


@pytest.fixture()
def sample_subtask(db_session, system_user, task_for_subtask):
    """Create a subtask in the test DB."""
    from tests.factories.task_factory import SubTaskFactory

    return SubTaskFactory(
        parent_task=task_for_subtask.id,
        status="queued",
        createdById=system_user.id,
        updatedById=system_user.id,
    )


@pytest.fixture()
def failed_subtask(db_session, system_user, task_for_subtask):
    """Create a failed subtask for retry tests."""
    from tests.factories.task_factory import SubTaskFactory

    return SubTaskFactory(
        parent_task=task_for_subtask.id,
        status="failed",
        createdById=system_user.id,
        updatedById=system_user.id,
    )


class TestGetSubTasks:
    """GET /sub-tasks/ — list all subtasks."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_subtask,
    ):
        resp = client.get(f"{API}/sub-tasks/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/sub-tasks/")
        assert resp.status_code in (401, 403)

    def test_permission_denied(self, client, auth_headers):
        """Without mock_permission_allow, sub_tasks_read is denied."""
        resp = client.get(f"{API}/sub-tasks/", headers=auth_headers)
        assert resp.status_code == 403


class TestGetSubTaskById:
    """GET /sub-tasks/{id} — get single subtask."""

    def test_returns_subtask(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_subtask,
    ):
        resp = client.get(
            f"{API}/sub-tasks/{sample_subtask.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_subtask.id)

    def test_not_found_returns_404(self, client, auth_headers, mock_permission_allow):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/sub-tasks/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404


class TestRetrySubTask:
    """GET /sub-tasks/{id}/retry — retry a failed subtask."""

    def test_retry_non_failed_returns_403(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        mock_redis_queues,
        sample_subtask,
    ):
        """Only failed subtasks can be retried."""
        resp = client.get(
            f"{API}/sub-tasks/{sample_subtask.id}/retry",
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_retry_failed_subtask_without_redis_returns_400(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        mock_redis_queues,
        failed_subtask,
    ):
        """Non-periodic failed subtasks need Redis to retry; returns 400
        because the job cannot be found in the mocked queue."""
        resp = client.get(
            f"{API}/sub-tasks/{failed_subtask.id}/retry",
            headers=auth_headers,
        )
        assert resp.status_code == 400
