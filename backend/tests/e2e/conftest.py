"""
E2E workflow test fixtures.

Provides multi-step test helpers: pre-built courses, templates, events,
teacher/student users with JWT headers, and a login-capable user.

Re-exports integration fixtures (client, auth_headers, etc.) so that
tests under tests/e2e/ can use them without being nested inside
tests/integration/.
"""

import uuid
from datetime import date, datetime, time, timezone

import pytest

from tests.helpers.auth_helpers import create_test_token

# Re-export integration fixtures so pytest discovers them here.
from tests.integration.conftest import (  # noqa: F401
    API,
    admin_headers,
    admin_user,
    auth_headers,
    client,
    expired_auth_headers,
)


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------


def _set_event_status(db_session, event, status_name, event_statuses):
    """Set event status directly in DB (simulates worker result)."""
    event.status = event_statuses[status_name].id
    db_session.flush()


# ------------------------------------------------------------------
# Course / Template / Event fixtures
# ------------------------------------------------------------------


@pytest.fixture()
def workflow_course(db_session, system_user):
    """Course with all required FK relationships."""
    from models import Course

    now = datetime.now(timezone.utc)
    course = Course(
        id=uuid.uuid4(),
        name=f"Workflow Course {uuid.uuid4().hex[:6]}",
        description="Course for workflow tests",
        guacamole=False,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(course)
    db_session.flush()
    return course


@pytest.fixture()
def workflow_template(db_session, system_user):
    """Template with proxmoxId (ready status, no prevent_delete)."""
    from models import Template

    now = datetime.now(timezone.utc)
    template = Template(
        id=uuid.uuid4(),
        name=f"Workflow Template {uuid.uuid4().hex[:6]}",
        description="Template for workflow tests",
        status="Ready",
        proxmoxId=9000,
        proxmoxNode="pve-node-01",
        cpu=2,
        ram=4096,
        disk=32,
        prevent_delete=False,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(template)
    db_session.flush()
    return template


@pytest.fixture()
def workflow_event(db_session, system_user, event_statuses, workflow_course):
    """Event in 'Geplant' status with associated course."""
    from models import Event

    now = datetime.now(timezone.utc)
    event = Event(
        id=uuid.uuid4(),
        name=f"Workflow Event {uuid.uuid4().hex[:6]}",
        slug=f"wf-{uuid.uuid4().hex[:4]}",
        description="Event for workflow tests",
        dateStart=date(2026, 7, 1),
        dateEnd=date(2026, 7, 31),
        timeStart=time(8, 0),
        timeEnd=time(18, 0),
        guacamole=False,
        status=event_statuses["Geplant"].id,
        course=workflow_course.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(event)
    db_session.flush()
    return event


# ------------------------------------------------------------------
# User fixtures
# ------------------------------------------------------------------


@pytest.fixture()
def teacher_user(db_session, system_user, role_teacher):
    """Teacher user with 'lehrende' role."""
    from models import User
    from models.associations import user_role_association_table

    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        username=f"teacher_{uuid.uuid4().hex[:6]}",
        name="Teacher User",
        email=f"teacher_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="$2b$12$dummyhashvalue",
        status="Active",
        locale="de_DE",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(user)
    db_session.flush()
    db_session.execute(
        user_role_association_table.insert().values(
            user_id=user.id, role_id=role_teacher.id
        )
    )
    db_session.flush()
    return user


@pytest.fixture()
def teacher_headers(teacher_user):
    """JWT Bearer token for the teacher."""
    token = create_test_token(teacher_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def student_user(db_session, system_user, role_student):
    """Student user with 'studierende' role."""
    from models import User
    from models.associations import user_role_association_table

    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        username=f"student_{uuid.uuid4().hex[:6]}",
        name="Student User",
        email=f"student_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="$2b$12$dummyhashvalue",
        status="Active",
        locale="de_DE",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(user)
    db_session.flush()
    db_session.execute(
        user_role_association_table.insert().values(
            user_id=user.id, role_id=role_student.id
        )
    )
    db_session.flush()
    return user


@pytest.fixture()
def student_headers(student_user):
    """JWT Bearer token for the student."""
    token = create_test_token(student_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def user_b(db_session, system_user):
    """Second user without any special permissions."""
    from models import User

    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        username=f"userb_{uuid.uuid4().hex[:6]}",
        name="User B",
        email=f"userb_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="$2b$12$dummyhashvalue",
        status="Active",
        locale="de_DE",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture()
def user_b_headers(user_b):
    """JWT Bearer token for user B."""
    token = create_test_token(user_b)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def login_user(db_session, system_user):
    """User with real bcrypt password hash for login tests."""
    from core.auth import get_password_hash
    from models import User

    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        username=f"loginuser_{uuid.uuid4().hex[:6]}",
        name="Login User",
        email=f"loginuser_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=get_password_hash("testpassword123"),
        status="Active",
        locale="de_DE",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(user)
    db_session.flush()
    return user
