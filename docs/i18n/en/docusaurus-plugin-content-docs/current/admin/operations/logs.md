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

## Overview {#overview}

This page describes the logging infrastructure of OpenVLE. All containers write their logs to stdout, making them accessible via the standard Docker mechanisms (`docker logs`, `docker compose logs`).

## Services and Their Logs {#service-logs}

| Service               | Purpose                        | Details                                                   |
| --------------------- | ------------------------------ | --------------------------------------------------------- |
| `backend`             | FastAPI API server             | Uvicorn-based logs, incl. HTTP access, errors, start/stop |
| `worker` (4 replicas) | General background tasks       | Task execution, errors, retry attempts                    |
| `worker-vm-clone`     | VM clone and delete operations | Long-running Proxmox operations                           |
| `worker-periodic`     | Proxmox polling                | Periodic status synchronization                           |
| `scheduler`           | Scheduled tasks (`rq cron`)    | Scheduled and executed periodic tasks                     |
| `frontend`            | Vue.js/Nginx web server        | HTTP access and error logs                                |
| `mariadb`             | SQL database                   | Start/shutdown messages, warnings                         |
| `mongodb`             | NoSQL database                 | Connection information, authentication                    |
| `redis`               | Task queue and cache           | `loglevel warning`, minimal output                        |

## Viewing Logs {#view-logs}

Docker provides two commands for viewing logs: `docker logs` for a single container (referenced by container name) and `docker compose logs` for one or more services at once (referenced by service name from `docker-compose.yml`). Both support the same basic options.

### Single Container {#single-container}

```bash
docker logs [OPTIONS] <container_name>
```

| Option          | Description                                                              |
| --------------- | ------------------------------------------------------------------------ |
| `-f`            | **Follow** — shows live logs, similar to `tail -f`                       |
| `-n` / `--tail` | Shows only the last `n` lines                                            |
| `--since`       | Shows logs since a specific point in time (`10m`, `2026-04-28T12:00:00`) |
| `--timestamps`  | Includes timestamps in the log lines                                     |

**Example:**

```bash
docker logs -f -n 100 openvle-backend
```

Shows the last 100 lines of the `openvle-backend` container and then continues following in real time. The display can be stopped with `Ctrl+C`.

### Multiple Services {#multiple-services}

```bash
docker compose logs [OPTIONS] [service_name ...]
```

| Option          | Description                                       |
| --------------- | ------------------------------------------------- |
| `-f`            | **Follow** — continuously shows new logs          |
| `-n` / `--tail` | Shows only the last `n` lines per container       |
| `--timestamps`  | Shows timestamps                                  |
| `--no-color`    | Disables colored highlighting (e.g., for scripts) |

**Example:**

```bash
docker compose logs -f -n 50 backend worker scheduler
```

Shows the last 50 lines of the three services and continues following the logs in real time.

### Error Search {#error-search}

```bash
# Search for errors in the backend
docker compose logs backend | grep ERROR

# Search for errors in all workers
docker compose logs worker worker-vm-clone worker-periodic | grep ERROR
```

## Log Format {#log-format}

FastAPI uses Uvicorn, which by default produces log lines in the following format:

```
INFO:     127.0.0.1:54321 - "GET /v1/users HTTP/1.1" 200 OK
ERROR:    Exception in ASGI application: ...
```

Worker logs show task executions with status, duration, and error messages where applicable.

## Centralized Log Aggregation {#log-aggregation}

For production environments, it is recommended to configure all services with a centralized logging driver (e.g., `gelf`, `fluentd`, or an ELK/EFK stack). A `docker-compose.override.yml` is well-suited for this to maintain update compatibility.

**Example for GELF (Graylog):**

```yaml
logging:
  driver: gelf
  options:
    gelf-address: udp://graylog.example.org:12201
    tag: openvle-backend
```

:::note Replicated Workers
Since the `worker` service runs with 4 replicas in production, it is recommended to append service and instance names as metadata when using centralized log aggregation, so that logs can be attributed to individual replicas.
:::

## Typical Use Cases {#use-cases}

- **Error investigation** — Errors and tracebacks in backend or worker logs
- **Task analysis** — Check duration and status of worker jobs
- **Scheduler monitoring** — Verify that periodic tasks are running on schedule
- **Audit** — Detect unauthorized API access
- **Frontend debugging** — Nginx access and error logs for access issues
