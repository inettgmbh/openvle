---
id: openvle
sidebar_label: OpenVLE
sidebar_position: 40
status: finished
tags:
  - installation
  - docker
  - backend
  - frontend
---

# OpenVLE {#openvle}

OpenVLE wird als Docker-Compose-Stack betrieben und umfasst alle benötigten Dienste in einem einzigen Repository. Ein `docker compose up -d` startet die gesamte Anwendung.

## Architektur {#architecture}

Der Docker-Compose-Stack besteht aus folgenden Services:

| Service     | Funktion                                                                          |
| ----------- | --------------------------------------------------------------------------------- |
| `backend`   | Python/FastAPI — API-Server, Geschäftslogik                                       |
| `frontend`  | Vue.js/Nginx — Weboberfläche                                                      |
| `worker`    | RQ Worker — asynchrone Hintergrundaufgaben (VM-Operationen, E-Mail-Versand, etc.) |
| `scheduler` | RQ Scheduler — periodische Tasks (Node-Info-Updates, etc.)                        |
| `mariadb`   | MariaDB — relationale Datenbank für Kernentitäten                                 |
| `mongodb`   | MongoDB — Dokumentdatenbank für Aktivitäten und Logs                              |
| `redis`     | Redis — Task-Queue und Cache für Worker/Scheduler                                 |

## Voraussetzungen {#prerequisites}

- [Docker und Docker Compose](requirements) installiert
- [Proxmox VE](proxmoxve) eingerichtet (erforderlich für VM-Verwaltung)
- Ein SMTP-Server für den E-Mail-Versand (Zugangsdaten bereithalten)
- Optional: [Apache Guacamole](guacamole) für Remote-Desktop-Zugang

## Installation {#installation}

### Repository herunterladen {#download}

Lade die `docker-compose.yml` und die `.env.sample`-Dateien aus dem offiziellen Repository herunter:

```bash
mkdir openvle && cd openvle
curl -fsSLO https://raw.githubusercontent.com/inettgmbh/openvle/main/docker-compose.yml
curl -fsSL -o .env         https://raw.githubusercontent.com/inettgmbh/openvle/main/backend/.env.sample
curl -fsSL -o frontend.env https://raw.githubusercontent.com/inettgmbh/openvle/main/frontend/.env.sample
```

### Docker Images herunterladen {#pull}

```bash
docker compose pull
```

### Konfiguration {#configuration}

OpenVLE verwendet zwei Konfigurationsdateien auf Root-Ebene: `.env` für Backend, Worker, Scheduler und Compose-Variablen-Interpolation, sowie `frontend.env` für die Frontend-Runtime-Konfiguration.

#### Backend (`.env`) {#configure-backend}

Generiere zuerst sichere, zufällige Passwörter und Secrets für alle sicherheitsrelevanten Variablen:

```bash
sed -i \
  -e "s|AUTH_SECRET = \"\"|AUTH_SECRET = \"$(openssl rand -hex 32)\"|" \
  -e "s|SESSION_SECRET_TOKEN = \"\"|SESSION_SECRET_TOKEN = \"$(openssl rand -hex 32)\"|" \
  -e "s|MARIADB_PASSWORD = \"project\"|MARIADB_PASSWORD = \"$(openssl rand -hex 16)\"|" \
  -e "s|MARIADB_ROOT_PASSWORD = \"root\"|MARIADB_ROOT_PASSWORD = \"$(openssl rand -hex 16)\"|" \
  -e "s|MONGODB_PASSWORD = \"project\"|MONGODB_PASSWORD = \"$(openssl rand -hex 16)\"|" \
  -e "s|REDIS_PASSWORD = \"password\"|REDIS_PASSWORD = \"$(openssl rand -hex 16)\"|" \
  .env
```

:::caution
Dieser Befehl ersetzt die Standard-Passwörter einmalig durch zufällige Werte. Führe ihn **nur einmal** aus — bei erneuter Ausführung würden die bereits gesetzten Werte nicht mehr den Standardwerten entsprechen und der Befehl hätte keine Wirkung. Sichere die generierte `.env` anschließend, da die Passwörter nicht wiederherstellbar sind.

