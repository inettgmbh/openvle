import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from fixtures.constants import (
    GUAC_IDENTIFIER_BASE,
    GUACD_HOSTNAME,
    GUACD_PORT,
    ROLE_LEHRENDE_ID,
    ensure_association,
    fixture_timestamp,
    fixture_uuid,
    next_audit_user,
)
from fixtures.profiles import ProfileConfig
from models.associations import (
    user_vm_association_table,
    vm_guac_association_table,
)
from models.events_user import EventsUser
from models.guacamole import Guacamole
from models.guacamole_connection_profiles import (
    GuacamoleConnectionProfile,
)

log = logging.getLogger("fixtures")


def create_guacamole(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    profile = config.name.value
    profiles_created = 0
    connections_created = 0
    gcp_idx = 0
    conn_idx = 0

    templates_by_id = {t.id: t for t in context.get("templates", [])}

    # Cache: event_id -> list of teacher user_ids
    event_teachers: dict = {}

    for vm in context.get("vms", []):
        tpl = templates_by_id.get(vm.template)
        if not tpl:
            continue

        # Get template's connection profiles
        tpl_gcps = (
            session.execute(
                select(GuacamoleConnectionProfile).where(
                    GuacamoleConnectionProfile.objectId == tpl.id,
                    GuacamoleConnectionProfile.objectType == "Template",
                )
            )
            .scalars()
            .all()
        )
        if not tpl_gcps:
            continue

        # Get assigned student for this VM
        vm_user_row = session.execute(
            user_vm_association_table.select().where(
                user_vm_association_table.c.vm_id == vm.id
            )
        ).first()
        student_id = vm_user_row.user_id if vm_user_row else None

        # Get teachers for this event (cached); manual VMs have no event
        if vm.event and vm.event not in event_teachers:
            rows = session.execute(
                select(EventsUser.user_id).where(
                    EventsUser.event_id == vm.event,
                    EventsUser.role_id == ROLE_LEHRENDE_ID,
                )
            ).all()
            event_teachers[vm.event] = [r[0] for r in rows]
        teachers = event_teachers.get(vm.event, [])

        # Clone each template GCP for this VM
        for tpl_gcp in tpl_gcps:
            prof_uid = fixture_uuid("guac_profile", profile, gcp_idx)
            existing_prof = session.get(GuacamoleConnectionProfile, prof_uid)
            if not existing_prof:
                prof_ts = fixture_timestamp(
                    "guac", profile, gcp_idx, vm.createdAt
                )
                prof_author = next_audit_user(context)
                gcp = GuacamoleConnectionProfile(
                    id=prof_uid,
                    port=tpl_gcp.port,
                    protocol=tpl_gcp.protocol,
                    username=tpl_gcp.username,
                    password=tpl_gcp.password,
                    objectId=vm.id,
                    objectType="VirtualMachine",
                    createdAt=prof_ts,
                    updatedAt=prof_ts,
                    createdById=prof_author,
                    updatedById=prof_author,
                )
                session.add(gcp)
                session.flush()
                profiles_created += 1
            else:
                gcp = existing_prof
            gcp_idx += 1

            # Collect users who get connections:
            # 1) The assigned student
            # 2) All teachers of the event
            conn_users: list = []
            if student_id:
                conn_users.append(student_id)
            for tid in teachers:
                if tid not in conn_users:
                    conn_users.append(tid)

            for user_id in conn_users:
                conn_uid = fixture_uuid("guac_conn", profile, conn_idx)
                if not session.get(Guacamole, conn_uid):
                    conn_ts = fixture_timestamp(
                        "guac_conn",
                        profile,
                        conn_idx,
                        vm.createdAt,
                    )
                    conn_author = next_audit_user(context)
                    conn = Guacamole(
                        id=conn_uid,
                        name=f"{vm.name}-{gcp.protocol}"[:100],
                        guacd_hostname=GUACD_HOSTNAME,
                        guacd_port=GUACD_PORT,
                        guacd_encryption=True,
                        connection_hostname=vm.ipv4 or "10.0.0.1",
                        connection_profile=gcp.id,
                        identifier=GUAC_IDENTIFIER_BASE + conn_idx,
                        userId=user_id,
                        eventId=vm.event,
                        createdAt=conn_ts,
                        updatedAt=conn_ts,
                        createdById=conn_author,
                        updatedById=conn_author,
                    )
                    session.add(conn)
                    session.flush()

                    ensure_association(
                        session,
                        vm_guac_association_table,
                        vm_id=vm.id,
                        guacamole_id=conn_uid,
                    )

                    connections_created += 1
                conn_idx += 1

    session.flush()
    log.info(
        "  %d guacamole profiles, %d connections",
        profiles_created,
        connections_created,
    )
