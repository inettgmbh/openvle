---
id: task-system
sidebar_label: Task-System
sidebar_position: 35
status: finished
tags:
  - infrastructure
  - worker
  - scheduler
---

# Task-System {#task-system}

OpenVLE führt ressourcenintensive und zeitaufwendige Operationen asynchron im Hintergrund aus. Das Task-System basiert auf Redis Queue (RQ) und besteht aus **Worker-Containern** für die Aufgabenausführung und einem **Scheduler** für periodische Aufgaben.

## Architektur {#architecture}

```
Backend/Scheduler → Redis Queue → Worker → Ausführung
```

1. **Enqueue** — Das Backend oder der Scheduler legt eine Aufgabe in eine benannte Redis-Queue.
2. **Dequeue** — Der zuständige Worker holt die nächste Aufgabe aus seiner Queue.
3. **Ausführung** — Der Worker führt die Aufgabe aus (z. B. VM klonen, E-Mail senden).
4. **Ergebnis** — Das Ergebnis wird in der Datenbank als Task/SubTask gespeichert und dem Benutzer angezeigt.

## Queues {#queues}

Das System verwendet mehrere benannte Queues, die jeweils für einen bestimmten Aufgabenbereich zuständig sind:

Die Umgebungsvariable `WORKER_MAX_RETRY` (Standard: `5`) steuert die maximale Anzahl an Wiederholungen für die meisten Queues. Einige Queues verwenden einen festen Wert.

| Queue            | Zweck                                        | Max. Retries       | Retry-Intervalle |
| ---------------- | -------------------------------------------- | ------------------ | ---------------- |
| `pve_vm_clone`   | VM-Klonen und -Löschen                       | `WORKER_MAX_RETRY` | 10s, 30s, 60s    |
| `pve_vm_actions` | VM-Aktionen (Start, Stop, Reset, Migrate)    | `WORKER_MAX_RETRY` | 5s, 10s, 15s     |
| `pve_periodic`   | Proxmox-Polling (Node-Info-Sync)             | 3 (fest)           | 5s, 10s, 15s     |
| `mails`          | E-Mail-Versand                               | `WORKER_MAX_RETRY` | 30s, 60s, 120s   |
| `guacamole`      | Guacamole-Verbindungsverwaltung              | `WORKER_MAX_RETRY` | 10s, 30s, 60s    |
| `moodle`         | Moodle-Kurs- und Benutzerverwaltung          | `WORKER_MAX_RETRY` | 10s, 30s, 60s    |
| `core_periodic`  | Veranstaltungs-Lifecycle, E-Mail-Bereinigung | 3 (fest)           | 5s, 10s, 15s     |

## Worker {#worker}

Im Produktivbetrieb laufen drei Worker-Typen als separate Docker-Container. Jeder Typ lauscht auf bestimmte Queues:

| Worker-Typ          | `SERVICE_ROLE`    | Queues                                                            | Replicas |
| ------------------- | ----------------- | ----------------------------------------------------------------- | -------- |
| **Worker**          | `worker`          | `core_periodic`, `guacamole`, `mails`, `moodle`, `pve_vm_actions` | 4        |
| **Worker VM-Clone** | `worker-vm-clone` | `pve_vm_clone`                                                    | 1        |
| **Worker Periodic** | `worker-periodic` | `pve_periodic`                                                    | 1        |

Die Aufteilung auf mehrere Worker-Typen stellt sicher, dass langlaufende VM-Klon-Operationen nicht die Verarbeitung anderer Aufgaben blockieren.

:::note Lokale Entwicklung
In der lokalen Entwicklungsumgebung können alle Queues von einem einzelnen Worker (`SERVICE_ROLE=worker-all`) abgearbeitet werden.
:::

### Aufgabentypen {#task-types}

| Aufgabe                      | Queue            | Auslöser           | Beschreibung                                                       |
| ---------------------------- | ---------------- | ------------------ | ------------------------------------------------------------------ |
| VM klonen                    | `pve_vm_clone`   | Benutzer/Scheduler | Erstellt eine neue VM aus einer VM-Vorlage auf Proxmox             |
| VM starten/stoppen/resetten  | `pve_vm_actions` | Benutzer           | Startet, stoppt oder setzt eine VM auf Proxmox zurück              |
| VM löschen                   | `pve_vm_clone`   | Benutzer/Scheduler | Löscht eine VM von Proxmox und bereinigt die Datenbank             |
| VM migrieren                 | `pve_vm_actions` | Benutzer           | Verschiebt eine VM auf einen anderen Proxmox-Node                  |
| E-Mail versenden             | `mails`          | System             | Versendet Benachrichtigungen über SMTP                             |
| Guacamole provisionieren     | `guacamole`      | System             | Erstellt Guacamole-Benutzer, Verbindungen und Sharing-Profile      |
| Guacamole bereinigen         | `guacamole`      | System             | Löscht Verbindungen und Sharing-Profile                            |
| Moodle-Kurs deployen         | `moodle`         | System             | Dupliziert Moodle-Vorlagenkurs für eine Veranstaltung              |
| Moodle-Benutzer einschreiben | `moodle`         | System             | Erstellt Benutzer in Moodle und schreibt sie in Kurse ein          |
| Veranstaltung deployen       | `core_periodic`  | Scheduler          | Erstellt alle VMs und Verbindungen für eine Veranstaltung          |
| Veranstaltung archivieren    | `core_periodic`  | Scheduler          | Löscht alle VMs und bereinigt Verbindungen nach Veranstaltungsende |

