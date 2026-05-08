import builtins
import contextlib
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from rq.job import Job
from sqlalchemy.orm import Session

from core.config import Settings
from core.exceptions import BadRequestError
from core.mariadb import SessionLocal
from core.redis import (
    queue_core_periodic,
    queue_guacamole,
    queue_mails,
    queue_pve_periodic,
    redis_connection,
)
from middlewares.i18n import _
from models import Event, EventStatus, SubTask, Task
from pve.worker_utils import TaskException
from schemas.sub_tasks import SubTaskCreate, SubTaskUpdate

from .base import CRUDBase

settings = Settings()


class CRUDSubTask(CRUDBase[SubTask, SubTaskCreate, SubTaskUpdate]):
    # Create SubTask
    def create(
        self, db: Session, request: Request = None, *, obj_in: SubTaskCreate
    ) -> SubTask:
        obj_in_data = jsonable_encoder(obj_in)
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        if hasattr(obj_in, "object_id"):
            self.db_obj.object_id = obj_in.object_id
        self.db_obj.parent_task = obj_in.parent_task
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    def worker_process_start(self, db: Session, id: Any):
        self.db_obj = self._get(db, id)
        if not self.db_obj:
            raise TaskException("Unable to retrieve task object from database")
        self.db_obj.status = "processing"
        if not self.db_obj.action.startswith("periodic"):
            self.db_obj.attempt = int(self.db_obj.attempt) + 1
        self.db_obj = self._commit(db, self.db_obj)
        return True

    def worker_process_success(
        self,
        id: Any,
        response_code: int,
        response_message: str,
        db: Session = None,
    ):
        from core.mail_automated import system_triggered_mail_handler

        if not db:
            db = SessionLocal()
        self.db_obj = self._get(db, id)
        if not self.db_obj:
            db.close()
            return True
        self.db_obj.status = "success"
        self.db_obj.response_code = response_code
        self.db_obj.response_message = response_message
        self.db_obj = self._commit(db, self.db_obj)
        # Pass SubTask to system_triggered_mail_handler
        with contextlib.suppress(Exception):
            system_triggered_mail_handler(self.db_obj.id)

        def check_all_success(sub_tasks_all) -> bool:
            return all(
                sub_task.status == "success" for sub_task in sub_tasks_all
            )

        # Check if all SubTasks are completed for parent Task
        try:
            sub_tasks_all = (
                db.query(SubTask)
                .filter(SubTask.parent_task == self.db_obj.parent_task)
                .all()
            )
            if check_all_success(sub_tasks_all):
                parent_task = db.get(Task, self.db_obj.parent_task)
                parent_task.status = "success"
                db.add(parent_task)
                db.commit()
                db.refresh(parent_task)
        except:
            db.close()
            raise TaskException(
                "Worker utility 'kvs_task_success' was unable to update parent Task with status 'success'"
            )
        db.close()
        return True

    def worker_process_fail(
        self,
        id: Any,
        response_code: int,
        response_message: str,
        db: Session = None,
        force_fail: bool = False,
    ):
        from core.mail_automated import system_triggered_mail_handler

        # Enforce max length for response_message
        if response_message and len(response_message) > 500:
            response_message = response_message[:497] + "..."
        if not db:
            db = SessionLocal()
        self.db_obj = self._get(db, id)
        if not self.db_obj:
            db.close()
            raise TaskException(response_message)
        self.db_obj.status = "failed"
        self.db_obj.response_code = response_code
        self.db_obj.response_message = response_message
        self.db_obj = self._commit(db, self.db_obj)
        # Check if current attempt exceeds max attempts, or if forced to fail immediately
        if force_fail or int(self.db_obj.attempt) >= int(
            settings.worker_max_retry
        ):
            parent_task = db.get(Task, self.db_obj.parent_task)
            parent_task.status = "failed"
            # Check related Event status and update if subtask effects status
            if parent_task.event_id and self.db_obj.object_type != "Mail":
                event = db.get(Event, parent_task.event_id)
                event_status = db.get(EventStatus, event.status)
                if event_status.name in ["Deploying", "Archiving"]:
                    error_status_name = (
                        "Deployment Fehler"
                        if event_status.name == "Deploying"
                        else "Archival Fehler"
                    )
                    event_status_error = CRUDBase(EventStatus)._get_by_name(
                        db, error_status_name
                    )
                    event.status = event_status_error.id
                    db.add(event)

            db.add(parent_task)
            db.commit()
            db.refresh(parent_task)
            # Pass SubTask to system_triggered_mail_handler
            with contextlib.suppress(Exception):
                system_triggered_mail_handler(self.db_obj.id)
        db.close()
        raise TaskException(response_message) from None

    def retry(self, db: Session, request: Request, id: Any):
        subtask = self._get(db, id)

        # Check if this is a periodic task (action == "periodic_update" or "periodic_delete")
        is_periodic = subtask.action in ["periodic_update", "periodic_delete"]
        if is_periodic:
            # For periodic tasks, enqueue an immediate one-off execution.
            # The cron scheduler continues to handle the regular schedule.
            _periodic_jobs = {
                "proxmox_node_info_periodic": (
                    queue_pve_periodic,
                    "pve.pve_node_info.proxmox_node_info_periodic",
                ),
                "core_events_periodic": (
                    queue_core_periodic,
                    "core.periodic_tasks.events_periodic",
                ),
                "core_mail_periodic_delete": (
                    queue_core_periodic,
                    "core.periodic_tasks.mail_periodic_delete",
                ),
            }
            entry = _periodic_jobs.get(subtask.job_id)
            if not entry:
                raise BadRequestError(
                    message=_("Unknown periodic task: {job_id}").format(
                        job_id=subtask.job_id
                    )
                )
            queue, func_path = entry
            import importlib

            mod_path, func_name = func_path.rsplit(".", 1)
            func = getattr(importlib.import_module(mod_path), func_name)
            queue.enqueue(func, result_ttl=-1)

            subtask.status = "queued"
            subtask.attempt = 0
            subtask.updatedById = request.user.id
            db.add(subtask)
            db.commit()
            return subtask

        # Non-periodic SubTask handling
        try:
            job = Job.fetch(subtask.job_id, connection=redis_connection)
        except Exception:
            raise BadRequestError(
                message=_(
                    "{subtask} job could not be found in Redis queue."
                ).format(subtask=subtask.action)
            )
        # If the job has failed and has no other job depending on it, update SubTask and requeue Job
        if job.get_status() == "failed":
            subtask.status = "queued"
            subtask.attempt = 0
            subtask.updatedById = request.user.id
            job.requeue()
            db.add(subtask)
            db.commit()
        if job.dependent_ids:
            # If the job has dependencies, retry dependents first
            for dependent_job in job.dependent_ids:
                db_subtask = (
                    db.query(SubTask)
                    .filter(SubTask.job_id == dependent_job)
                    .first()
                )
                with contextlib.suppress(builtins.BaseException):
                    self.retry(db, request, db_subtask.id)

        return subtask


sub_task = CRUDSubTask(SubTask)
