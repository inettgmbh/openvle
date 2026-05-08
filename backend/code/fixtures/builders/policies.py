import logging

from sqlalchemy.orm import Session

from fixtures.constants import fixture_timestamp, fixture_uuid, next_audit_user
from fixtures.profiles import ProfileConfig
from models.policies import Policy

log = logging.getLogger("fixtures")

POLICY_DEFS = [
    {
        "name": "Datenschutzrichtlinie",
        "description": (
            "Regelungen zum Schutz personenbezogener Daten "
            "in der virtuellen Laborumgebung"
        ),
        "content": (
            "1. Geltungsbereich\n\n"
            "Diese Datenschutzrichtlinie gilt fuer alle Nutzerinnen "
            "und Nutzer der virtuellen Laborumgebung OpenVLE. Sie "
            "regelt die Erhebung, Verarbeitung und Nutzung "
            "personenbezogener Daten im Rahmen der Plattformnutzung.\n\n"
            "2. Verantwortliche Stelle\n\n"
            "Verantwortlich fuer die Datenverarbeitung ist die "
            "Hochschulverwaltung in Zusammenarbeit mit dem "
            "Rechenzentrum. Anfragen zum Datenschutz richten Sie "
            "bitte an datenschutz@hochschule-beispiel.de.\n\n"
            "3. Erhobene Daten\n\n"
            "Im Rahmen der Nutzung werden folgende Daten erhoben:\n"
            "- Anmeldedaten (Benutzername, E-Mail-Adresse)\n"
            "- Verbindungsdaten (IP-Adresse, Zeitstempel, "
            "aufgerufene Ressourcen)\n"
            "- Aktivitaetsdaten (erstellte virtuelle Maschinen, "
            "Verbindungszeiten)\n\n"
            "4. Zweck der Datenverarbeitung\n\n"
            "Die Daten werden ausschliesslich zur Bereitstellung "
            "der Laborumgebung, zur Gewaehrleistung der "
            "IT-Sicherheit und zur Abrechnung der Ressourcennutzung "
            "verarbeitet. Eine Weitergabe an Dritte erfolgt nicht.\n\n"
            "5. Speicherdauer\n\n"
            "Personenbezogene Daten werden nach Ablauf des "
            "Semesters bzw. spatestens sechs Monate nach der "
            "letzten Anmeldung geloescht. Verbindungsprotokolle "
            "werden nach 90 Tagen automatisch entfernt.\n\n"
            "6. Rechte der Betroffenen\n\n"
            "Sie haben das Recht auf Auskunft, Berichtigung, "
            "Loeschung und Einschraenkung der Verarbeitung Ihrer "
            "Daten. Wenden Sie sich hierzu an die verantwortliche "
            "Stelle."
        ),
    },
    {
        "name": "Nutzungsbedingungen",
        "description": (
            "Allgemeine Bedingungen fuer die Nutzung der "
            "Lernplattform und virtuellen Maschinen"
        ),
        "content": (
            "1. Allgemeines\n\n"
            "Mit der Registrierung auf der Plattform OpenVLE "
            "erklaeren Sie sich mit den folgenden "
            "Nutzungsbedingungen einverstanden. Die Plattform dient "
            "ausschliesslich Lehr- und Forschungszwecken.\n\n"
            "2. Nutzungsumfang\n\n"
            "Jede Nutzerin und jeder Nutzer erhaelt Zugang zu den "
            "virtuellen Maschinen, die im Rahmen der gebuchten "
            "Veranstaltungen bereitgestellt werden. Die Nutzung "
            "ist auf den Zeitraum der jeweiligen Veranstaltung "
            "beschraenkt.\n\n"
            "3. Verbotene Nutzung\n\n"
            "Folgende Aktivitaeten sind untersagt:\n"
            "- Installation nicht autorisierter Software\n"
            "- Nutzung der Ressourcen fuer private oder "
            "kommerzielle Zwecke\n"
            "- Weitergabe von Zugangsdaten an Dritte\n"
            "- Versuche, Sicherheitsmechanismen zu umgehen\n"
            "- Kryptomining oder andere ressourcenintensive "
            "Prozesse ohne Genehmigung\n\n"
            "4. Ressourcenlimits\n\n"
            "Virtuelle Maschinen unterliegen Ressourcenbegrenzungen "
            "(CPU, RAM, Speicherplatz), die von der "
            "Veranstaltungsleitung festgelegt werden. Bei "
            "Ueberschreitung kann die VM automatisch gestoppt "
            "werden.\n\n"
            "5. Verfuegbarkeit\n\n"
            "Die Plattform wird nach bestem Wissen betrieben, eine "
            "Verfuegbarkeitsgarantie besteht nicht. Wartungsfenster "
            "werden nach Moeglichkeit vorab angekuendigt.\n\n"
            "6. Haftung\n\n"
            "Die Hochschule haftet nicht fuer Datenverluste "
            "innerhalb der virtuellen Maschinen. Nutzerinnen und "
            "Nutzer sind fuer die Sicherung eigener Daten selbst "
            "verantwortlich.\n\n"
            "7. Aenderungen\n\n"
            "Die Hochschule behaelt sich vor, diese "
            "Nutzungsbedingungen jederzeit anzupassen. "
            "Aenderungen werden ueber die Plattform bekannt gegeben."
        ),
    },
    {
        "name": "IT-Sicherheitsrichtlinie",
        "description": (
            "Verbindliche Vorgaben zur Informationssicherheit im Laborbetrieb"
        ),
        "content": (
            "1. Zweck\n\n"
            "Diese Richtlinie definiert verbindliche Massnahmen "
            "zur Gewaehrleistung der Informationssicherheit in "
            "der virtuellen Laborumgebung. Sie gilt fuer alle "
            "Personen mit Zugang zur Plattform.\n\n"
            "2. Passwortrichtlinie\n\n"
            "- Passwoerter muessen mindestens 12 Zeichen lang sein "
            "und Gross-/Kleinbuchstaben, Ziffern sowie "
            "Sonderzeichen enthalten.\n"
            "- Die Wiederverwendung der letzten fuenf Passwoerter "
            "ist nicht gestattet.\n"
            "- Passwoerter duerfen nicht im Klartext gespeichert "
            "oder per E-Mail versendet werden.\n"
            "- Sofern angeboten, ist Zwei-Faktor-Authentifizierung "
            "zu aktivieren.\n\n"
            "3. Zugangskontrolle\n\n"
            "Der Zugriff auf virtuelle Maschinen erfolgt "
            "ausschliesslich ueber die bereitgestellten "
            "Remote-Desktop-Verbindungen. Direkte SSH- oder "
            "RDP-Verbindungen unter Umgehung der Plattform sind "
            "nicht gestattet.\n\n"
            "4. Meldepflicht\n\n"
            "Sicherheitsvorfaelle (verdaechtige Aktivitaeten, "
            "unbefugter Zugriff, Malware-Befall) sind umgehend "
            "an das Rechenzentrum zu melden unter "
            "security@hochschule-beispiel.de.\n\n"
            "5. Software und Updates\n\n"
            "Innerhalb der bereitgestellten VMs darf nur die "
            "vorinstallierte Software genutzt werden. "
            "Eigenstaendige Installationen beduerfen der "
            "vorherigen Genehmigung durch die "
            "Veranstaltungsleitung.\n\n"
            "6. Netzwerksicherheit\n\n"
            "- Port-Scanning und Netzwerk-Sniffing sind untersagt.\n"
            "- Die Einrichtung eigener Netzwerkdienste (Webserver, "
            "Proxies) innerhalb der VMs ist ohne Genehmigung nicht "
            "gestattet.\n"
            "- Datenverkehr wird protokolliert und kann bei "
            "Verdacht auf Missbrauch ausgewertet werden.\n\n"
            "7. Sanktionen\n\n"
            "Verstoesse gegen diese Richtlinie koennen zum "
            "sofortigen Entzug des Zugangs fuehren und "
            "disziplinarische Massnahmen nach sich ziehen."
        ),
    },
]


def create_policies(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    profile = config.name.value
    count = 0

    for i in range(config.policies):
        uid = fixture_uuid("policy", profile, i)
        existing = session.get(Policy, uid)
        if existing:
            continue
        pdef = POLICY_DEFS[i % len(POLICY_DEFS)]
        policy = Policy(
            id=uid,
            name=pdef["name"]
            if i < len(POLICY_DEFS)
            else (f"{pdef['name']} v{i}"),
            description=pdef["description"],
            content=pdef["content"],
            active=True,
            createdAt=fixture_timestamp("policy", profile, i),
            updatedAt=fixture_timestamp("policy_upd", profile, i),
            createdById=next_audit_user(context),
            updatedById=next_audit_user(context),
        )
        session.add(policy)
        count += 1

    session.flush()
    log.info("  %d policies", count)
