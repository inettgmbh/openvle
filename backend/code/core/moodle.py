"""
Moodle Business Logic + Worker Functions
"""

import contextlib
import logging

from pydantic import UUID4

from controllers.sub_tasks import CRUDSubTask
from core.core_utils import db_save
from core.mariadb import SessionLocal
from models import (
    Course,
    Event,
    EventsUser,
    Role,
    SubTask,
    User,
)

from .config import Settings
from .exceptions import MoodleConnectionError
from .moodlelib import MoodleAPIError, MoodleClient

logger = logging.getLogger(__name__)

settings = Settings()

# Moodle role ID mapping
ROLE_MAP = {
    "lehrende": 3,  # editingteacher
    "studierende": 5,  # student
}


def moodle_connect(
    timeout: int | None = None,
) -> MoodleClient | bool:
    """Connect to Moodle API and validate the token.

    Args:
        timeout: Optional timeout override in seconds.
                 Defaults to settings.moodle_timeout.

    Returns:
        MoodleClient instance on success, False on failure.
    """
    try:
        client = MoodleClient(
            url=settings.moodle_url,
            token=settings.moodle_token,
            verify_ssl=settings.moodle_verify_ssl,
            timeout=timeout or settings.moodle_timeout,
        )
        client.get_site_info()
        return client
    except Exception:
        return False


def resolve_moodle_user(
    moodle: MoodleClient,
    email: str,
    username: str,
    match_field: str = "email",
) -> int | None:
    """Find a Moodle user by email or username.

    Args:
        moodle: MoodleClient instance.
        email: User's email address.
        username: User's username.
        match_field: Field to match on ('email' or 'username').

    Returns:
        Moodle user ID if found, None otherwise.
    """
    value = email if match_field == "email" else username
    try:
        users = moodle.get_users_by_field(match_field, [value])
        if users and len(users) > 0:
            return users[0]["id"]
    except MoodleAPIError as e:
        logger.warning(
            f"Failed to resolve Moodle user "
            f"({match_field}={value}): {e.message}"
        )
    return None


# ------------------------------------------------------------------
# Event-Lifecycle Functions
# ------------------------------------------------------------------


def ensure_moodle_user(moodle: MoodleClient, user: User) -> int:
    """Find or create a Moodle user for the given KVS user.

    Args:
        moodle: Active MoodleClient instance.
        user: KVS User model instance.

    Returns:
        Moodle user ID.

    Raises:
        MoodleAPIError: If user creation fails.
    """
    match_field = settings.moodle_user_match_field
    value = user.email if match_field == "email" else user.username

    # Try to find existing user
    users = moodle.get_users_by_field(match_field, [value])
    if users and len(users) > 0:
        return users[0]["id"]

    # Create user in Moodle
    # Note: preferences must bypass create_users() serialisation
    # because it wraps keys as users[0][key] which would mangle
    # nested bracket notation.
    firstname = user.name.split(" ")[0] if user.name else user.username
    lastname = (
        " ".join(user.name.split(" ")[1:])
        if user.name and len(user.name.split(" ")) > 1
        else user.username
    )
    params = {
        "users[0][username]": user.username.lower(),
        "users[0][firstname]": firstname,
        "users[0][lastname]": lastname,
        "users[0][email]": user.email,
        "users[0][auth]": settings.moodle_user_auth,
        "users[0][createpassword]": 0,
        "users[0][maildisplay]": 0,
    }
    new_users = moodle._call("core_user_create_users", **params)
    if not new_users or len(new_users) == 0:
        raise MoodleAPIError(
            error_code="user_create_failed",
            message=f"Failed to create Moodle user for {user.username}",
        )
    return new_users[0]["id"]


