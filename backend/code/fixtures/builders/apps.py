import logging

from sqlalchemy.orm import Session

from fixtures.constants import (
    fixture_timestamp,
    fixture_uuid,
    next_audit_user,
)
from fixtures.profiles import ProfileConfig
from models.apps import Application
from models.vendor import Vendor

log = logging.getLogger("fixtures")

# Vendors to create (only if they don't exist as seeds)
VENDOR_DEFS = [
    ("JetBrains", "Entwicklungsumgebungen und Produktivitaetstools"),
    ("HashiCorp", "Infrastructure-as-Code und Cloud-Tooling"),
    ("Docker Inc", "Container-Plattform und Entwicklertools"),
    ("PostgreSQL Global Development Group", "Open-Source-Datenbank"),
    ("Elastic NV", "Such- und Analyseplattform"),
    ("Grafana Labs", "Monitoring- und Observability-Plattform"),
    ("Oracle", "Datenbanken und Enterprise-Software"),
    ("Red Hat", "Enterprise-Linux und Open-Source-Loesungen"),
    ("Wireshark Foundation", "Netzwerkanalyse-Tools"),
    ("OpenJS Foundation", "JavaScript-Oekosystem und Laufzeitumgebungen"),
    ("Python Software Foundation", "Python-Programmiersprache"),
    ("The Document Foundation", "Freie Office-Software"),
    ("Nmap Project", "Open-Source-Netzwerksicherheit"),
    ("Simon Tatham", "PuTTY SSH-Client"),
    ("Tim Kosse", "FileZilla FTP-Client"),
    ("GNOME Foundation", "Freie Desktop-Umgebung und Anwendungen"),
    (
        "Software Freedom Conservancy",
        "Foerderung freier Software-Projekte",
    ),
]

# Apps to create: (key, name, vendor_name, description)
# vendor_name must match a seed vendor or one from VENDOR_DEFS above
APP_DEFS = [
    (
        "intellij_idea",
        "IntelliJ IDEA",
        "JetBrains",
        "Integrierte Entwicklungsumgebung fuer Java und Kotlin",
    ),
    (
        "pycharm",
        "PyCharm",
        "JetBrains",
        "Python-IDE mit Debugging und Testing-Integration",
    ),
    (
        "docker_desktop",
        "Docker Desktop",
        "Docker Inc",
        "Container-Runtime und Management-Oberflaeche",
    ),
    (
        "terraform",
        "Terraform",
        "HashiCorp",
        "Infrastructure-as-Code fuer Cloud-Provisionierung",
    ),
    (
        "ansible",
        "Ansible",
        "Red Hat",
        "Automatisierungstool fuer Konfigurationsmanagement",
    ),
    (
        "postgresql",
        "PostgreSQL",
        "PostgreSQL Global Development Group",
        "Relationales Open-Source-Datenbanksystem",
    ),
    (
        "mysql_workbench",
        "MySQL Workbench",
        "Oracle",
        "Visuelles Datenbank-Design- und Administrationstool",
    ),
    (
        "wireshark",
        "Wireshark",
        "Wireshark Foundation",
        "Netzwerkprotokoll-Analysator",
    ),
    (
        "git",
        "Git",
        "Software Freedom Conservancy",
        "Verteiltes Versionskontrollsystem",
    ),
    (
        "nodejs",
        "Node.js",
        "OpenJS Foundation",
        "JavaScript-Laufzeitumgebung fuer serverseitige Anwendungen",
    ),
    (
        "python3",
        "Python 3",
        "Python Software Foundation",
        "Interpretierte Programmiersprache fuer vielseitige Einsatzgebiete",
    ),
    (
        "grafana",
        "Grafana",
        "Grafana Labs",
        "Dashboards und Visualisierung fuer Metriken und Logs",
    ),
    (
        "elasticsearch",
        "Elasticsearch",
        "Elastic NV",
        "Verteilte Such- und Analyse-Engine",
    ),
    (
        "libreoffice",
        "LibreOffice",
        "The Document Foundation",
        "Freies Office-Paket fuer Textverarbeitung und Tabellenkalkulation",
    ),
    (
        "thunderbird",
        "Thunderbird",
        "Mozilla",
        "Open-Source-E-Mail-Client",
    ),
    (
        "gimp",
        "GIMP",
        "GNOME Foundation",
        "Open-Source-Bildbearbeitungsprogramm",
    ),
    (
        "filezilla",
        "FileZilla",
        "Tim Kosse",
        "FTP-, FTPS- und SFTP-Client",
    ),
    (
        "putty",
        "PuTTY",
        "Simon Tatham",
        "SSH- und Telnet-Client fuer Windows",
    ),
    (
        "nmap",
        "Nmap",
        "Nmap Project",
        "Netzwerk-Scanner und Security-Auditing-Tool",
    ),
    (
        "virtualbox",
        "VirtualBox",
        "Oracle",
        "Desktop-Virtualisierung fuer Testzwecke",
    ),
]

# Which apps go on which template type (by template name prefix)
TEMPLATE_APP_MAPPING = {
    "Debian": [
        "git",
        "python3",
        "nodejs",
        "docker_desktop",
        "ansible",
        "nmap",
        "wireshark",
    ],
    "Windows": [
        "putty",
        "filezilla",
        "libreoffice",
        "thunderbird",
        "mysql_workbench",
        "virtualbox",
    ],
    "Ubuntu": [
        "git",
        "python3",
        "docker_desktop",
        "intellij_idea",
        "pycharm",
        "postgresql",
        "gimp",
    ],
}


def create_apps(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    profile = config.name.value
    vendor_count = 0
    app_count = 0

    # Ensure vendors exist (create only new ones)
    vendors_by_name: dict[str, Vendor] = {}
    for existing in session.query(Vendor).all():
        vendors_by_name[existing.name] = existing

    for vi, (name, desc) in enumerate(VENDOR_DEFS):
        if name in vendors_by_name:
            continue
        uid = fixture_uuid("vendor", profile, vi)
        existing = session.get(Vendor, uid)
        if existing:
            vendors_by_name[existing.name] = existing
            continue
        ts = fixture_timestamp("vendor", profile, vi)
        author = next_audit_user(context)
        vendor = Vendor(
            id=uid,
            name=name,
            description=desc,
            createdAt=ts,
            updatedAt=ts,
            createdById=author,
            updatedById=author,
        )
        session.add(vendor)
        vendors_by_name[name] = vendor
        vendor_count += 1

    session.flush()

    # Create apps
    apps_by_key: dict[str, Application] = {}
    for existing in session.query(Application).all():
        apps_by_key[existing.key] = existing

    for ai, (key, name, vendor_name, desc) in enumerate(APP_DEFS):
        if key in apps_by_key:
            continue
        uid = fixture_uuid("app", profile, ai)
        existing = session.get(Application, uid)
        if existing:
            apps_by_key[existing.key] = existing
            continue
        vendor = vendors_by_name.get(vendor_name)
        if not vendor:
            continue
        ts = fixture_timestamp("app", profile, ai)
        author = next_audit_user(context)
        app = Application(
            id=uid,
            key=key,
            name=name,
            description=desc,
            vendor=vendor.id,
            createdAt=ts,
            updatedAt=ts,
            createdById=author,
            updatedById=author,
        )
        session.add(app)
        apps_by_key[key] = app
        app_count += 1

    session.flush()
    context["apps_by_key"] = apps_by_key
    context["vendors_by_name"] = vendors_by_name
    log.info("  %d vendors, %d apps", vendor_count, app_count)
