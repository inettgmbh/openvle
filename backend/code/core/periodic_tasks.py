import logging
from datetime import datetime, timedelta, timezone

from controllers.base import CRUDBase
from controllers.events import CRUDEvent
from controllers.mails import CRUDMail
from models import (
    Event,
    EventStatus,
    Mail,
    MailAction,
    MailTemplate,
    SubTask,
    Task,
    User,
)

from .config import Settings
from .mariadb import SessionLocal

settings = Settings()
logger = logging.getLogger(__name__)


def check_for_event_mail_simple(db, event_id, mail_action_slug):
    """
    Check if a specific mail type has already been sent for this event.
    Returns True if mail exists and was sent successfully.
    """
    from sqlalchemy import exists

    # Check if a Mail exists for this event with this mail action that was successfully sent
    mail_exists = db.query(
        exists()
        .where(Mail.event == event_id)
        .where(Mail.templateId == MailTemplate.id)
        .where(MailTemplate.mail_action == MailAction.id)
        .where(MailAction.slug == mail_action_slug)
        .where(
            Mail.sendStatus.in_(["sent", "queued"])
        )  # Either sent or currently queued
    ).scalar()

    return mail_exists


# Events periodic task
def events_periodic():
    """Periodic task for Events.
    This task will be run daily to check for any Events that are due to start.
    This is determined according to the .env variable EVENTS_PREP_TIME (in days). The task checks all events and if
    they are due to start and triggers the CRUDEvent.actions_start function to start the Event (if all function requirements are met)"""

    # Set db variable to MariaDB session
    try:
        db = SessionLocal()
    except:
        return "Unable to connect to MariaDB"

    try:
        from controllers.sub_tasks import CRUDSubTask

        sub_task = (
            db.query(SubTask)
            .filter(SubTask.job_id == "core_events_periodic")
            .first()
        )
        CRUDSubTask(SubTask).worker_process_start(db, sub_task.id)
        # Get list of all Event objects in database
        events_all = db.query(Event).all()
        if not events_all:
            return CRUDSubTask(SubTask).worker_process_success(
                sub_task.id, 200, "No Events found in DB", db
            )
        today = datetime.now().date()
        events_triggered = []

        # Batch-load all EventStatus objects as a dict
        all_statuses = {s.id: s for s in db.query(EventStatus).all()}

        for event in events_all:
            # Get EventStatus for event
            event_status = all_statuses.get(event.status)
            if not event_status:
                continue  # Skip Event if EventStatus does not exist (Edge case that _SHOULD NOT_ happen)

            match event_status.name:
                # Handling of "Geplant" Events
                case "Geplant":
                    # Minus 1 week from Event.dateStart to get date on which the Event is to be automatically started
                    PRE_START_EVENT_DATE = event.dateStart - timedelta(
                        days=settings.events_start_prep_time_days
                    )
                    PRE_START_EVENT_DATE = PRE_START_EVENT_DATE
                    # Case: Too early to start
                    if today < PRE_START_EVENT_DATE:
                        # Calculate when the pre-start notification should be sent
                        pre_start_notif_date = event.dateStart - timedelta(
                            days=settings.events_start_prep_time_days
                        )
                        # Check if today is in the range from pre_start_notif_date to EVENT_START_DATE
                        if (
                            pre_start_notif_date
                            <= today
                            <= PRE_START_EVENT_DATE
                        ):
                            # Check if any events_pre_start Mails were already sent successfully
                            eps_mail = check_for_event_mail_simple(
                                db=db,
                                event_id=event.id,
                                mail_action_slug="events_pre_start",
                            )
                            if not eps_mail:
                                # Send Mail to Event admin
                                events_triggered.append(
                                    (event.id, "pre_start_mail")
                                )
                                event_admin = CRUDEvent(Event).get_event_admin(
                                    db=db, id=event.id
                                )
                                admin_user_ids = [
                                    ea.user_id for ea in event_admin
                                ]
                                admin_users = {
                                    u.id: u
                                    for u in db.query(User)
                                    .filter(User.id.in_(admin_user_ids))
                                    .all()
                                }
                                for eu in event_admin:
                                    user = admin_users.get(eu.user_id)
                                    if not user:
                                        continue
                                    new_mail = CRUDMail(
                                        Mail
                                    ).create_system_mail(
                                        db=db,
                                        user=user,
                                        context_objects=[event],
                                        mail_action_slug="events_pre_start",
                                        event_id=event.id,
                                    )
                    # Case: Due to start
                    elif today > PRE_START_EVENT_DATE:
                        # Start Event
                        try:
                            CRUDEvent(Event).actions_start(
                                db=db, request=None, id=event.id
                            )
                            events_triggered.append((event.id, "started"))
                        except Exception as exc:
                            event_status_core_error = CRUDBase(
                                EventStatus
                            )._get_by_name(db, "Core Fehler")
                            event.status = event_status_core_error.id
                            event.deployment_status = f"The following error occurred while trying to start the event: {exc.detail}"[
                                :500
                            ]
                            db.add(event)
                            db.commit()

                # Handling of "Aktiv" Events
                case "Aktiv":
                    # Add 1 week to Event.dateEnd to get date on which the Event is to be automatically archived
                    POST_END_EVENT_DATE = event.dateEnd + timedelta(
                        days=settings.events_end_prep_time_days
                    )
                    POST_END_EVENT_DATE = POST_END_EVENT_DATE
                    # Case: Too early to end
                    if today < POST_END_EVENT_DATE:
                        # Get required dates
                        pre_end_notif_date = event.dateEnd - timedelta(
                            days=settings.events_end_prep_time_days
                        )
                        if pre_end_notif_date <= today <= POST_END_EVENT_DATE:
                            # Check if admin pre-end mails were already sent
                            admin_mail_sent = check_for_event_mail_simple(
                                db=db,
                                event_id=event.id,
                                mail_action_slug="events_pre_end_admin",
                            )
                            if not admin_mail_sent:
                                # Send Mail to Event admin
                                events_triggered.append(
                                    (event.id, "pre_end_mail_admin")
                                )
                                event_admin = CRUDEvent(Event).get_event_admin(
                                    db=db, id=event.id
                                )
                                admin_user_ids = [
                                    ea.user_id for ea in event_admin
                                ]
                                admin_users = {
                                    u.id: u
                                    for u in db.query(User)
                                    .filter(User.id.in_(admin_user_ids))
                                    .all()
                                }
                                for eu in event_admin:
                                    user = admin_users.get(eu.user_id)
                                    if not user:
                                        continue
                                    new_mail = CRUDMail(
                                        Mail
                                    ).create_system_mail(
                                        db=db,
                                        user=user,
                                        context_objects=[event],
                                        mail_action_slug="events_pre_end_admin",
                                        event_id=event.id,
                                    )

                            # Check if student pre-end mails were already sent
                            student_mail_sent = check_for_event_mail_simple(
                                db=db,
                                event_id=event.id,
                                mail_action_slug="events_pre_end_student",
                            )
                            if not student_mail_sent:
                                # Send mail to students notifying them of impending VM loss
                                events_triggered.append(
                                    (event.id, "pre_end_mail_student")
                                )
                                event_students = CRUDEvent(
                                    Event
                                ).get_event_students(db=db, id=event.id)
                                student_user_ids = [
                                    s.user_id for s in event_students
                                ]
                                student_users = {
                                    u.id: u
                                    for u in db.query(User)
                                    .filter(User.id.in_(student_user_ids))
                                    .all()
                                }
                                for student in event_students:
                                    user = student_users.get(student.user_id)
                                    if not user:
                                        continue
                                    new_mail = CRUDMail(
                                        Mail
                                    ).create_system_mail(
                                        db=db,
                                        user=user,
                                        context_objects=[event],
                                        mail_action_slug="events_pre_end_student",
                                        event_id=event.id,
                                    )
                    # Case: Due to end
                    elif today > POST_END_EVENT_DATE:
                        # End Event
                        try:
                            CRUDEvent(Event).actions_stop(
                                db=db, request=None, id=event.id
                            )
                            events_triggered.append((event.id, "ended"))
                        except Exception as exc:
                            event.deployment_status = f"The following error occurred while trying to end the event: {exc.detail}"[
                                :500
                            ]
                            db.add(event)
                            db.commit()

        response_message = (
            "No automated actions were triggered for Events"
            if not events_triggered
            else f"The following Event actions were triggered: {events_triggered}"
        )

        return CRUDSubTask(SubTask).worker_process_success(
            sub_task.id, 200, response_message, db
        )
    finally:
        db.close()