### Job-Abhängigkeiten {#job-dependencies}

Jobs können Abhängigkeiten zu anderen Jobs haben (`depends_on`). Damit werden Ausführungsketten gebildet, z. B.:

```
Guacamole-Verbindung löschen → VM stoppen → VM löschen
```

Der nächste Job wird erst gestartet, wenn der vorherige erfolgreich abgeschlossen ist.

### Fehlerbehandlung {#error-handling}

Fehlgeschlagene Jobs werden automatisch wiederholt. Die maximale Anzahl an Wiederholungen und die Retry-Intervalle sind pro Queue konfiguriert (siehe [Queues](#queues)). Nach Ausschöpfung aller Versuche wird der Job als dauerhaft fehlgeschlagen markiert.

Einige Fehler werden als permanent erkannt und nicht wiederholt (z. B. SMTP-Fehlercode 550 bei ungültiger Empfängeradresse).

:::note Logs
Fehlerhafte Jobs und ihre Fehlermeldungen sind in den Worker-Logs sichtbar, z. B. `docker logs openvle-worker-vm-clone`. Weitere Informationen zum Logging findest du unter [Logs](../operations/logs).
:::

### Task-Tracking {#task-tracking}

Jede asynchrone Operation wird in der Datenbank über zwei Modelle nachverfolgt:

- **Task** — Repräsentiert eine logische Operation (z. B. "VM klonen")
- **SubTask** — Einzelne Ausführungsversuche eines Tasks mit Status (`processing`, `success`, `error`), Fehlermeldung und Versuchsnummer

Der Fortschritt wird in der Benutzeroberfläche angezeigt.

## Scheduler {#scheduler}

Der Scheduler läuft als eigener Container (`SERVICE_ROLE=scheduler`) und verwendet `rq cron` mit Cron-Expressions, um periodische Aufgaben in die Redis-Queue einzureihen. Die Worker führen diese dann aus.

### Periodische Aufgaben {#periodic-tasks}

| Aufgabe                  | Queue           | Zeitplan                                                     | Beschreibung                                                                                         |
| ------------------------ | --------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| Proxmox-Node-Info        | `pve_periodic`  | Alle `WORKER_PVE_PERIODIC_INTERVAL` Sekunden (Standard: 60s) | Synchronisiert VM-/Template-Status und Node-Informationen aus dem Proxmox-Cluster                    |
| Veranstaltungs-Lifecycle | `core_periodic` | Täglich um 01:00 UTC                                         | Prüft ob Veranstaltungen gestartet oder archiviert werden müssen, versendet Vorab-Benachrichtigungen |
| E-Mail-Bereinigung       | `core_periodic` | Täglich um 02:00 UTC                                         | Löscht versendete E-Mails, die älter als `MAIL_MAX_AGE_WEEKS` (Standard: 4 Wochen) sind              |

:::info Vorbereitungszeit
Die Vorbereitungszeit für automatische Deployments und Archivierungen wird über `EVENTS_START_PREP_TIME_DAYS` und `EVENTS_END_PREP_TIME_DAYS` gesteuert (Standard: jeweils 7 Tage). Siehe [Konfigurationsreferenz — Veranstaltungen](../install/configuration#events).
:::

## Zusammenspiel der Komponenten {#interaction}

| Komponente          | Rolle                                       | Verbindungen                                                 |
| ------------------- | ------------------------------------------- | ------------------------------------------------------------ |
| **Backend**         | Erstellt Aufgaben auf Benutzeranfrage       | → Redis (Enqueue)                                            |
| **Scheduler**       | Erstellt periodische Aufgaben nach Zeitplan | → Redis (Enqueue)                                            |
| **Redis**           | Queue-System                                | Empfängt und hält Jobs in benannten Queues                   |
| **Worker** (4x)     | Verarbeitet allgemeine Aufgaben             | → Redis, → MariaDB, → Proxmox, → Guacamole, → Moodle, → SMTP |
| **Worker VM-Clone** | Verarbeitet VM-Klon/Lösch-Operationen       | → Redis, → MariaDB, → Proxmox                                |
| **Worker Periodic** | Verarbeitet Proxmox-Polling                 | → Redis, → MariaDB, → MongoDB, → Proxmox                     |

## Weiterführende Informationen {#further-reading}

- [Konfigurationsreferenz — Worker](../install/configuration#worker) — Umgebungsvariablen für Worker und Scheduler
- [Verwendete Komponenten](components) — Container-Details aller Services