def moodle_deploy_course_worker(
    kvs_event_id: UUID4,
    kvs_task_object_id: UUID4,
):
    """Async worker (BLOCKER): Duplicate Moodle course for event
    and enrol all participants.

    Steps:
    1. Duplicate course from course.moodleCourseId
    2. Set event.moodleCourseId = new course ID
    3. Enrol all EventsUsers
    """
    db = None
    moodle = None
    try:
        db = SessionLocal()
        moodle = moodle_connect()
        if not moodle:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                502,
                "Failed to connect to Moodle",
            )
    except Exception:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            502,
            "Failed to initialize Moodle connection",
        )

    CRUDSubTask(SubTask).worker_process_start(db, kvs_task_object_id)

    try:
        event = db.get(Event, kvs_event_id)
        if not event:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id, 404, "Event not found"
            )

        course = db.get(Course, event.course)
        if not course or not course.moodleCourseId:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                400,
                "Course has no moodleCourseId template",
            )

        # Step 1: Get source course info for categoryid
        source_courses = moodle.get_courses([course.moodleCourseId])
        categoryid = source_courses[0]["categoryid"] if source_courses else 1

        # Step 2: Duplicate course
        fullname = f"{event.name} ({event.slug})"
        result = moodle.duplicate_course(
            course_id=course.moodleCourseId,
            fullname=fullname,
            shortname=event.slug,
            categoryid=categoryid,
            visible=settings.moodle_course_visible,
        )
        new_moodle_id = result["id"]

        # Step 3: Save moodleCourseId on event
        event.moodleCourseId = new_moodle_id
        db_save(db, event)

        # Step 4: Enrol all EventsUsers
        event_users = (
            db.query(EventsUser)
            .filter(EventsUser.event_id == kvs_event_id)
            .all()
        )
        enrolments = []
        for eu in event_users:
            user = db.get(User, eu.user_id)
            role = db.get(Role, eu.role_id)
            if not user or not role:
                continue
            try:
                moodle_user_id = ensure_moodle_user(moodle, user)
            except MoodleAPIError as e:
                logger.warning(
                    f"Could not ensure Moodle user for "
                    f"{user.username}: {e.message}"
                )
                continue
            moodle_role_id = ROLE_MAP.get(role.key, 5)
            enrolments.append(
                {
                    "roleid": moodle_role_id,
                    "userid": moodle_user_id,
                    "courseid": new_moodle_id,
                }
            )

        if enrolments:
            moodle.enrol_users(enrolments)

        return CRUDSubTask(SubTask).worker_process_success(
            kvs_task_object_id,
            200,
            f"Moodle course deployed (id={new_moodle_id}), "
            f"{len(enrolments)} users enrolled",
        )

    except MoodleAPIError as e:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            400,
            f"Moodle API error during deploy: {e.message}",
        )
    except Exception as e:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            500,
            f"Unexpected error during Moodle deploy: {e}",
        )
    finally:
        if moodle:
            moodle.close()
        if db:
            db.close()


def moodle_enrol_user_worker(
    kvs_event_id: UUID4,
    kvs_user_id: UUID4,
    kvs_role_key: str,
    kvs_task_object_id: UUID4,
):
    """Async worker: Enrol a single user into the event's Moodle course."""
    db = None
    moodle = None
    try:
        db = SessionLocal()
        moodle = moodle_connect()
        if not moodle:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                502,
                "Failed to connect to Moodle",
            )
    except Exception:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            502,
            "Failed to initialize Moodle connection",
        )

    CRUDSubTask(SubTask).worker_process_start(db, kvs_task_object_id)

    try:
        event = db.get(Event, kvs_event_id)
        if not event or not event.moodleCourseId:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                400,
                "Event not found or has no moodleCourseId",
            )

        user = db.get(User, kvs_user_id)
        if not user:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id, 404, "User not found"
            )

        moodle_user_id = ensure_moodle_user(moodle, user)
        moodle_role_id = ROLE_MAP.get(kvs_role_key, 5)

        moodle.enrol_users(
            [
                {
                    "roleid": moodle_role_id,
                    "userid": moodle_user_id,
                    "courseid": event.moodleCourseId,
                }
            ]
        )
        return CRUDSubTask(SubTask).worker_process_success(
            kvs_task_object_id,
            200,
            f"User {user.username} enrolled in Moodle course "
            f"{event.moodleCourseId}",
        )

    except MoodleAPIError as e:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            400,
            f"Moodle API error during enrolment: {e.message}",
        )
    except Exception as e:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            500,
            f"Unexpected error during Moodle enrolment: {e}",
        )
    finally:
        if moodle:
            moodle.close()
        if db:
            db.close()