def mail_periodic_delete():
    # Set db variable to MariaDB session
    try:
        db = SessionLocal()
    except:
        return "Unable to connect to MariaDB"

    try:
        from controllers.sub_tasks import CRUDSubTask

        sub_task = (
            db.query(SubTask)
            .filter(SubTask.job_id == "core_mail_periodic_delete")
            .first()
        )
        CRUDSubTask(SubTask).worker_process_start(db, sub_task.id)
        # Get all Mails older than value set in .env
        cutoff = datetime.now(timezone.utc) - timedelta(
            weeks=settings.mail_max_age_weeks
        )
        mails_to_delete = db.query(Mail).filter(Mail.createdAt < cutoff).all()
        if not mails_to_delete:
            return CRUDSubTask(SubTask).worker_process_success(
                sub_task.id, 200, "No expired Mail objects found in DB", db
            )

        for mail in mails_to_delete:
            db.delete(mail)
        db.commit()
        CRUDSubTask(SubTask).worker_process_success(
            sub_task.id, 200, "Expired Mail objects have been deleted", db
        )
    except Exception:
        return CRUDSubTask(SubTask).worker_process_fail(
            sub_task.id,
            400,
            "An unexpected error occured while trying to delete expired Mail objects",
            db,
        )
    finally:
        db.close()


