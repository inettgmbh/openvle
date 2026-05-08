import logging

from sqlalchemy.orm import Session

from fixtures.constants import (
    ROLE_LEHRENDE_ID,
    ROLE_STUDIERENDE_ID,
    SYSTEM_USER_ID,
    fixture_timestamp,
    fixture_uuid,
)
from fixtures.profiles import ProfileConfig
from models.associations import user_role_association_table
from models.users import User

log = logging.getLogger("fixtures")

# bcrypt hash for "Test1234!" — same across all fixture users
_FIXTURE_PASSWORD_HASH = (
    "$2b$12$LJ3m4ys3Lhyuq1G8s0VjCe0X6R4QqD7vQf5G6Y8pQ9N2jK5mW7xHi"
)

_UMLAUT_MAP = str.maketrans(
    {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "é": "e"}
)


def _to_username(full_name: str) -> str:
    """'Prof. Dr. Anna Müller' -> 'amueller'"""
    # Strip titles
    name = full_name
    for prefix in ("Prof. Dr. ", "Dr. "):
        name = name.removeprefix(prefix)
    parts = name.split()
    first = parts[0][0].lower()
    last = parts[-1].lower().translate(_UMLAUT_MAP)
    return f"{first}{last}"


def _unique_username(full_name: str, used: set[str]) -> str:
    """Return a unique username, appending a number only on collision."""
    base = _to_username(full_name)
    candidate = base
    n = 2
    while candidate in used:
        candidate = f"{base}{n}"
        n += 1
    used.add(candidate)
    return candidate


TEACHER_NAMES = [
    "Prof. Dr. Anna Müller",
    "Prof. Dr. Thomas Weber",
    "Dr. Julia Schneider",
    "Dr. Markus Fischer",
    "Prof. Dr. Sabine Becker",
    "Dr. Andreas Hoffmann",
    "Prof. Dr. Claudia Richter",
    "Dr. Stefan Wagner",
    "Prof. Dr. Petra Braun",
    "Dr. Michael Schulz",
    "Prof. Dr. Renate Kraus",
    "Dr. Oliver Schröder",
    "Prof. Dr. Karin Vogel",
    "Dr. Jürgen Stein",
    "Prof. Dr. Monika Winkler",
]

# First/last name pools for generating large numbers of students
_FIRST_NAMES = [
    "Lena",
    "Jonas",
    "Sophie",
    "Lukas",
    "Emma",
    "Felix",
    "Mia",
    "Noah",
    "Hannah",
    "Leon",
    "Laura",
    "Tim",
    "Anna",
    "Paul",
    "Lisa",
    "Max",
    "Julia",
    "David",
    "Sarah",
    "Jan",
    "Marie",
    "Tom",
    "Lea",
    "Simon",
    "Klara",
    "Nico",
    "Lara",
    "Ben",
    "Amelie",
    "Finn",
    "Emilia",
    "Moritz",
    "Charlotte",
    "Alexander",
    "Johanna",
    "Elias",
    "Victoria",
    "Philipp",
    "Theresa",
    "Tobias",
    "Katharina",
    "Florian",
    "Vanessa",
    "Sebastian",
    "Nele",
    "Patrick",
    "Carla",
    "Daniel",
    "Zoe",
    "Matthias",
    "Helena",
    "Robin",
    "Antonia",
    "Jannik",
    "Maja",
    "Luca",
    "Franziska",
    "Erik",
    "Miriam",
    "Niklas",
    "Clara",
    "Ole",
    "Annika",
    "Maximilian",
    "Pauline",
    "Henrik",
    "Marlene",
    "Fabian",
    "Svenja",
    "Dominik",
    "Celine",
    "Marcel",
    "Ronja",
    "Kevin",
    "Sophia",
    "Dennis",
    "Isabel",
    "Adrian",
    "Vivien",
    "Timo",
]