def moodle_unenrol_user_worker(
    kvs_event_id: UUID4,
    kvs_user_id: UUID4,
    kvs_role_key: str,
    kvs_task_object_id: UUID4,
):
    """Async worker: Unenrol a user from the event's Moodle course."""
    db = None
    moodle = None
    try:
        db = SessionLocal()
        moodle = moodle_connect()
        if not moodle:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                502,
                "Failed to connect to Moodle",
            )
    except Exception:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            502,
            "Failed to initialize Moodle connection",
        )

    CRUDSubTask(SubTask).worker_process_start(db, kvs_task_object_id)

    try:
        event = db.get(Event, kvs_event_id)
        if not event or not event.moodleCourseId:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                400,
                "Event not found or has no moodleCourseId",
            )

        user = db.get(User, kvs_user_id)
        if not user:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id, 404, "User not found"
            )

        match_field = settings.moodle_user_match_field
        moodle_user_id = resolve_moodle_user(
            moodle, user.email, user.username, match_field
        )
        if not moodle_user_id:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                404,
                f"Moodle user not found for {user.username}",
            )

        moodle_role_id = ROLE_MAP.get(kvs_role_key, 5)
        moodle.unenrol_users(
            [
                {
                    "roleid": moodle_role_id,
                    "userid": moodle_user_id,
                    "courseid": event.moodleCourseId,
                }
            ]
        )
        return CRUDSubTask(SubTask).worker_process_success(
            kvs_task_object_id,
            200,
            f"User {user.username} unenrolled from Moodle "
            f"course {event.moodleCourseId}",
        )

    except MoodleAPIError as e:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            400,
            f"Moodle API error during unenrol: {e.message}",
        )
    except Exception as e:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            500,
            f"Unexpected error during Moodle unenrol: {e}",
        )
    finally:
        if moodle:
            moodle.close()
        if db:
            db.close()


def moodle_end_event_worker(
    kvs_event_id: UUID4,
    kvs_task_object_id: UUID4,
):
    """Async worker (BLOCKER): End Moodle course for event.

    Steps:
    a. Unenrol all students
    b. Leave teacher enrolments unchanged
    c. Set course visibility to hidden
    """
    db = None
    moodle = None
    try:
        db = SessionLocal()
        moodle = moodle_connect()
        if not moodle:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                502,
                "Failed to connect to Moodle",
            )
    except Exception:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            502,
            "Failed to initialize Moodle connection",
        )

    CRUDSubTask(SubTask).worker_process_start(db, kvs_task_object_id)

    try:
        event = db.get(Event, kvs_event_id)
        if not event or not event.moodleCourseId:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                400,
                "Event has no moodleCourseId",
            )

        moodle_course_id = event.moodleCourseId
        match_field = settings.moodle_user_match_field

        # Get student role
        role_student = db.query(Role).filter(Role.key == "studierende").first()

        # Unenrol students
        unenrol_count = 0
        if role_student:
            student_event_users = (
                db.query(EventsUser)
                .filter(
                    EventsUser.event_id == kvs_event_id,
                    EventsUser.role_id == role_student.id,
                )
                .all()
            )
            for eu in student_event_users:
                user = db.get(User, eu.user_id)
                if not user:
                    continue
                moodle_user_id = resolve_moodle_user(
                    moodle, user.email, user.username, match_field
                )
                if not moodle_user_id:
                    continue
                try:
                    moodle.unenrol_users(
                        [
                            {
                                "roleid": ROLE_MAP["studierende"],
                                "userid": moodle_user_id,
                                "courseid": moodle_course_id,
                            }
                        ]
                    )
                    unenrol_count += 1
                except MoodleAPIError as e:
                    logger.warning(
                        f"Failed to unenrol {user.username} "
                        f"from Moodle course {moodle_course_id}: "
                        f"{e.message}"
                    )

        # Set course to hidden
        moodle.update_courses(
            [
                {
                    "id": moodle_course_id,
                    "visible": 0,
                }
            ]
        )

        return CRUDSubTask(SubTask).worker_process_success(
            kvs_task_object_id,
            200,
            f"Moodle event ended: {unenrol_count} students unenrolled, "
            f"course hidden",
        )

    except MoodleAPIError as e:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            400,
            f"Moodle API error during event end: {e.message}",
        )
    except Exception as e:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            500,
            f"Unexpected error during Moodle event end: {e}",
        )
    finally:
        if moodle:
            moodle.close()
        if db:
            db.close()


def moodle_delete_course(moodle_course_id: int):
    """Sync: Delete a Moodle course (if config allows).

    Args:
        moodle_course_id: The Moodle course ID to delete.
    """
    if not settings.moodle_enabled:
        return
    if not settings.moodle_delete_course_on_event_delete:
        return

    moodle = None
    try:
        moodle = moodle_connect()
        if not moodle:
            return
        moodle.delete_courses([moodle_course_id])
    except Exception as e:
        logger.warning(
            f"Failed to delete Moodle course {moodle_course_id}: {e}"
        )
    finally:
        if moodle:
            moodle.close()
