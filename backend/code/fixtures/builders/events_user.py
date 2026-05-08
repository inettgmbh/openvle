import logging

from sqlalchemy.orm import Session

from fixtures.constants import (
    ROLE_LEHRENDE_ID,
    ROLE_STUDIERENDE_ID,
    fixture_timestamp,
    fixture_uuid,
    next_audit_user,
)
from fixtures.profiles import ProfileConfig
from models.events_user import EventsUser

log = logging.getLogger("fixtures")


def create_events_user(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    profile = config.name.value
    idx = 0

    teachers = context["teachers"]
    students = context["students"]
    events = context["events"]

    for event_idx, event in enumerate(events):
        # Assign 1-2 teachers per event (round-robin)
        n_teachers = min(2, len(teachers))
        for t in range(n_teachers):
            teacher = teachers[(event_idx + t) % len(teachers)]
            uid = fixture_uuid("events_user", profile, idx)
            existing = session.get(EventsUser, uid)
            if not existing:
                eu = EventsUser(
                    id=uid,
                    user_id=teacher.id,
                    event_id=event.id,
                    role_id=ROLE_LEHRENDE_ID,
                    createdAt=fixture_timestamp(
                        "eu", profile, idx, event.createdAt
                    ),
                    updatedAt=fixture_timestamp(
                        "eu_upd", profile, idx, event.createdAt
                    ),
                    createdById=next_audit_user(context),
                    updatedById=next_audit_user(context),
                )
                session.add(eu)
            idx += 1

        # Assign a subset of students per event (round-robin)
        students_per_event = min(
            len(students),
            max(3, len(students) // max(len(events), 1)),
        )
        for s in range(students_per_event):
            student = students[(event_idx + s) % len(students)]
            uid = fixture_uuid("events_user", profile, idx)
            existing = session.get(EventsUser, uid)
            if not existing:
                eu = EventsUser(
                    id=uid,
                    user_id=student.id,
                    event_id=event.id,
                    role_id=ROLE_STUDIERENDE_ID,
                    createdAt=fixture_timestamp(
                        "eu", profile, idx, event.createdAt
                    ),
                    updatedAt=fixture_timestamp(
                        "eu_upd", profile, idx, event.createdAt
                    ),
                    createdById=next_audit_user(context),
                    updatedById=next_audit_user(context),
                )
                session.add(eu)
            idx += 1

    session.flush()
    log.info("  %d event-user assignments", idx)
