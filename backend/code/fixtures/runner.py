import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from fixtures.builders import (
    apps,
    courses,
    documents,
    events,
    events_user,
    guacamole,
    mails,
    policies,
    roles,
    settings,
    tags,
    tasks,
    templates,
    users,
    vms,
)
from fixtures.constants import (
    FIXTURE_MARKER_KEY,
    SYSTEM_USER_ID,
    Profile,
    fixture_uuid,
)
from fixtures.engine import create_session
from fixtures.profiles import PROFILES, ProfileConfig

log = logging.getLogger("fixtures")


def seed(profile: Profile, *, dry_run: bool = False) -> None:
    config = PROFILES[profile]
    session = create_session()
    context: dict = {}

    try:
        # Check marker
        from models.tags import Tag

        marker = session.execute(
            select(Tag).where(
                Tag.key == FIXTURE_MARKER_KEY,
                Tag.value == profile.value,
            )
        ).scalar_one_or_none()

        if marker:
            log.info(
                "Fixtures for '%s' already seeded. "
                "Re-running for idempotent upsert...",
                profile.value,
            )

        log.info(
            "Seeding profile '%s': %s",
            profile.value,
            config.description,
        )

        log.info("Creating users...")
        users.create_users(session, config, context)

        log.info("Creating roles...")
        roles.create_roles(session, config, context)

        log.info("Creating courses...")
        courses.create_courses(session, config, context)

        log.info("Creating apps...")
        apps.create_apps(session, config, context)

        log.info("Creating templates...")
        templates.create_templates(session, config, context)

        log.info("Creating events...")
        events.create_events(session, config, context)

        log.info("Creating event-user assignments...")
        events_user.create_events_user(session, config, context)

        log.info("Creating virtual machines...")
        vms.create_virtual_machines(session, config, context)

        log.info("Creating guacamole connections...")
        guacamole.create_guacamole(session, config, context)

        log.info("Creating tasks...")
        tasks.create_tasks(session, config, context)

        log.info("Creating mails...")
        mails.create_mails(session, config, context)

        log.info("Creating policies...")
        policies.create_policies(session, config, context)

        log.info("Creating documents...")
        documents.create_documents(session, config, context)

        log.info("Creating tags...")
        tags.create_tags(session, config, context)

        log.info("Updating settings...")
        settings.update_settings(session, config, context)

        # Write marker tag
        if not marker:
            now = datetime.now(timezone.utc)
            marker_id = fixture_uuid("marker", profile.value, 0)
            from models.tags import Tag

            session.add(
                Tag(
                    id=marker_id,
                    key=FIXTURE_MARKER_KEY,
                    value=profile.value,
                    objectId=marker_id,
                    objectType="System",
                    createdAt=now,
                    updatedAt=now,
                    createdById=SYSTEM_USER_ID,
                    updatedById=SYSTEM_USER_ID,
                )
            )

        if dry_run:
            log.info("Dry run — rolling back.")
            session.rollback()
        else:
            session.commit()
            log.info(
                "Fixtures committed for profile '%s'.",
                profile.value,
            )
    except Exception:
        session.rollback()
        log.exception("Fixture seeding failed — rolled back.")
        raise
    finally:
        session.close()


def purge(profile: Profile) -> None:
    """Delete all fixture data for a profile using deterministic UUIDs."""
    config = PROFILES[profile]
    session = create_session()
    p = profile.value

    try:
        log.info("Purging fixtures for profile '%s'...", p)

        _purge_tags(session, config, p)
        _purge_mails(session, config, p)
        _purge_tasks(session, config, p)
        _purge_documents(session, config, p)
        _purge_policies(session, config, p)
        _purge_guacamole(session, config, p)
        _purge_vms(session, config, p)
        _purge_events_user(session, config, p)
        _purge_events(session, config, p)
        _purge_templates(session, config, p)
        _purge_apps(session, config, p)
        _purge_courses(session, config, p)
        _purge_roles(session, config, p)
        _purge_users(session, config, p)
        _purge_marker(session, p)

        log.info("Restoring settings...")
        settings.restore_settings(session)

        session.commit()
        log.info("Purge complete for profile '%s'.", p)
    except Exception:
        session.rollback()
        log.exception("Purge failed — rolled back.")
        raise
    finally:
        session.close()


# -- Purge helpers (UUID-based) --


def _uids(entity: str, profile: str, count: int) -> list:
    return [fixture_uuid(entity, profile, i) for i in range(count)]


