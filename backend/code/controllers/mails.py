import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from pydantic import UUID4
from rq import Retry
from sqlalchemy.orm import Session

from core.config import Settings
from core.core_utils import get_system_user
from core.exceptions import (
    JobEnqueueError,
    MailSubjectSlugRenderError,
    ObjectNotFound,
)
from core.redis import queue_mails
from models import (
    Event,
    Language,
    Mail,
    MailAction,
    MailTemplate,
    SubTask,
    Task,
    User,
)
from schemas.mails import MailCreate
from schemas.tasks import TaskCreate

from .base import CRUDBase
from .mails_actions import CRUDMailAction
from .tasks import CRUDTask

settings = Settings()

# Matches {{event.slug}} with any amount of whitespace inside the braces
_SUBJECT_SLUG_PLACEHOLDER_RE = re.compile(r"\{\{\s*event\.slug\s*\}\}")


class CRUDMail(CRUDBase[Mail, MailCreate, MailCreate]):
    # Send Mail based on MailTemplate and context objects - User triggered
    def create(
        self,
        db: Session,
        request: Request,
        *,
        obj_in: MailCreate,
        context_objects: list = None,
        event_id: Any = None,
    ) -> Mail:
        obj_in_data = jsonable_encoder(obj_in)
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        mail_template = CRUDBase(MailTemplate).get(db, obj_in.templateId)
        self.db_obj.templateId = mail_template.id
        if obj_in.user_id:
            self.db_obj.user_id = obj_in.user_id
        self.db_obj.sendStatus = "queued"
        # Assign event if provided
        if event_id:
            self.db_obj.event = event_id
        self.db_obj = self._commit(db, self.db_obj)
        job_send = self._task_mail_send(
            db=db,
            request=request,
            context_objects=context_objects,
            event_id=event_id,
        )
        return self.db_obj

    # Send Mail based on MailAction and context objects - System triggered
    def create_system_mail(
        self,
        db: Session,
        *,
        mail_action_slug: str,
        user: User,
        context_objects: list = None,
        event_id: Any = None,
    ):
        if context_objects is None:
            context_objects = []
        # Get MailAction
        mail_action = CRUDMailAction(MailAction).get_by_slug(
            db=db, slug=mail_action_slug
        )
        if not mail_action:
            raise ObjectNotFound(
                slug=mail_action_slug, model_name=self.model.__name__
            )
        # Get MailTemplate related to MailAction and language of User
        user_language = (
            db.query(Language).filter(Language.key == user.locale).first()
        )
        mail_template = (
            db.query(MailTemplate)
            .filter(
                MailTemplate.language == user_language.id,
                MailTemplate.mail_action == mail_action.id,
            )
            .first()
        )
        if not mail_template:
            # If no MailTemplate exists for langauge, return default language version (German)
            default_language = (
                db.query(Language).filter(Language.key == "de_DE").first()
            )
            mail_template = (
                db.query(MailTemplate)
                .filter(
                    MailTemplate.language == default_language.id,
                    MailTemplate.mail_action == mail_action.id,
                )
                .first()
            )
            if not mail_template:
                return None
        subject = mail_template.subject
        if _SUBJECT_SLUG_PLACEHOLDER_RE.search(subject):
            if not event_id:
                raise MailSubjectSlugRenderError()
            event = db.get(Event, event_id)
            if not event:
                raise MailSubjectSlugRenderError()
            subject = _SUBJECT_SLUG_PLACEHOLDER_RE.sub(event.slug, subject)
        new_mail_schema = MailCreate(
            toMail=user.email,
            user_id=user.id,
            subject=subject,
            fromName=settings.smtp_from_name,
            fromMail=settings.smtp_from_mail,
            replyTo=settings.smtp_from_mail,
            templateId=mail_template.id,
        )
        obj_in_data = jsonable_encoder(new_mail_schema)
        self._initialize_object_fields(db=db, obj_data_in=obj_in_data)
        self.db_obj.templateId = mail_template.id
        self.db_obj.user_id = user.id
        self.db_obj.sendStatus = "queued"
        # Assign event if provided
        if event_id:
            self.db_obj.event = event_id
        self.db_obj = self._commit(db, self.db_obj)

        job_send = self._task_mail_send(
            db=db, context_objects=context_objects, event_id=event_id
        )
        return self.db_obj

    def resend(
        self, db: Session, request: Request, *, kvs_subtask_object_id: UUID4
    ) -> Any:
        from core.mail_worker import mail_worker_send

        # Get task object
        task_object = db.get(SubTask, kvs_subtask_object_id)
        if not task_object:
            raise HTTPException(
                status_code=404,
                detail=f"SubTask object with ID: {kvs_subtask_object_id} not found.",
            )
        # TODO: KVS-445
        # Check if SubTask.object_type is Mail
        if task_object.object_type != "Mail":
            raise HTTPException(
                status_code=422,
                detail=f"Retrying of SubTasks with object_type '{task_object.object_type}' not yet supported.",
            )
        task_object.status = "queued"
        task_object.attempt = 0
        task_object.updatedById = request.user.id
        db.add(task_object)
        # Get related Mail object
        mail_object = db.get(Mail, uuid.UUID(task_object.object_id))
        if not mail_object:
            raise HTTPException(
                status_code=404,
                detail=f"Mail object with ID: {task_object.object_id} not found.",
            )
        mail_object.status = "queued"
        mail_object.updatedById = request.user.id
        db.add(mail_object)
        check = queue_mails.enqueue(
            mail_worker_send,
            kvs_task_object_id=task_object.id,
            kvs_mail_id=mail_object.id,
        )
        if not check:
            raise HTTPException(
                status_code=400, detail="Unable to add mails_send job to queue"
            )
        db.commit()
        db.refresh(task_object)
        return task_object

    def _task_mail_send(
        self,
        db: Session,
        request: Request = None,
        context_objects: list = None,
        event_id: Any = None,
    ):
        from core.mail_worker import mail_worker_send

        # Create Task object
        task_name = "Send mail"
        if event_id:
            event = db.get(Event, event_id)
            task_name += f" for Event {event.name}"
        new_task = CRUDTask(Task).create(
            db=db,
            request=request,
            obj_in=TaskCreate(name=task_name, event_id=event_id),
        )
        # Create SubTask objects and enqueue job (SEND)
        sub_task_send = SubTask(
            id=uuid.uuid4(),
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
            status="queued",
            createdById=get_system_user(db).id
            if not request
            else request.user.id,
            updatedById=get_system_user(db).id
            if not request
            else request.user.id,
            name="Send mail",
            object_type="Mail",
            object_id=self.db_obj.id,
            action="mails_send",
            attempt=0,
            parent_task=new_task.id,
        )
        db.add(sub_task_send)
        db.commit()
        db.refresh(sub_task_send)
        if context_objects:
            job_send = queue_mails.enqueue(
                mail_worker_send,
                kvs_task_object_id=sub_task_send.id,
                kvs_mail_id=self.db_obj.id,
                context_objects=context_objects,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_send = queue_mails.enqueue(
                mail_worker_send,
                kvs_task_object_id=sub_task_send.id,
                kvs_mail_id=self.db_obj.id,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_send:
            raise JobEnqueueError(job_key="mails_send")
        return job_send


mail = CRUDMail(Mail)
