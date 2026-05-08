---
id: guacamole
sidebar_label: Apache Guacamole
sidebar_position: 55
status: finished
tags:
  - infrastructure
  - guacamole
---

# Apache Guacamole {#guacamole}

Apache Guacamole ermöglicht den webbasierten Remote-Desktop-Zugang zu virtuellen Maschinen. Teilnehmer greifen damit direkt aus dem Browser auf ihre VMs zu — ohne zusätzliche Software installieren zu müssen.

:::info Optional
Apache Guacamole ist eine optionale Komponente. Ohne Guacamole kann OpenVLE weiterhin zum Verwalten von VMs und VM-Vorlagen genutzt werden, jedoch ohne Remote-Desktop-Zugang im Browser.
:::

## Architektur {#architecture}

Apache Guacamole ist eine Open-Source-Software, die Zugriff auf entfernte Ressourcen via RDP, VNC, SSH und weitere Protokolle über einen Standard-Webbrowser ermöglicht. Der Guacamole-Stack besteht aus drei Komponenten:

| Komponente        | Funktion                                                               |
| ----------------- | ---------------------------------------------------------------------- |
| **Guacamole Web** | Weboberfläche und API-Server                                           |
| **guacd**         | Verbindungs-Daemon, der die eigentlichen Remote-Protokolle verarbeitet |
| **Guacamole DB**  | Datenbank für Benutzer, Verbindungen und Konfiguration                 |

## Kommunikation mit OpenVLE {#communication}

OpenVLE verwaltet Guacamole-Verbindungen automatisch. Das Backend kommuniziert über die Guacamole-API mit dem Guacamole-Server und erstellt, aktualisiert und löscht Verbindungen bei folgenden Ereignissen:

- **Verbindung erstellt** — Eine neue Guacamole-Verbindung wird automatisch angelegt
- **VM gelöscht** — Die zugehörige Verbindung wird entfernt
- **Veranstaltung gestartet/beendet** — Verbindungen werden entsprechend aktiviert oder deaktiviert

Dafür benötigt das OpenVLE-Backend einen dedizierten Benutzeraccount mit administrativen Berechtigungen in Guacamole.

## Voraussetzungen {#requirements}

Das OpenVLE-Backend benötigt folgende Informationen, um mit Guacamole zu kommunizieren:

| Information                       | Beispiel                        |
| --------------------------------- | ------------------------------- |
| URL des Guacamole-Servers         | `https://guacamole.example.com` |
| Datenbanktyp von Guacamole        | `mysql`                         |
| Benutzername des OpenVLE-Accounts | `OpenVLE`                       |
| Passwort des OpenVLE-Accounts     | _(sicheres Passwort)_           |

Diese Informationen werden in der `.env` konfiguriert. Zusätzlich muss netzwerktechnisch ein Zugriff vom Backend-Server zum Guacamole-Server möglich sein (standardmäßig HTTPS 443/tcp).

:::note Automatische Verwaltung
Nach der Konfiguration der Zugangsdaten sind keine weiteren manuellen Eingriffe in Guacamole erforderlich. OpenVLE übernimmt die Verwaltung aller Verbindungen vollständig automatisch.
:::

## Benutzer-Authentifizierung in Guacamole {#guacamole-auth}

Guacamole sollte idealerweise an denselben Identity Provider (LDAP oder OIDC) angebunden werden wie OpenVLE. Der Grund: OpenVLE provisioniert Guacamole-Verbindungen auf die gleichen Benutzernamen, die die Benutzer in OpenVLE haben. Wenn Guacamole denselben IdP nutzt, können die Benutzer sich direkt mit ihren bestehenden Zugangsdaten am Remote-Desktop anmelden.

Eine manuelle Benutzerverwaltung in Guacamole ist nicht notwendig — OpenVLE legt Guacamole-Benutzer automatisch an, falls diese noch nicht existieren. In Guacamole muss daher nur die Authentifizierung konfiguriert werden, nicht die Provisionierung.

## Weiterführende Informationen {#further-reading}

- [Apache Guacamole installieren](../install/guacamole) — Einrichtung und Installation
- [Konfigurationsreferenz — Guacamole](../install/configuration#guacamole) — Alle verfügbaren Umgebungsvariablen
