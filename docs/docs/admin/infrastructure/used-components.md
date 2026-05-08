---
id: components
sidebar_label: Verwendete Komponenten
sidebar_position: 20
status: finished
tags:
  - infrastructure
  - architecture
---

# Verwendete Komponenten {#used-components}

Diese Seite beschreibt die Docker-Container des OpenVLE-Stacks im Detail: Konfiguration, Ports, Abhängigkeiten und Health Checks. Einen Überblick über alle Komponenten und das Architekturdiagramm findest du auf der [Infrastruktur-Übersicht](infrastructure).

:::caution Gilt nur für Standard-Setup
Diese Seite bezieht sich auf den Standardzustand des offiziellen Repositories. Bei abweichenden Setups (z. B. durch eigene Dockerfiles, angepasste `.env`/`frontend.env`-Dateien oder andere Infrastruktur) können die Informationen hiervon abweichen.
:::

## Anwendung {#application}

Backend und Frontend bilden die Anwendungsschicht von OpenVLE. Das Backend stellt die REST-API bereit, das Frontend die Weboberfläche.

| Service    | Beschreibung                                                                                          | Port      | Abhängigkeiten                         |
| ---------- | ----------------------------------------------------------------------------------------------------- | --------- | -------------------------------------- |
| `backend`  | Python 3 / FastAPI — REST-API, Geschäftslogik, Authentifizierung, Proxmox-Integration, E-Mail-Versand | 8000 → 80 | MariaDB, MongoDB, Redis (alle healthy) |
| `frontend` | Vue.js / Nginx — Weboberfläche, über die alle Funktionen zugänglich sind                              | 80 → 80   | `backend` (clientseitig im Browser)    |

- Das **Backend** (`SERVICE_ROLE=backend`) ist die zentrale Komponente: Es verarbeitet API-Anfragen, prüft Berechtigungen, koordiniert alle Prozesse und reiht Hintergrundaufgaben in die Redis-Queue ein.
- Das **Frontend** wird beim Build kompiliert und in einem Nginx-Container bereitgestellt. Über `frontend.env` werden API-URL und optionale Einstellungen (z. B. Sentry-DSN) konfiguriert. Optional können eigene Logos via `static/`-Mounts eingebunden werden.

## Hintergrundverarbeitung {#background-processing}

Das Task-System besteht aus mehreren Worker-Containern und einem Scheduler. Die Aufteilung auf spezialisierte Worker stellt sicher, dass langlaufende Operationen (z. B. VM-Klonen) andere Aufgaben nicht blockieren. Alle Worker und der Scheduler benötigen MariaDB (healthy) und Redis (healthy).

| Service           | `SERVICE_ROLE`    | Queues                                                            | Replicas | Beschreibung                                                   |
| ----------------- | ----------------- | ----------------------------------------------------------------- | -------- | -------------------------------------------------------------- |
| `worker`          | `worker`          | `core_periodic`, `guacamole`, `mails`, `moodle`, `pve_vm_actions` | 4        | Allgemeine Aufgaben: VM-Aktionen, E-Mail, Guacamole, Moodle    |
| `worker-vm-clone` | `worker-vm-clone` | `pve_vm_clone`                                                    | 1        | VM-Klon- und Lösch-Operationen (langlaufend)                   |
| `worker-periodic` | `worker-periodic` | `pve_periodic`                                                    | 1        | Proxmox-Polling (VM-/Template-Status, Node-Info)               |
| `scheduler`       | `scheduler`       | —                                                                 | 1        | Reiht periodische Aufgaben nach Cron-Zeitplan in die Queue ein |

Weitere Details zum Task-System, den Queues und der Fehlerbehandlung findest du unter [Task-System](task-system).

## Datenbanken {#databases}

Drei Datenbanksysteme decken unterschiedliche Anforderungen ab. Keiner der Datenbank-Container veröffentlicht Ports — sie sind ausschließlich intern erreichbar.

| Service   | Typ               | Zweck                                                                             | Persistenz                   | Health Check                           |
| --------- | ----------------- | --------------------------------------------------------------------------------- | ---------------------------- | -------------------------------------- |
| `mariadb` | MariaDB (SQL)     | Kernentitäten: Benutzer, Rollen, Berechtigungen, Umgebungen, Veranstaltungen, VMs | `./mariadb/data`             | `mariadb-admin ping`                   |
| `mongodb` | MongoDB (NoSQL)   | Aktivitäten, System-Events, Audit-Logs, Änderungsverläufe                         | `./mongodb`                  | `mongosh eval db.adminCommand('ping')` |
| `redis`   | Redis (In-Memory) | Task-Queue und Cache für Worker/Scheduler                                         | AOF + Snapshot (`save 60 1`) | `redis-cli incr ping`                  |

- **MariaDB** — Schema und initiale Daten werden beim Erststart automatisch durch Backend/Worker angelegt (Migration mit Lock-Mechanismus). Zugriff durch Backend, Worker und Scheduler.
- **MongoDB** — Zugriff ausschließlich über das Backend. Authentifizierung über Root-User aus `.env`.
- **Redis** — Passwortgeschützt über `.env`. Konfiguriert mit AOF (`appendonly yes`) und periodischem Snapshot für persistente Speicherung.

Weitere Details zur Datenarchitektur findest du unter [Datenbanken](databases).

## Entwicklungsumgebung {#dev-environment}

Die folgenden Services sind nicht im Produktions-Stack enthalten und stehen nur in der Entwicklungs- bzw. lokalen Umgebung zur Verfügung:

| Service      | Konfiguration            | Zweck                                      | Port                       |
| ------------ | ------------------------ | ------------------------------------------ | -------------------------- |
| `phpmyadmin` | `docker-compose.dev.yml` | Web-GUI zur MariaDB-Verwaltung             | 8888                       |
| `fake-smtp`  | `docker-compose.dev.yml` | Lokaler SMTP-Server zum Testen von E-Mails | 1025 (SMTP), 8088 (Web-UI) |

:::note Internes Netzwerk
Alle Services sind intern über das Docker-Netzwerk `openvle-internal` verbunden. Nur das Frontend und Backend sind extern exponiert. Weitere Details findest du unter [Netzwerk & Docker](networking).
:::
