import logging

from sqlalchemy.orm import Session

from fixtures.constants import fixture_timestamp, fixture_uuid, next_audit_user
from fixtures.profiles import ProfileConfig
from models.documents import Document

log = logging.getLogger("fixtures")

DOCUMENT_DEFS = [
    (
        "Installationsanleitung Debian",
        "/docs/install_debian.pdf",
        "Schritt-fuer-Schritt-Anleitung zur Installation "
        "und Grundkonfiguration von Debian 12 Bookworm",
    ),
    (
        "Netzwerkkonfiguration Handbuch",
        "/docs/network_config.pdf",
        "Konfiguration von Netzwerkschnittstellen, "
        "IP-Adressen, DNS und Routing unter Linux",
    ),
    (
        "Windows-Einrichtung Leitfaden",
        "/docs/windows_setup.pdf",
        "Ersteinrichtung von Windows 11 fuer den Einsatz "
        "in der virtuellen Laborumgebung",
    ),
    (
        "SSH-Zugang Kurzanleitung",
        "/docs/ssh_quickstart.pdf",
        "Anleitung zur Einrichtung von SSH-Schluesselpaaren "
        "und Verbindungsaufbau zu den Lab-VMs",
    ),
    (
        "Laborordnung",
        "/docs/lab_rules.pdf",
        "Verhaltensregeln und organisatorische Hinweise "
        "fuer die Nutzung der virtuellen Labore",
    ),
    (
        "Git-Einfuehrung",
        "/docs/git_intro.pdf",
        "Grundlagen der Versionsverwaltung mit Git: "
        "Commits, Branches, Merges und Zusammenarbeit",
    ),
    (
        "Docker-Grundlagen",
        "/docs/docker_basics.pdf",
        "Einfuehrung in Containerisierung mit Docker: "
        "Images, Container, Volumes und Netzwerke",
    ),
    (
        "SQL-Referenz",
        "/docs/sql_reference.pdf",
        "Nachschlagewerk fuer SQL-Syntax, Joins, "
        "Aggregationen und Unterabfragen",
    ),
    (
        "Python-Cheatsheet",
        "/docs/python_cheatsheet.pdf",
        "Kurzreferenz fuer Python 3: Datentypen, "
        "Kontrollstrukturen, Standardbibliothek",
    ),
    (
        "Sicherheitsrichtlinien Labor",
        "/docs/lab_security.pdf",
        "Technische und organisatorische Massnahmen "
        "zur IT-Sicherheit im Laborbetrieb",
    ),
]


def create_documents(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    profile = config.name.value
    count = 0

    for i in range(config.documents):
        uid = fixture_uuid("document", profile, i)
        existing = session.get(Document, uid)
        if existing:
            continue
        name, path, desc = DOCUMENT_DEFS[i % len(DOCUMENT_DEFS)]
        doc = Document(
            id=uid,
            name=name,
            description=desc,
            path=f"/fixtures{path}",
            createdAt=fixture_timestamp("document", profile, i),
            updatedAt=fixture_timestamp("document_upd", profile, i),
            createdById=next_audit_user(context),
            updatedById=next_audit_user(context),
        )
        session.add(doc)
        count += 1

    session.flush()
    log.info("  %d documents", count)