def tasks_enqueue():
    """Create Task and SubTask DB entries for periodic jobs (if they don't
    exist yet).  Scheduling is handled by the ``rq cron`` scheduler
    container — this function only ensures the tracking rows are present."""

    from controllers.sub_tasks import CRUDSubTask
    from controllers.tasks import CRUDTask
    from schemas.sub_tasks import SubTaskCreate
    from schemas.tasks import TaskCreate

    try:
        db = SessionLocal()
    except Exception:
        return "Unable to connect to MariaDB"

    try:
        for task_name, obj_type, job_id, action in [
            (
                "Periodic: proxmox_node_info_periodic",
                "System",
                "proxmox_node_info_periodic",
                "periodic_update",
            ),
            (
                "Periodic: core_events_periodic",
                "Event",
                "core_events_periodic",
                "periodic_update",
            ),
            (
                "Periodic: core_mail_periodic_delete",
                "Mail",
                "core_mail_periodic_delete",
                "periodic_delete",
            ),
        ]:
            try:
                parent = db.query(Task).filter(Task.name == task_name).first()
                if not parent:
                    parent = CRUDTask(Task).create(
                        db=db, obj_in=TaskCreate(name=task_name)
                    )
                child = (
                    db.query(SubTask).filter(SubTask.name == task_name).first()
                )
                if not child:
                    CRUDSubTask(SubTask).create(
                        db=db,
                        obj_in=SubTaskCreate(
                            name=task_name,
                            object_type=obj_type,
                            job_id=job_id,
                            parent_task=parent.id,
                            action=action,
                        ),
                        request=None,
                    )
                logger.info("%s DB entries ensured", task_name)
            except Exception:
                logger.exception(
                    "Could not create DB entries for %s", task_name
                )
    finally:
        db.close()
