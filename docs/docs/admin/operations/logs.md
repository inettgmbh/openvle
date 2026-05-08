---
id: logs
sidebar_label: Logging
sidebar_position: 20
status: finished
tags:
  - operations
  - logs
---

# Logging {#logging}

## Übersicht {#overview}

Diese Seite beschreibt die Logging-Infrastruktur von OpenVLE. Alle Container schreiben ihre Logs auf stdout, sodass sie über die Docker-Standard-Mechanismen (`docker logs`, `docker compose logs`) abrufbar sind.

## Services und deren Logs {#service-logs}

| Service               | Zweck                            | Besonderheiten                                                 |
| --------------------- | -------------------------------- | -------------------------------------------------------------- |
| `backend`             | FastAPI-API-Server               | Uvicorn-basierte Logs, inkl. HTTP-Zugriffe, Fehler, Start/Stop |
| `worker` (4 Replicas) | Allgemeine Hintergrundaufgaben   | Task-Ausführung, Fehler, Retry-Versuche                        |
| `worker-vm-clone`     | VM-Klon- und Lösch-Operationen   | Langlaufende Proxmox-Operationen                               |
| `worker-periodic`     | Proxmox-Polling                  | Periodische Status-Synchronisation                             |
| `scheduler`           | Zeitgesteuerte Tasks (`rq cron`) | Geplante und ausgeführte periodische Tasks                     |
| `frontend`            | Vue.js/Nginx Webserver           | HTTP-Access- und Error-Logs                                    |
| `mariadb`             | SQL-Datenbank                    | Start/Shutdown-Meldungen, Warnungen                            |
| `mongodb`             | NoSQL-Datenbank                  | Verbindungsinformationen, Authentifizierung                    |
| `redis`               | Task-Queue und Cache             | `loglevel warning`, minimale Ausgabe                           |

## Logs abrufen {#view-logs}

Docker bietet zwei Befehle zum Abrufen von Logs: `docker logs` für einen einzelnen Container (angesprochen über den Container-Namen) und `docker compose logs` für einen oder mehrere Services auf einmal (angesprochen über den Service-Namen aus der `docker-compose.yml`). Beide unterstützen die gleichen grundlegenden Optionen.

### Einzelner Container {#single-container}

```bash
docker logs [OPTIONEN] <container_name>
```

| Option          | Beschreibung                                                              |
| --------------- | ------------------------------------------------------------------------- |
| `-f`            | **Follow** — zeigt Live-Logs an, ähnlich wie `tail -f`                    |
| `-n` / `--tail` | Zeigt nur die letzten `n` Zeilen an                                       |
| `--since`       | Zeigt Logs seit einem bestimmten Zeitpunkt (`10m`, `2026-04-28T12:00:00`) |
| `--timestamps`  | Gibt Zeitstempel in den Logzeilen mit aus                                 |

**Beispiel:**

```bash
docker logs -f -n 100 openvle-backend
```

Zeigt die letzten 100 Zeilen des Containers `openvle-backend` und folgt dann weiter in Echtzeit. Die Anzeige kann mit `Ctrl+C` beendet werden.

### Mehrere Services {#multiple-services}

```bash
docker compose logs [OPTIONEN] [service_name ...]
```

| Option          | Beschreibung                                             |
| --------------- | -------------------------------------------------------- |
| `-f`            | **Follow** — zeigt kontinuierlich neue Logs              |
| `-n` / `--tail` | Gibt nur die letzten `n` Zeilen pro Container aus        |
| `--timestamps`  | Zeigt Zeitstempel an                                     |
| `--no-color`    | Deaktiviert farbliche Hervorhebungen (z. B. für Skripte) |

**Beispiel:**

```bash
docker compose logs -f -n 50 backend worker scheduler
```

Zeigt die letzten 50 Zeilen der drei Services und verfolgt die Logs in Echtzeit weiter.

### Fehlersuche {#error-search}

```bash
# Fehler im Backend suchen
docker compose logs backend | grep ERROR

# Fehler in allen Workern suchen
docker compose logs worker worker-vm-clone worker-periodic | grep ERROR
```

## Log-Format {#log-format}

FastAPI nutzt Uvicorn, das standardmäßig Logzeilen im folgenden Format erzeugt:

```
INFO:     127.0.0.1:54321 - "GET /v1/users HTTP/1.1" 200 OK
ERROR:    Exception in ASGI application: ...
```

Die Worker-Logs zeigen Task-Ausführungen mit Status, Dauer und ggf. Fehlermeldungen.

## Zentrale Logaggregation {#log-aggregation}

Für produktive Umgebungen wird empfohlen, alle Services mit einem zentralen Logging-Driver (z. B. `gelf`, `fluentd`, oder ELK/EFK-Stack) zu versehen. Dafür bietet sich eine `docker-compose.override.yml` an, um die Update-Fähigkeit beizubehalten.

**Beispiel für GELF (Graylog):**

```yaml
logging:
  driver: gelf
  options:
    gelf-address: udp://graylog.example.org:12201
    tag: openvle-backend
```

:::note Replizierte Worker
Da der `worker`-Service im Produktivbetrieb mit 4 Replicas läuft, empfiehlt sich bei zentraler Logaggregation das Anhängen von Service- und Instanznamen als Metadaten, um Logs den einzelnen Replicas zuordnen zu können.
:::

## Typische Anwendungsfälle {#use-cases}

- **Fehlersuche** — Errors und Tracebacks in Backend- oder Worker-Logs
- **Task-Analyse** — Dauer und Status von Worker-Jobs prüfen
- **Scheduler-Monitoring** — Prüfen ob periodische Tasks planmäßig laufen
- **Audit** — Unautorisierte API-Zugriffe erkennen
- **Frontend-Debugging** — Nginx-Access- und Error-Logs bei Zugriffsproblemen