_LAST_NAMES = [
    "Schmidt",
    "Meyer",
    "Bauer",
    "Wolf",
    "Richter",
    "Braun",
    "Hofmann",
    "Wagner",
    "Schäfer",
    "Zimmermann",
    "Koch",
    "Becker",
    "Schmitz",
    "Werner",
    "Frank",
    "Hartmann",
    "Krüger",
    "Lange",
    "König",
    "Schwarz",
    "Weiß",
    "Berger",
    "Lehmann",
    "Fuchs",
    "Huber",
    "Maier",
    "Peters",
    "Neumann",
    "Schreiber",
    "Ludwig",
    "Groß",
    "Keller",
    "Heinrich",
    "Brandt",
    "Kraft",
    "Seidel",
    "Vogt",
    "Schuster",
    "Lorenz",
    "Baumann",
    "Haas",
    "Pfeiffer",
    "Roth",
    "Klein",
    "Ullrich",
    "Franke",
    "Winter",
    "Beck",
    "Krause",
    "Engel",
    "Schumacher",
    "Böhm",
    "Friedrich",
    "Günther",
    "Schmitt",
    "Bergmann",
    "Schilling",
    "Sommer",
    "Wendt",
    "Horn",
    "Jäger",
    "Hahn",
    "Scholz",
    "Ott",
    "Krämer",
    "Böttcher",
    "Rau",
    "Kuhn",
    "Graf",
    "Henning",
    "Strauss",
    "Köhler",
    "Barth",
    "Busch",
    "Walther",
    "Kunz",
    "Dietrich",
    "Pohl",
    "Seifert",
    "Mayer",
]


def _generate_name(index: int) -> str:
    """Generate a full name from first/last name pools."""
    first = _FIRST_NAMES[index % len(_FIRST_NAMES)]
    last = _LAST_NAMES[index // len(_FIRST_NAMES) % len(_LAST_NAMES)]
    return f"{first} {last}"


def _user_status(index: int, total: int) -> str:
    """Assign status: ~92% Active, ~5% Banned, ~3% E-Mail-Pending."""
    pos = index / max(total, 1)
    if pos > 0.97:
        return "E-Mail-Pending"
    if pos > 0.92:
        return "Banned"
    return "Active"


def create_users(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    profile = config.name.value
    teachers: list[User] = []
    students: list[User] = []
    used_usernames: set[str] = set()

    # -- Teachers --
    for i in range(config.users_teacher):
        uid = fixture_uuid("teacher", profile, i)
        existing = session.get(User, uid)
        if existing:
            teachers.append(existing)
            used_usernames.add(existing.username)
            continue
        name = TEACHER_NAMES[i % len(TEACHER_NAMES)]
        username = _unique_username(name, used_usernames)
        user = User(
            id=uid,
            username=username,
            name=name,
            email=f"{username}@{profile}.openvle.de",
            hashed_password=_FIXTURE_PASSWORD_HASH,
            status="Active",
            locale="de_DE",
            createdAt=fixture_timestamp("teacher", profile, i),
            updatedAt=fixture_timestamp("teacher_upd", profile, i),
            createdById=SYSTEM_USER_ID,
            updatedById=SYSTEM_USER_ID,
        )
        session.add(user)
        teachers.append(user)

    # -- Students --
    for i in range(config.users_student):
        uid = fixture_uuid("student", profile, i)
        existing = session.get(User, uid)
        if existing:
            students.append(existing)
            continue
        name = _generate_name(i)
        username = _unique_username(name, used_usernames)
        status = _user_status(i, config.users_student)
        user = User(
            id=uid,
            username=username,
            name=name,
            email=f"{username}@{profile}.openvle.de",
            hashed_password=_FIXTURE_PASSWORD_HASH,
            status=status,
            locale="de_DE",
            createdAt=fixture_timestamp("student", profile, i),
            updatedAt=fixture_timestamp("student_upd", profile, i),
            createdById=SYSTEM_USER_ID,
            updatedById=SYSTEM_USER_ID,
        )
        session.add(user)
        students.append(user)

    session.flush()

    # -- Role assignments (only for active users) --
    active_students = [s for s in students if s.status == "Active"]
    _assign_roles(session, teachers, ROLE_LEHRENDE_ID)
    _assign_roles(session, active_students, ROLE_STUDIERENDE_ID)

    # Track earliest user creation for child object timestamps
    all_users = teachers + students
    if all_users:
        context["earliest_user"] = min(u.createdAt for u in all_users)

    # Build rotating audit user list for other builders
    # Teachers + openvle admin rotate as creators/updaters
    audit_pool = [SYSTEM_USER_ID] + [t.id for t in teachers]
    context["_audit_pool"] = audit_pool
    context["_audit_idx"] = 0
    context["teachers"] = teachers
    context["students"] = students
    log.info("  %d teachers, %d students", len(teachers), len(students))


def _assign_roles(
    session: Session,
    users: list[User],
    role_id,
) -> None:
    for user in users:
        exists = session.execute(
            user_role_association_table.select().where(
                user_role_association_table.c.user_id == user.id,
                user_role_association_table.c.role_id == role_id,
            )
        ).first()
        if not exists:
            session.execute(
                user_role_association_table.insert().values(
                    user_id=user.id, role_id=role_id
                )
            )