Falls du den `sed`-Befehl nicht verwenden möchtest, musst du die folgenden Variablen **unbedingt manuell** auf sichere Werte setzen: `AUTH_SECRET`, `SESSION_SECRET_TOKEN`, `MARIADB_PASSWORD`, `MARIADB_ROOT_PASSWORD`, `MONGODB_PASSWORD`, `REDIS_PASSWORD`. Die Standardwerte in der `.env.sample` sind unsicher und dürfen nicht im Produktivbetrieb verwendet werden.
:::

:::note MARIADB_ROOT_PASSWORD
`MARIADB_ROOT_PASSWORD` wird nur beim **initialen Start** benötigt — MariaDB übernimmt das Passwort bei der ersten Initialisierung und speichert es in der Datenbank. Nach dem ersten erfolgreichen Start kannst du die Variable aus der `.env` entfernen und das Passwort stattdessen an einem sicheren Ort aufbewahren (z. B. Passwort-Manager), falls du es für Wartungsarbeiten oder Fehlerfälle benötigst.
:::

Bearbeite anschließend die `.env` und setze die verbleibenden umgebungsspezifischen Variablen:

**CORS**

| Variable       | Beschreibung                                             | Beispiel                          |
| -------------- | -------------------------------------------------------- | --------------------------------- |
| `CORS_ORIGINS` | Erlaubte Ursprünge für CORS-Anfragen (URL des Frontends) | `["https://openvle.example.com"]` |

**Proxmox VE** — Zugangsdaten aus der [Proxmox VE Integration](proxmoxve)

| Variable          | Beschreibung                          | Beispiel                                 |
| ----------------- | ------------------------------------- | ---------------------------------------- |
| `PVE_HOSTNAME`    | Hostname und Port des Proxmox-Servers | `"proxmox.example.com:8006"`             |
| `PVE_USER`        | Proxmox-Benutzer                      | `"OpenVLE@pve"`                          |
| `PVE_TOKEN_NAME`  | Name des API-Tokens                   | `"prod01"`                               |
| `PVE_TOKEN_VALUE` | Geheimer Wert des API-Tokens          | `"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"` |
| `PVE_FQDN`        | FQDN des Proxmox-Servers              | `"proxmox.example.com:8006"`             |
| `PVE_VMS_POOL`    | Proxmox-Pool für verwaltete VMs       | `"OpenVLE-VMs"`                          |
| `PVE_VM_SUBNET`   | Subnetz für VMs                       | `"10.1.1.0/24"`                          |

**E-Mail / SMTP**

| Variable         | Beschreibung              | Beispiel                |
| ---------------- | ------------------------- | ----------------------- |
| `SMTP_HOST`      | SMTP-Server               | `"mail.example.com"`    |
| `SMTP_PORT`      | SMTP-Port                 | `465`                   |
| `SMTP_METHOD`    | Verbindungsmethode        | `"ssl"`                 |
| `SMTP_USERNAME`  | SMTP-Benutzername         | `"openvle@example.com"` |
| `SMTP_PASSWORD`  | SMTP-Passwort             | `"smtp-passwort"`       |
| `SMTP_FROM_MAIL` | Absenderadresse           | `"openvle@example.com"` |
| `SMTP_FROM_NAME` | Anzeigename des Absenders | `"OpenVLE"`             |

:::info
Die Variablen müssen in **Anführungszeichen (`" "`)** gesetzt werden, da es andernfalls beim Start zu Parsing-Fehlern kommt.
:::

:::note Vollständige Referenz
Die obige Tabelle zeigt nur die erforderlichen Variablen. Für optionale Einstellungen (Guacamole, LDAP, OIDC, Moodle, Sentry, etc.) siehe die [Konfigurationsreferenz](configuration).
:::

#### Frontend (`frontend.env`) {#configure-frontend}

Im Frontend muss lediglich die Backend-URL gesetzt werden:

```bash
VITE_BACKEND_URL='https://openvle.example.com/v1'
```

Weitere optionale Frontend-Variablen (z. B. Sentry) findest du in der [Konfigurationsreferenz](configuration?stack=frontend).

### Container starten {#start}

```bash
docker compose up -d
```

Docker erstellt automatisch alle notwendigen Verzeichnisse, initialisiert die Datenbanken und startet alle Services.

