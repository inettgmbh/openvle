"""Tests for controllers/sub_tasks.py - CRUDSubTask operations."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from controllers.sub_tasks import CRUDSubTask
from models import Course, Event, SubTask, Task
from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def parent_task(db_session, system_user):
    now = datetime.now(timezone.utc)
    task = Task(
        id=uuid.uuid4(),
        name="Parent Task",
        status="queued",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(task)
    db_session.flush()
    return task


@pytest.fixture()
def sample_subtask(db_session, system_user, parent_task):
    now = datetime.now(timezone.utc)
    subtask = SubTask(
        id=uuid.uuid4(),
        name="Test SubTask",
        status="queued",
        object_type="VirtualMachine",
        object_id=str(uuid.uuid4()),
        action="vm_clone",
        attempt="0",
        parent_task=parent_task.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(subtask)
    db_session.flush()
    return subtask


class TestWorkerProcessStart:
    def setup_method(self):
        self.crud = CRUDSubTask(SubTask)

    def test_sets_status_processing(self, db_session, sample_subtask):
        result = self.crud.worker_process_start(db_session, id=sample_subtask.id)
        assert result is True
        db_session.refresh(sample_subtask)
        assert sample_subtask.status == "processing"

    def test_increments_attempt(self, db_session, sample_subtask):
        self.crud.worker_process_start(db_session, id=sample_subtask.id)
        db_session.refresh(sample_subtask)
        assert int(sample_subtask.attempt) == 1

    def test_nonexistent_subtask_raises(self, db_session, system_user):
        from pve.worker_utils import TaskException

        with pytest.raises(TaskException):
            self.crud.worker_process_start(db_session, id=uuid.uuid4())


class TestWorkerProcessSuccess:
    def setup_method(self):
        self.crud = CRUDSubTask(SubTask)

    @patch("core.mail_automated.system_triggered_mail_handler")
    def test_sets_status_success(self, mock_mail_handler, db_session, sample_subtask):
        self.crud.worker_process_success(
            id=sample_subtask.id,
            response_code=200,
            response_message="OK",
            db=db_session,
        )
        db_session.refresh(sample_subtask)
        assert sample_subtask.status == "success"
        assert sample_subtask.response_code == "200"

    @patch("core.mail_automated.system_triggered_mail_handler")
    def test_completes_parent_task_when_all_done(
        self, mock_mail_handler, db_session, sample_subtask, parent_task
    ):
        """When all subtasks succeed, parent task status becomes 'success'."""
        self.crud.worker_process_success(
            id=sample_subtask.id,
            response_code=200,
            response_message="OK",
            db=db_session,
        )
        db_session.refresh(parent_task)
        assert parent_task.status == "success"


class TestWorkerProcessFail:
    def setup_method(self):
        self.crud = CRUDSubTask(SubTask)

    @patch("core.mail_automated.system_triggered_mail_handler")
    def test_sets_status_failed(self, mock_mail_handler, db_session, sample_subtask):
        from pve.worker_utils import TaskException

        with pytest.raises(TaskException):
            self.crud.worker_process_fail(
                id=sample_subtask.id,
                response_code=500,
                response_message="Error occurred",
                db=db_session,
            )
        db_session.refresh(sample_subtask)
        assert sample_subtask.status == "failed"

    @patch("core.mail_automated.system_triggered_mail_handler")
    def test_truncates_long_response_message(
        self, mock_mail_handler, db_session, sample_subtask
    ):
        from pve.worker_utils import TaskException

        long_msg = "x" * 600
        with pytest.raises(TaskException):
            self.crud.worker_process_fail(
                id=sample_subtask.id,
                response_code=500,
                response_message=long_msg,
                db=db_session,
            )
        db_session.refresh(sample_subtask)
        assert len(sample_subtask.response_message) <= 500

    @patch("core.mail_automated.system_triggered_mail_handler")
    def test_max_retry_fails_parent_task(
        self, mock_mail_handler, db_session, sample_subtask, parent_task
    ):
        """When max_retry is reached, parent task status becomes 'failed'."""
        from pve.worker_utils import TaskException

        # Set attempt to max_retry (5)
        sample_subtask.attempt = "5"
        db_session.flush()

        with pytest.raises(TaskException):
            self.crud.worker_process_fail(
                id=sample_subtask.id,
                response_code=500,
                response_message="Max retry reached",
                db=db_session,
            )
        db_session.refresh(parent_task)
        assert parent_task.status == "failed"

    @patch("core.mail_automated.system_triggered_mail_handler")
    def test_max_retry_with_event_updates_event_status(
        self, mock_mail_handler, db_session, system_user, event_statuses
    ):
        """When max_retry is reached and task is linked to an event, event status changes."""
        from pve.worker_utils import TaskException

        deploying_status = event_statuses["Deploying"]

        now = datetime.now(timezone.utc)
        course = Course(
            id=uuid.uuid4(),
            name="Test Course",
            description="Course for subtask test",
            guacamole=True,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(course)
        db_session.flush()

        event = Event(
            id=uuid.uuid4(),
            name="Test Event",
            slug="tst-evnt",
            dateStart=now.date(),
            dateEnd=now.date(),
            status=deploying_status.id,
            course=course.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(event)
        db_session.flush()

        task = Task(
            id=uuid.uuid4(),
            name="Event Task",
            status="processing",
            event_id=event.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(task)
        db_session.flush()

        subtask = SubTask(
            id=uuid.uuid4(),
            name="Event SubTask",
            status="processing",
            object_type="VirtualMachine",
            object_id=str(uuid.uuid4()),
            action="vm_clone",
            attempt="5",
            parent_task=task.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(subtask)
        db_session.flush()

        with pytest.raises(TaskException):
            self.crud.worker_process_fail(
                id=subtask.id,
                response_code=500,
                response_message="Deploy failed",
                db=db_session,
            )

        db_session.refresh(event)
        deploy_error_status = event_statuses["Deployment Fehler"]
        assert event.status == deploy_error_status.id


class TestRetry:
    """Tests for CRUDSubTask.retry() method."""

    def setup_method(self):
        self.crud = CRUDSubTask(SubTask)

    # -- Periodic task tests --

    @patch("controllers.sub_tasks.CRUDSubTask._get")
    def test_retry_periodic_proxmox_node_info(
        self,
        mock_get,
        db_session,
        active_user,
        system_user,
        parent_task,
        mock_redis_queues,
    ):
        """Retrying a periodic subtask with job_id 'proxmox_node_info_periodic' should enqueue the task."""
        now = datetime.now(timezone.utc)
        subtask = SubTask(
            id=uuid.uuid4(),
            name="Periodic PVE Node Info",
            status="failed",
            object_type="Proxmox",
            action="periodic_update",
            attempt="3",
            parent_task=parent_task.id,
            job_id="proxmox_node_info_periodic",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(subtask)
        db_session.flush()
        mock_get.return_value = subtask

        request = create_mock_request(active_user)
        result = self.crud.retry(db_session, request, subtask.id)

        assert len(mock_redis_queues) == 1
        assert result.status == "queued"
        assert result.attempt == "0"
        assert result.updatedById == active_user.id

    @patch("controllers.sub_tasks.CRUDSubTask._get")
    def test_retry_periodic_events(
        self,
        mock_get,
        db_session,
        active_user,
        system_user,
        parent_task,
        mock_redis_queues,
    ):
        """Retrying a periodic subtask with job_id 'core_events_periodic' should enqueue the task."""
        now = datetime.now(timezone.utc)
        subtask = SubTask(
            id=uuid.uuid4(),
            name="Periodic Events",
            status="failed",
            object_type="Event",
            action="periodic_update",
            attempt="2",
            parent_task=parent_task.id,
            job_id="core_events_periodic",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(subtask)
        db_session.flush()
        mock_get.return_value = subtask

        request = create_mock_request(active_user)
        result = self.crud.retry(db_session, request, subtask.id)

        assert len(mock_redis_queues) == 1
        assert result.status == "queued"
        assert result.attempt == "0"

    @patch("controllers.sub_tasks.CRUDSubTask._get")
    def test_retry_periodic_mail_delete(
        self,
        mock_get,
        db_session,
        active_user,
        system_user,
        parent_task,
        mock_redis_queues,
    ):
        """Retrying a periodic subtask with job_id 'core_mail_periodic_delete' should enqueue the task."""
        now = datetime.now(timezone.utc)
        subtask = SubTask(
            id=uuid.uuid4(),
            name="Periodic Mail Delete",
            status="failed",
            object_type="Mail",
            action="periodic_delete",
            attempt="1",
            parent_task=parent_task.id,
            job_id="core_mail_periodic_delete",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(subtask)
        db_session.flush()
        mock_get.return_value = subtask

        request = create_mock_request(active_user)
        result = self.crud.retry(db_session, request, subtask.id)

        assert len(mock_redis_queues) == 1
        assert result.status == "queued"
        assert result.attempt == "0"

    @patch("controllers.sub_tasks.CRUDSubTask._get")
    def test_retry_periodic_unknown_job_id_raises(
        self, mock_get, db_session, active_user, system_user, parent_task
    ):
        """Retrying a periodic subtask with an unknown job_id should raise BadRequestError."""
        from core.exceptions import BadRequestError

        now = datetime.now(timezone.utc)
        subtask = SubTask(
            id=uuid.uuid4(),
            name="Unknown Periodic",
            status="failed",
            object_type="Unknown",
            action="periodic_update",
            attempt="1",
            parent_task=parent_task.id,
            job_id="unknown_periodic_job",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(subtask)
        db_session.flush()
        mock_get.return_value = subtask

        request = create_mock_request(active_user)
        with pytest.raises(BadRequestError):
            self.crud.retry(db_session, request, subtask.id)

    # -- Non-periodic task tests --

    @patch("controllers.sub_tasks.CRUDSubTask._get")
    @patch("controllers.sub_tasks.Job.fetch")
    def test_retry_non_periodic_failed_job_requeues(
        self, mock_fetch, mock_get, db_session, active_user, system_user, parent_task
    ):
        """Retrying a non-periodic failed subtask should requeue the Redis job."""
        now = datetime.now(timezone.utc)
        subtask = SubTask(
            id=uuid.uuid4(),
            name="VM Clone SubTask",
            status="failed",
            object_type="VirtualMachine",
            object_id=str(uuid.uuid4()),
            action="vm_clone",
            attempt="3",
            parent_task=parent_task.id,
            job_id="rq-job-123",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(subtask)
        db_session.flush()
        mock_get.return_value = subtask

        mock_job = MagicMock()
        mock_job.get_status.return_value = "failed"
        mock_job.dependent_ids = []
        mock_fetch.return_value = mock_job

        request = create_mock_request(active_user)
        result = self.crud.retry(db_session, request, subtask.id)

        mock_job.requeue.assert_called_once()
        assert result.status == "queued"
        assert result.attempt == "0"
        assert result.updatedById == active_user.id

    @patch("controllers.sub_tasks.CRUDSubTask._get")
    @patch("controllers.sub_tasks.Job.fetch")
    def test_retry_non_periodic_job_not_found_raises(
        self, mock_fetch, mock_get, db_session, active_user, system_user, parent_task
    ):
        """Retrying a non-periodic subtask where the Redis job is missing should raise BadRequestError."""
        from core.exceptions import BadRequestError
        from rq.exceptions import NoSuchJobError

        now = datetime.now(timezone.utc)
        subtask = SubTask(
            id=uuid.uuid4(),
            name="Missing Job SubTask",
            status="failed",
            object_type="VirtualMachine",
            object_id=str(uuid.uuid4()),
            action="vm_clone",
            attempt="1",
            parent_task=parent_task.id,
            job_id="rq-job-missing",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(subtask)
        db_session.flush()
        mock_get.return_value = subtask

        mock_fetch.side_effect = NoSuchJobError()

        request = create_mock_request(active_user)
        with pytest.raises(BadRequestError):
            self.crud.retry(db_session, request, subtask.id)

    @patch("controllers.sub_tasks.CRUDSubTask._get")
    @patch("controllers.sub_tasks.Job.fetch")
    def test_retry_non_periodic_non_failed_job_does_not_requeue(
        self, mock_fetch, mock_get, db_session, active_user, system_user, parent_task
    ):
        """If the Redis job status is not 'failed', the job should not be requeued."""
        now = datetime.now(timezone.utc)
        subtask = SubTask(
            id=uuid.uuid4(),
            name="Running SubTask",
            status="processing",
            object_type="VirtualMachine",
            object_id=str(uuid.uuid4()),
            action="vm_start",
            attempt="1",
            parent_task=parent_task.id,
            job_id="rq-job-running",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(subtask)
        db_session.flush()
        mock_get.return_value = subtask

        mock_job = MagicMock()
        mock_job.get_status.return_value = "started"
        mock_job.dependent_ids = []
        mock_fetch.return_value = mock_job

        request = create_mock_request(active_user)
        result = self.crud.retry(db_session, request, subtask.id)

        mock_job.requeue.assert_not_called()
        assert result == subtask

    @patch("controllers.sub_tasks.CRUDSubTask._get")
    @patch("controllers.sub_tasks.Job.fetch")
    def test_retry_with_dependent_jobs_retries_dependents(
        self, mock_fetch, mock_get, db_session, active_user, system_user, parent_task
    ):
        """If the job has dependent_ids, retry should attempt to retry dependent subtasks."""
        now = datetime.now(timezone.utc)
        dependent_job_id = "rq-job-dependent"

        # Create the dependent subtask
        dependent_subtask = SubTask(
            id=uuid.uuid4(),
            name="Dependent SubTask",
            status="failed",
            object_type="VirtualMachine",
            object_id=str(uuid.uuid4()),
            action="vm_stop",
            attempt="2",
            parent_task=parent_task.id,
            job_id=dependent_job_id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(dependent_subtask)
        db_session.flush()

        # Create the main subtask
        main_subtask = SubTask(
            id=uuid.uuid4(),
            name="Main SubTask",
            status="failed",
            object_type="VirtualMachine",
            object_id=str(uuid.uuid4()),
            action="vm_clone",
            attempt="2",
            parent_task=parent_task.id,
            job_id="rq-job-main",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(main_subtask)
        db_session.flush()

        # _get returns the main subtask
        mock_get.return_value = main_subtask

        # First call to Job.fetch returns the main job, second call returns the dependent job
        mock_main_job = MagicMock()
        mock_main_job.get_status.return_value = "failed"
        mock_main_job.dependent_ids = [dependent_job_id]

        mock_dependent_job = MagicMock()
        mock_dependent_job.get_status.return_value = "failed"
        mock_dependent_job.dependent_ids = []

        def fetch_side_effect(job_id, connection=None):
            if job_id == "rq-job-main":
                return mock_main_job
            return mock_dependent_job

        mock_fetch.side_effect = fetch_side_effect

        # Override _get for recursive calls to return the dependent subtask
        call_count = [0]

        def get_side_effect(db, id):
            call_count[0] += 1
            if call_count[0] == 1:
                return main_subtask
            return dependent_subtask

        mock_get.side_effect = get_side_effect

        request = create_mock_request(active_user)
        self.crud.retry(db_session, request, main_subtask.id)

        # Main job should be requeued
        mock_main_job.requeue.assert_called_once()
