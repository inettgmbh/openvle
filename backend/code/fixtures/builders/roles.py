import logging

from sqlalchemy.orm import Session

from fixtures.constants import (
    SYSTEM_USER_ID,
    ensure_association,
    fixture_timestamp,
    fixture_uuid,
    next_audit_user,
)
from fixtures.profiles import ProfileConfig
from models.associations import user_role_association_table
from models.roles import Role

log = logging.getLogger("fixtures")

ROLE_DEFS = [
    {
        "name": "Professoren",
        "key": "professoren",
        "description": "Professorinnen und Professoren der Hochschule",
    },
    {
        "name": "Fachbereich Informatik",
        "key": "fb_informatik",
        "description": "Mitglieder des Fachbereichs Informatik",
    },
    {
        "name": "Fachbereich Elektrotechnik",
        "key": "fb_elektrotechnik",
        "description": "Mitglieder des Fachbereichs Elektrotechnik",
    },
    {
        "name": "Laborassistenz",
        "key": "laborassistenz",
        "description": "Laborassistentinnen und -assistenten",
    },
    {
        "name": "Tutorinnen und Tutoren",
        "key": "tutoren",
        "description": "Tutorinnen und Tutoren fuer Uebungsgruppen",
    },
]


def create_roles(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    profile = config.name.value
    not_before = context.get("earliest_user")
    roles: list[Role] = []

    for i in range(config.roles):
        uid = fixture_uuid("role", profile, i)
        existing = session.get(Role, uid)
        if existing:
            roles.append(existing)
            continue
        rdef = ROLE_DEFS[i % len(ROLE_DEFS)]
        role = Role(
            id=uid,
            name=rdef["name"],
            key=rdef["key"],
            description=rdef["description"],
            protected=False,
            createdAt=fixture_timestamp("role", profile, i, not_before),
            updatedAt=fixture_timestamp("role_upd", profile, i, not_before),
            createdById=next_audit_user(context),
            updatedById=next_audit_user(context),
        )
        session.add(role)
        roles.append(role)

    session.flush()

    # Assign members to roles
    teachers = context.get("teachers", [])
    students = context.get("students", [])

    for i, role in enumerate(roles):
        rdef = ROLE_DEFS[i % len(ROLE_DEFS)]
        key = rdef["key"]

        if key == "professoren":
            # All teachers are professors
            members = teachers
        elif key.startswith("fb_"):
            # Split teachers across departments, some students too
            dept_teachers = teachers[i :: len(roles)]
            dept_students = students[i :: len(roles)]
            members = list(dept_teachers) + list(dept_students[:3])
        elif key == "laborassistenz":
            # A few students
            members = students[: min(3, len(students))]
        elif key == "tutoren":
            # Some students
            members = students[2 : min(8, len(students))]
        else:
            members = []

        for user in members:
            ensure_association(
                session,
                user_role_association_table,
                user_id=user.id,
                role_id=role.id,
            )

    session.flush()
    context["fixture_roles"] = roles
    log.info("  %d roles", len(roles))
