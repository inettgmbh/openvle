import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from fixtures.constants import fixture_timestamp, fixture_uuid, next_audit_user
from fixtures.profiles import ProfileConfig
from models.associations import vm_guac_association_table
from models.guacamole import Guacamole
from models.tags import Tag
from models.virtual_machines import VirtualMachine

log = logging.getLogger("fixtures")

# Tags assigned per event — each event gets 1-2 from this pool
EVENT_TAG_DEFS = [
    ("fachbereich", "informatik"),
    ("fachbereich", "elektrotechnik"),
    ("fachbereich", "mathematik"),
    ("semester", "ws2026"),
    ("semester", "ss2026"),
    ("semester", "ws2025"),
    ("lehrformat", "laboruebung"),
    ("lehrformat", "projektseminar"),
    ("lehrformat", "blockkurs"),
    ("standort", "campus-nord"),
    ("standort", "campus-sued"),
    ("schwerpunkt", "programmierung"),
    ("schwerpunkt", "netzwerke"),
    ("schwerpunkt", "betriebssysteme"),
]

# Extra tags only for templates
TEMPLATE_TAG_DEFS = [
    ("os-familie", "linux"),
    ("os-familie", "windows"),
    ("einsatz", "lehre"),
    ("einsatz", "pruefung"),
]


def create_tags(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    profile = config.name.value
    count = 0
    idx = 0

    events = context.get("events", [])
    vms_by_event: dict[uuid.UUID, list] = {}
    for vm in context.get("vms", []):
        vms_by_event.setdefault(vm.event, []).append(vm)

    # -- Tag events + propagate to VMs and connections --
    for ei, event in enumerate(events):
        # Pick 1-2 tags per event based on index
        n_tags = 1 + (ei % 2)
        for t in range(n_tags):
            tag_def = EVENT_TAG_DEFS[(ei * 2 + t) % len(EVENT_TAG_DEFS)]
            key, value = tag_def

            # Tag the event
            idx = _add_tag(
                session,
                profile,
                idx,
                key,
                value,
                event.id,
                "Event",
                event.createdAt,
                context,
            )
            count += 1

            # Propagate to all VMs of this event
            event_vms = vms_by_event.get(event.id, [])
            for vm in event_vms:
                idx = _add_tag(
                    session,
                    profile,
                    idx,
                    key,
                    value,
                    vm.id,
                    "VirtualMachine",
                    vm.createdAt,
                    context,
                )
                count += 1

                # Propagate to all connections of this VM
                conn_rows = session.execute(
                    vm_guac_association_table.select().where(
                        vm_guac_association_table.c.vm_id == vm.id
                    )
                ).fetchall()
                for row in conn_rows:
                    conn = session.get(Guacamole, row.guacamole_id)
                    if conn:
                        idx = _add_tag(
                            session,
                            profile,
                            idx,
                            key,
                            value,
                            conn.id,
                            "Guacamole",
                            conn.createdAt,
                            context,
                        )
                        count += 1

    # -- Tag templates --
    for ti, tpl in enumerate(context.get("templates", [])):
        tag_def = TEMPLATE_TAG_DEFS[ti % len(TEMPLATE_TAG_DEFS)]
        key, value = tag_def
        idx = _add_tag(
            session,
            profile,
            idx,
            key,
            value,
            tpl.id,
            "Template",
            tpl.createdAt,
            context,
        )
        count += 1

    session.flush()
    log.info("  %d tags", count)


def _add_tag(
    session: Session,
    profile: str,
    idx: int,
    key: str,
    value: str,
    object_id,
    object_type: str,
    not_before,
    context: dict,
) -> int:
    uid = fixture_uuid("tag", profile, idx)
    if not session.get(Tag, uid):
        ts = fixture_timestamp("tag", profile, idx, not_before)
        author = next_audit_user(context)
        session.add(
            Tag(
                id=uid,
                key=key,
                value=value,
                objectId=object_id,
                objectType=object_type,
                createdAt=ts,
                updatedAt=ts,
                createdById=author,
                updatedById=author,
            )
        )
    return idx + 1