def _purge_tags(session: Session, config: ProfileConfig, p: str) -> None:
    from models.tags import Tag

    vm_count = _vm_count(config)
    tpl_count = _tpl_count(config)
    event_count = config.courses * config.events_per_course
    # Tags per event: event + VMs + connections (each VM has ~3 conns)
    conns_per_vm = 1 + config.users_teacher
    tags_per_event = 2 * (1 + vm_count + vm_count * conns_per_vm)
    max_tags = event_count * tags_per_event + tpl_count + 100
    uids = _uids("tag", p, max_tags)
    if uids:
        session.execute(delete(Tag).where(Tag.id.in_(uids)))
    # Marker
    session.execute(delete(Tag).where(Tag.key == FIXTURE_MARKER_KEY))


def _purge_mails(session: Session, config: ProfileConfig, p: str) -> None:
    from models.mails import Mail

    # Generous upper bound: events * (students + teachers*2)
    event_count = config.courses * config.events_per_course
    max_mails = event_count * (config.users_student + config.users_teacher * 4)
    uids = _uids("mail", p, max_mails)
    if uids:
        session.execute(delete(Mail).where(Mail.id.in_(uids)))


def _purge_tasks(session: Session, config: ProfileConfig, p: str) -> None:
    from models.sub_tasks import SubTask
    from models.tasks import Task

    # Generous upper bound for subtasks and tasks
    max_subtasks = 5000
    max_tasks = 500
    sub_uids = _uids("subtask", p, max_subtasks)
    task_uids = _uids("task", p, max_tasks)
    if sub_uids:
        session.execute(delete(SubTask).where(SubTask.id.in_(sub_uids)))
    if task_uids:
        session.execute(delete(Task).where(Task.id.in_(task_uids)))


def _purge_documents(session: Session, config: ProfileConfig, p: str) -> None:
    from models.documents import Document

    uids = _uids("document", p, config.documents)
    if uids:
        session.execute(delete(Document).where(Document.id.in_(uids)))


def _purge_policies(session: Session, config: ProfileConfig, p: str) -> None:
    from models.policies import Policy
    from models.policies_user import PoliciesUser

    uids = _uids("policy", p, config.policies)
    if uids:
        session.execute(
            delete(PoliciesUser).where(PoliciesUser.policy_id.in_(uids))
        )
        session.execute(delete(Policy).where(Policy.id.in_(uids)))


def _purge_guacamole(session: Session, config: ProfileConfig, p: str) -> None:
    from models.associations import vm_guac_association_table
    from models.guacamole import Guacamole
    from models.guacamole_connection_profiles import (
        GuacamoleConnectionProfile,
    )
    from models.virtual_machines import VirtualMachine

    # Upper bound for profiles: (event VMs + manual VMs) * GCPs per template
    total_vms = _vm_count(config) + config.vms_per_event_template
    max_prof = total_vms * 3
    # Upper bound for connections: VMs * GCPs * (1 owner + teachers)
    max_conn = max_prof * (1 + config.users_teacher)
    conn_uids = _uids("guac_conn", p, max_conn)
    prof_uids = _uids("guac_profile", p, max_prof)

    if conn_uids:
        session.execute(
            delete(vm_guac_association_table).where(
                vm_guac_association_table.c.guacamole_id.in_(conn_uids)
            )
        )
        session.execute(delete(Guacamole).where(Guacamole.id.in_(conn_uids)))
    if prof_uids:
        session.execute(
            delete(GuacamoleConnectionProfile).where(
                GuacamoleConnectionProfile.id.in_(prof_uids)
            )
        )

    # Clean up orphaned profiles (e.g. from earlier UUID scheme)
    existing_vm_ids = select(VirtualMachine.id)
    orphaned = select(GuacamoleConnectionProfile.id).where(
        GuacamoleConnectionProfile.objectType == "VirtualMachine",
        ~GuacamoleConnectionProfile.objectId.in_(existing_vm_ids),
    )
    # Delete guacamole connections referencing orphaned profiles
    session.execute(
        delete(vm_guac_association_table).where(
            vm_guac_association_table.c.guacamole_id.in_(
                select(Guacamole.id).where(
                    Guacamole.connection_profile.in_(orphaned)
                )
            )
        )
    )
    session.execute(
        delete(Guacamole).where(Guacamole.connection_profile.in_(orphaned))
    )
    session.execute(
        delete(GuacamoleConnectionProfile).where(
            GuacamoleConnectionProfile.id.in_(orphaned)
        )
    )


def _purge_vms(session: Session, config: ProfileConfig, p: str) -> None:
    from models.associations import (
        user_vm_association_table,
        vm_app_association_table,
    )
    from models.virtual_machines import VirtualMachine

    # Event VMs + manual VMs
    manual_count = config.vms_per_event_template
    uids = _uids("vm", p, _vm_count(config)) + _uids(
        "manual_vm", p, manual_count
    )
    if uids:
        session.execute(
            delete(vm_app_association_table).where(
                vm_app_association_table.c.vm_id.in_(uids)
            )
        )
        session.execute(
            delete(user_vm_association_table).where(
                user_vm_association_table.c.vm_id.in_(uids)
            )
        )
        session.execute(
            delete(VirtualMachine).where(VirtualMachine.id.in_(uids))
        )


