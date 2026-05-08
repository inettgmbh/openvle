---
id: guacamole
sidebar_label: Apache Guacamole Integration
sidebar_position: 30
status: finished
tags:
  - installation
  - guacamole
---

# Apache Guacamole — Integration {#guacamole-integration}

Apache Guacamole ermöglicht webbasierten Remote-Desktop-Zugang (RDP, VNC, SSH) ohne Client-Software. OpenVLE nutzt Guacamole, um Benutzern den Zugriff auf virtuelle Maschinen direkt im Browser zu ermöglichen.

Guacamole wird als separater Dienst betrieben und ist **nicht** Teil des Standard-Docker-Stacks von OpenVLE. Für die Installation und den Betrieb von Guacamole verweisen wir auf die offizielle Dokumentation.

:::info Optionale Komponente
Guacamole ist optional, wird aber empfohlen. Ohne Guacamole kann OpenVLE weiterhin zum Verwalten von VMs und VM-Vorlagen genutzt werden — der webbasierte Remote-Desktop-Zugang steht dann jedoch nicht zur Verfügung.
:::

## Voraussetzungen {#prerequisites}

- Separater Server oder Docker-Host für Guacamole
- Netzwerkzugang vom OpenVLE-Backend zum Guacamole-Server (Standard: Port 8080, bzw. 443 bei HTTPS)
- Eine MariaDB/MySQL-Datenbank für Guacamole

:::caution Separate Datenbank
Guacamole benötigt eine **eigene** Datenbank — verwende nicht die OpenVLE MariaDB-Instanz.
:::

## Installation {#installation}

Die offizielle Apache Guacamole Docker-Dokumentation beschreibt die Einrichtung im Detail:

- [Apache Guacamole Docker Installation](https://guacamole.apache.org/doc/gug/guacamole-docker.html)

Eine typische Guacamole-Installation besteht aus drei Containern:

| Container      | Funktion                                                       |
| -------------- | -------------------------------------------------------------- |
| `guacd`        | Connection Proxy — verwaltet die Remote-Desktop-Verbindungen   |
| `guacamole`    | Web-Frontend — stellt die Benutzeroberfläche bereit            |
| `guacamole-db` | Datenbank — speichert Benutzer, Verbindungen und Konfiguration |

## OpenVLE-Benutzer in Guacamole anlegen {#create-openvle-user}

OpenVLE benötigt einen dedizierten Admin-Account in Guacamole, um Verbindungen automatisch verwalten zu können. Erstelle diesen Benutzer über die Guacamole-Weboberfläche:

1. Melde dich als Administrator in der Guacamole-Weboberfläche an
2. Navigiere zu **Einstellungen → Benutzer → Neuer Benutzer**
3. Erstelle einen Benutzer mit Administratorrechten
4. Notiere dir Benutzername und Passwort — diese werden im nächsten Schritt benötigt

## OpenVLE-Backend konfigurieren {#configure-backend}

Trage die Guacamole-Verbindungsdaten in die `.env`-Datei des Backends ein. Die vollständige Referenz aller Umgebungsvariablen findest du unter [Konfiguration](configuration?stack=backend).

| Variable                              | Beschreibung                                  | Beispiel                       |
| ------------------------------------- | --------------------------------------------- | ------------------------------ |
| `GUACAMOLE_URL`                       | URL des Guacamole-Servers                     | `http://guacamole-server:8080` |
| `GUACAMOLE_DB`                        | Datenbanktyp von Guacamole                    | `mysql`                        |
| `GUACAMOLE_USER`                      | Benutzername des OpenVLE-Accounts             | `OpenVLE`                      |
| `GUACAMOLE_PASSWORD`                  | Passwort des OpenVLE-Accounts                 | `sicheres-passwort`            |
| `GUACAMOLE_CONNECTIONS_PREFIX`        | Präfix für automatisch erstellte Verbindungen | `openvle-`                     |
| `GUACAMOLE_CONNECTIONS_PREFIX_EVENTS` | Präfix auch für Event-Verbindungen verwenden  | `True`                         |

## Verifizierung {#verification}

1. **Guacamole-Weboberfläche** aufrufen und prüfen, ob der Login funktioniert
2. **OpenVLE-Backend-Logs** auf erfolgreiche Guacamole-Verbindung prüfen:
   ```bash
   docker logs openvle-backend 2>&1 | grep -i guacamole
   ```
3. In OpenVLE eine **Test-VM mit Verbindung** erstellen und prüfen, ob die Guacamole-Verbindung automatisch angelegt wird

## Fehlerbehebung {#troubleshooting}

| Problem                                        | Lösung                                                                                                                                                                           |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend kann Guacamole nicht erreichen         | Prüfe ob `GUACAMOLE_URL` in der `.env`-Datei korrekt gesetzt ist und der Netzwerkzugang zwischen Backend und Guacamole besteht.                                                  |
| Login in Guacamole-WebUI schlägt fehl          | Prüfe ob die initiale Datenbank-Einrichtung korrekt durchgeführt wurde.                                                                                                          |
| Verbindungen werden nicht automatisch erstellt | Prüfe die Backend-Logs (`docker logs openvle-backend`) auf Guacamole-bezogene Fehlermeldungen und stelle sicher, dass der OpenVLE-Benutzer Administratorrechte in Guacamole hat. |

## Weiterführende Dokumentation {#further-reading}

- [Infrastruktur: Guacamole](/docs/admin/infrastructure/guacamole) — Architektur und Netzwerkanforderungen
- [Benutzung: Guacamole](/docs/usage/guacamole/) — Anleitung für Endbenutzer
