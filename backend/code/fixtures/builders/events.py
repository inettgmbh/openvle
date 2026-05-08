import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from fixtures.constants import (
    STATUS_AKTIV_ID,
    STATUS_ARCHIVIERT_ID,
    STATUS_GEPLANT_ID,
    ensure_association,
    fixture_timestamp,
    fixture_uuid,
    next_audit_user,
)
from fixtures.profiles import ProfileConfig
from models.associations import template_event_association_table
from models.events import Event

log = logging.getLogger("fixtures")

# Status distribution for events (weighted)
_STATUS_CYCLE = [
    STATUS_GEPLANT_ID,
    STATUS_AKTIV_ID,
    STATUS_AKTIV_ID,
    STATUS_ARCHIVIERT_ID,
]

EVENT_SUFFIXES = [
    "WS 2026/27",
    "SS 2026",
    "WS 2025/26",
    "SS 2025",
    "Intensivkurs",
    "Blockseminar",
    "Praxisworkshop",
    "Projektseminar",
]

# Short slugs (max 8 chars) — course abbreviation + semester hint
EVENT_SLUGS = [
    "inf-ws27",
    "bs-ss26",
    "net-ws26",
    "db-ss25",
    "sec-ik26",
    "cld-bs26",
    "web-pw26",
    "swe-ps26",
    "inf-ss26",
    "bs-ws26",
    "net-ss25",
    "db-ws27",
    "sec-ws26",
    "cld-ss26",
    "web-ws27",
    "swe-ss25",
    "inf-ik26",
    "bs-bs26",
    "net-pw26",
    "db-ps26",
    "sec-ss26",
    "cld-ws27",
    "web-ss25",
    "swe-ws26",
]


def create_events(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    today = date.today()
    profile = config.name.value
    not_before = context.get("earliest_template") or context.get(
        "earliest_course"
    )
    events: list[Event] = []
    idx = 0
    geplant_count = 0

    templates_by_course = context.get("templates_by_course", {})

    for course in context["courses"]:
        course_templates = templates_by_course.get(course.id, [])

        for _e in range(config.events_per_course):
            uid = fixture_uuid("event", profile, idx)
            existing = session.get(Event, uid)
            if existing:
                events.append(existing)
                idx += 1
                continue

            status_id = _STATUS_CYCLE[idx % len(_STATUS_CYCLE)]

            # Spread events across time
            if status_id == STATUS_ARCHIVIERT_ID:
                start = today - timedelta(days=60 + idx * 7)
                end = start + timedelta(days=14)
            elif status_id == STATUS_AKTIV_ID:
                start = today - timedelta(days=3 + idx)
                end = today + timedelta(days=11 + idx)
            else:  # Geplant
                start = today + timedelta(days=14 + idx * 7)
                end = start + timedelta(days=14)

            suffix = EVENT_SUFFIXES[idx % len(EVENT_SUFFIXES)]
            event = Event(
                id=uid,
                name=f"{course.name} - {suffix}",
                slug=EVENT_SLUGS[idx % len(EVENT_SLUGS)],
                description=f"Veranstaltung {course.name}",
                dateStart=start,
                dateEnd=end,
                guacamole=True,
                status=status_id,
                course=course.id,
                createdAt=fixture_timestamp("event", profile, idx, not_before),
                updatedAt=fixture_timestamp(
                    "event_upd", profile, idx, not_before
                ),
                createdById=next_audit_user(context),
                updatedById=next_audit_user(context),
            )
            session.add(event)
            session.flush()

            # Link templates to event:
            # - Aktiv/Archiviert: always assign course templates
            # - Geplant: alternate (some with, some without)
            if status_id == STATUS_GEPLANT_ID:
                assign_templates = geplant_count % 2 == 0
                geplant_count += 1
            else:
                assign_templates = True
            if assign_templates:
                for tpl in course_templates:
                    ensure_association(
                        session,
                        template_event_association_table,
                        event_id=uid,
                        template_id=tpl.id,
                    )

            events.append(event)
            idx += 1

    session.flush()
    context["events"] = events
    log.info("  %d events", len(events))
