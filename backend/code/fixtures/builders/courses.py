import logging

from sqlalchemy.orm import Session

from fixtures.constants import fixture_timestamp, fixture_uuid, next_audit_user
from fixtures.profiles import ProfileConfig
from models.courses import Course

log = logging.getLogger("fixtures")

COURSE_NAMES = [
    "Einführung in die Informatik",
    "Betriebssysteme",
    "Netzwerktechnik",
    "Datenbanksysteme",
    "IT-Sicherheit",
    "Cloud Computing",
    "Web-Entwicklung",
    "Softwaretechnik",
    "Verteilte Systeme",
    "Maschinelles Lernen",
]

COURSE_DESCRIPTIONS = [
    "Vermittelt die Grundlagen der Programmierung mit Python, "
    "elementare Datenstrukturen und Algorithmen sowie "
    "objektorientierte Konzepte anhand praktischer Projekte.",
    "Behandelt den Aufbau moderner Betriebssysteme, "
    "Prozessverwaltung, Dateisysteme und Virtualisierung "
    "mit praktischen Uebungen unter Linux und Windows.",
    "Einfuehrung in Netzwerkprotokolle (TCP/IP, DNS, DHCP), "
    "Routing-Konzepte und die Konfiguration von Switches, "
    "Firewalls und VLANs im Laborumfeld.",
    "Relationale Datenmodellierung, SQL-Abfragen, "
    "Normalisierung und Transaktionsmanagement mit "
    "praktischen Uebungen in MariaDB und PostgreSQL.",
    "Grundlagen der Kryptografie, Netzwerksicherheit, "
    "Schwachstellenanalyse und Penetration Testing "
    "in kontrollierten Laborumgebungen.",
    "Einfuehrung in Cloud-Architekturen, "
    "Container-Technologien (Docker, Kubernetes) und "
    "Infrastructure as Code mit Terraform und Ansible.",
    "Entwicklung moderner Webanwendungen mit HTML, CSS, "
    "JavaScript und einem Backend-Framework, inklusive "
    "REST-API-Design und Deployment.",
    "Entwurfsmuster, Clean Code, automatisiertes Testing "
    "und Continuous Integration/Delivery in "
    "Teamprojekten mit Git und GitLab.",
    "Architektur verteilter Systeme, Konsistenzmodelle, "
    "Message Queues und Microservice-Kommunikation "
    "mit praktischen Implementierungen.",
    "Grundlagen des maschinellen Lernens, neuronale Netze, "
    "Modelltraining mit scikit-learn und PyTorch sowie "
    "Deployment von ML-Modellen.",
]


def create_courses(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    profile = config.name.value
    not_before = context.get("earliest_user")
    courses: list[Course] = []

    for i in range(config.courses):
        uid = fixture_uuid("course", profile, i)
        existing = session.get(Course, uid)
        if existing:
            courses.append(existing)
            continue
        course = Course(
            id=uid,
            name=COURSE_NAMES[i % len(COURSE_NAMES)],
            description=COURSE_DESCRIPTIONS[i % len(COURSE_DESCRIPTIONS)],
            guacamole=True,
            createdAt=fixture_timestamp("course", profile, i, not_before),
            updatedAt=fixture_timestamp("course_upd", profile, i, not_before),
            createdById=next_audit_user(context),
            updatedById=next_audit_user(context),
        )
        session.add(course)
        courses.append(course)

    session.flush()
    if courses:
        context["earliest_course"] = min(c.createdAt for c in courses)
    context["courses"] = courses
    log.info("  %d courses", len(courses))