:::caution Erster Start
Beim ersten Start führt das Backend automatisch die Datenbank-Migration durch. Dies kann einige Minuten dauern. Warte bis alle Container den Status `healthy` erreicht haben, bevor du fortfährst.
:::

### Netzwerk und Ports {#ports}

In der Standard-`docker-compose.yml` werden nur zwei Ports nach außen veröffentlicht:

| Service    | Port | Bindung        |
| ---------- | ---- | -------------- |
| `frontend` | 80   | `0.0.0.0:80`   |
| `backend`  | 8000 | `0.0.0.0:8000` |

Alle anderen Container (MariaDB, MongoDB, Redis, Worker, Scheduler) kommunizieren ausschließlich intern über das Docker-Netzwerk und veröffentlichen keine Ports — das soll auch so bleiben.

:::note Reverse Proxy verwenden
Wenn ein [Reverse Proxy](reverse-proxy) eingesetzt wird (empfohlen), können die Port-Veröffentlichungen von Frontend und Backend in der `docker-compose.yml` entfernt oder auf `127.0.0.1` eingeschränkt werden, da der gesamte externe Zugriff dann zentral über den Reverse Proxy erfolgt. Beispiel:

```yaml
ports:
  - 127.0.0.1:80:80 # nur lokal erreichbar
  - 127.0.0.1:8000:8000
```

:::

### Standard-Administrator {#default-admin}

Nach dem ersten erfolgreichen Start wird automatisch ein Standard-Administrator-Konto erstellt:

|                  |           |
| ---------------- | --------- |
| **Benutzername** | `openvle` |
| **Passwort**     | `openvle` |

:::caution Passwort sofort ändern
Ändere das Passwort des Standard-Administrators **sofort** nach dem ersten Login. Erstelle anschließend für jeden Administrator ein persönliches Konto und deaktiviere oder lösche den Standard-Account, sobald die individuellen Konten eingerichtet sind.
:::

## Verifizierung {#verification}

### Container-Status prüfen {#verify-containers}

```bash
docker ps -a
```

Alle 7 Container sollten den Status `Running (healthy)` haben.

### Logs prüfen {#verify-logs}

```bash
docker logs openvle-backend 2>&1 | head -50
```

Die Logs sollten keine Fehlermeldungen zeigen und die erfolgreiche Datenbankverbindung bestätigen.

### API-Zugang testen {#verify-api}

Rufe die Systemeinstellungen über die API ab:

```bash
curl -s https://openvle.example.com/v1/system/settings | head -20
```

Eine JSON-Antwort mit den aktuellen Einstellungen bestätigt, dass Backend und Reverse Proxy korrekt konfiguriert sind. Eine leere oder fehlerhafte Antwort deutet auf ein Konfigurationsproblem hin.

### Weboberfläche prüfen {#verify-frontend}

Öffne `https://openvle.example.com` im Browser. Die Anmeldeseite sollte angezeigt werden.

## Fehlerbehebung {#troubleshooting}

| Problem                           | Lösung                                                                                                                                    |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Container startet nicht           | Prüfe die Logs mittels `docker logs <container-name>`. Weitere Informationen unter [Logs](../operations/logs).                            |
| Datenbank-Fehler beim Start       | Stelle sicher, dass die MariaDB- und MongoDB-Variablen in der `.env` korrekt gesetzt sind. Siehe [Konfigurationsreferenz](configuration). |
| Health-Check schlägt fehl         | Warte einige Minuten — die initiale Datenbank-Migration kann beim ersten Start länger dauern.                                             |
| Weboberfläche nicht erreichbar    | Stelle sicher, dass der Frontend-Container läuft und der [Reverse Proxy](reverse-proxy) korrekt konfiguriert ist.                         |
| API-Calls schlagen fehl           | Prüfe `CORS_ORIGINS` in der `.env` — die URL des Frontends muss enthalten sein.                                                           |
| E-Mail-Versand funktioniert nicht | Prüfe die SMTP-Variablen in der `.env` und teste die Verbindung zum SMTP-Server.                                                          |
| Proxmox-Verbindung schlägt fehl   | Prüfe `PVE_HOSTNAME`, `PVE_USER`, `PVE_TOKEN_NAME` und `PVE_TOKEN_VALUE`. Siehe [Proxmox VE Integration](proxmoxve).                      |