def _purge_events_user(session: Session, config: ProfileConfig, p: str) -> None:
    from models.events_user import EventsUser

    # Upper bound: generous estimate for event-user assignments
    max_eu = (
        config.courses * config.events_per_course * (2 + config.users_student)
    )
    uids = _uids("events_user", p, max_eu)
    if uids:
        session.execute(delete(EventsUser).where(EventsUser.id.in_(uids)))


def _purge_events(session: Session, config: ProfileConfig, p: str) -> None:
    from models.associations import template_event_association_table
    from models.events import Event

    uids = _uids("event", p, config.courses * config.events_per_course)
    if uids:
        session.execute(
            delete(template_event_association_table).where(
                template_event_association_table.c.event_id.in_(uids)
            )
        )
        session.execute(delete(Event).where(Event.id.in_(uids)))


def _purge_templates(session: Session, config: ProfileConfig, p: str) -> None:
    from models.associations import (
        course_template_association_table,
        template_app_association_table,
    )
    from models.guacamole_connection_profiles import (
        GuacamoleConnectionProfile,
    )
    from models.templates import Template

    tpl_count = _tpl_count(config)
    uids = _uids("template", p, tpl_count)
    gcp_uids = _uids("tpl_gcp", p, tpl_count)

    if gcp_uids:
        session.execute(
            delete(GuacamoleConnectionProfile).where(
                GuacamoleConnectionProfile.id.in_(gcp_uids)
            )
        )
    if uids:
        session.execute(
            delete(template_app_association_table).where(
                template_app_association_table.c.template_id.in_(uids)
            )
        )
        session.execute(
            delete(course_template_association_table).where(
                course_template_association_table.c.template_id.in_(uids)
            )
        )
        session.execute(delete(Template).where(Template.id.in_(uids)))


def _purge_apps(session: Session, config: ProfileConfig, p: str) -> None:
    from fixtures.builders.apps import APP_DEFS, VENDOR_DEFS
    from models.apps import Application
    from models.associations import (
        template_app_association_table,
        vm_app_association_table,
    )
    from models.vendor import Vendor

    app_uids = _uids("app", p, len(APP_DEFS))
    vendor_uids = _uids("vendor", p, len(VENDOR_DEFS))

    if app_uids:
        # Clean up associations first
        session.execute(
            delete(template_app_association_table).where(
                template_app_association_table.c.app_id.in_(app_uids)
            )
        )
        session.execute(
            delete(vm_app_association_table).where(
                vm_app_association_table.c.app_id.in_(app_uids)
            )
        )
        session.execute(delete(Application).where(Application.id.in_(app_uids)))
    if vendor_uids:
        session.execute(delete(Vendor).where(Vendor.id.in_(vendor_uids)))


def _purge_courses(session: Session, config: ProfileConfig, p: str) -> None:
    from models.courses import Course

    uids = _uids("course", p, config.courses)
    if uids:
        session.execute(delete(Course).where(Course.id.in_(uids)))


def _purge_roles(session: Session, config: ProfileConfig, p: str) -> None:
    from models.associations import user_role_association_table
    from models.roles import Role

    uids = _uids("role", p, config.roles)
    if uids:
        session.execute(
            delete(user_role_association_table).where(
                user_role_association_table.c.role_id.in_(uids)
            )
        )
        session.execute(delete(Role).where(Role.id.in_(uids)))


def _purge_users(session: Session, config: ProfileConfig, p: str) -> None:
    from models.associations import user_role_association_table
    from models.users import User

    teacher_uids = _uids("teacher", p, config.users_teacher)
    student_uids = _uids("student", p, config.users_student)
    all_uids = teacher_uids + student_uids
    if all_uids:
        session.execute(
            delete(user_role_association_table).where(
                user_role_association_table.c.user_id.in_(all_uids)
            )
        )
        session.execute(delete(User).where(User.id.in_(all_uids)))


def _purge_marker(session: Session, p: str) -> None:
    from models.tags import Tag

    session.execute(delete(Tag).where(Tag.key == FIXTURE_MARKER_KEY))


def _vm_count(config: ProfileConfig) -> int:
    return (
        config.courses
        * config.events_per_course
        * config.templates_per_course
        * config.vms_per_event_template
    )


def _tpl_count(config: ProfileConfig) -> int:
    return config.courses * config.templates_per_course
