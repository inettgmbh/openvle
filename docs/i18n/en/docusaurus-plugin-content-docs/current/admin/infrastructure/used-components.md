---
id: components
sidebar_label: Used Components
sidebar_position: 20
status: finished
tags:
  - infrastructure
  - architecture
---

# Used Components {#used-components}

This page describes the Docker containers of the OpenVLE stack in detail: configuration, ports, dependencies, and health checks. For an overview of all components and the architecture diagram, see the [Infrastructure Overview](infrastructure).

:::caution Applies Only to Standard Setup
This page refers to the default state of the official repository. For divergent setups (e.g., custom Dockerfiles, modified `.env`/`frontend.env` files, or different infrastructure), the information may differ.
:::

## Application {#application}

Backend and frontend form the application layer of OpenVLE. The backend provides the REST API, the frontend provides the web interface.

| Service    | Description                                                                                         | Port      | Dependencies                           |
| ---------- | --------------------------------------------------------------------------------------------------- | --------- | -------------------------------------- |
| `backend`  | Python 3 / FastAPI -- REST API, business logic, authentication, Proxmox integration, email delivery | 8000 → 80 | MariaDB, MongoDB, Redis (all healthy)  |
| `frontend` | Vue.js / Nginx -- Web interface through which all features are accessible                           | 80 → 80   | `backend` (client-side in the browser) |

- The **Backend** (`SERVICE_ROLE=backend`) is the central component: it processes API requests, checks permissions, coordinates all processes, and enqueues background tasks into the Redis queue.
- The **Frontend** is compiled at build time and served in an Nginx container. The API URL and optional settings (e.g., Sentry DSN) are configured via `frontend.env`. Optionally, custom logos can be mounted via `static/` mounts.

## Background Processing {#background-processing}

The task system consists of multiple worker containers and a scheduler. The division into specialized workers ensures that long-running operations (e.g., VM cloning) do not block other tasks. All workers and the scheduler require MariaDB (healthy) and Redis (healthy).

| Service           | `SERVICE_ROLE`    | Queues                                                            | Replicas | Description                                               |
| ----------------- | ----------------- | ----------------------------------------------------------------- | -------- | --------------------------------------------------------- |
| `worker`          | `worker`          | `core_periodic`, `guacamole`, `mails`, `moodle`, `pve_vm_actions` | 4        | General tasks: VM actions, email, Guacamole, Moodle       |
| `worker-vm-clone` | `worker-vm-clone` | `pve_vm_clone`                                                    | 1        | VM clone and delete operations (long-running)             |
| `worker-periodic` | `worker-periodic` | `pve_periodic`                                                    | 1        | Proxmox polling (VM/template status, node info)           |
| `scheduler`       | `scheduler`       | --                                                                | 1        | Enqueues periodic tasks into the queue on a cron schedule |

For more details on the task system, queues, and error handling, see [Task System](task-system).

## Databases {#databases}

Three database systems cover different requirements. None of the database containers publish ports -- they are only accessible internally.

| Service   | Type              | Purpose                                                             | Persistence                  | Health Check                           |
| --------- | ----------------- | ------------------------------------------------------------------- | ---------------------------- | -------------------------------------- |
| `mariadb` | MariaDB (SQL)     | Core entities: users, roles, permissions, environments, events, VMs | `./mariadb/data`             | `mariadb-admin ping`                   |
| `mongodb` | MongoDB (NoSQL)   | Activities, system events, audit logs, change histories             | `./mongodb`                  | `mongosh eval db.adminCommand('ping')` |
| `redis`   | Redis (In-Memory) | Task queue and cache for worker/scheduler                           | AOF + Snapshot (`save 60 1`) | `redis-cli incr ping`                  |

- **MariaDB** -- Schema and initial data are automatically created on first startup by the backend/worker (migration with lock mechanism). Accessed by backend, worker, and scheduler.
- **MongoDB** -- Accessed exclusively by the backend. Authentication via root user from `.env`.
- **Redis** -- Password-protected via `.env`. Configured with AOF (`appendonly yes`) and periodic snapshots for persistent storage.

For more details on the data architecture, see [Databases](databases).

## Development Environment {#dev-environment}

The following services are not included in the production stack and are only available in the development or local environment:

| Service      | Configuration            | Purpose                              | Port                       |
| ------------ | ------------------------ | ------------------------------------ | -------------------------- |
| `phpmyadmin` | `docker-compose.dev.yml` | Web GUI for MariaDB administration   | 8888                       |
| `fake-smtp`  | `docker-compose.dev.yml` | Local SMTP server for testing emails | 1025 (SMTP), 8088 (Web UI) |

:::note Internal Network
All services are internally connected via the Docker network `openvle-internal`. Only the frontend and backend are externally exposed. For more details, see [Networking & Docker](networking).
:::
