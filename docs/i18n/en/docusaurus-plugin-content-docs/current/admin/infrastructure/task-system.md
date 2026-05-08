---
id: task-system
sidebar_label: Task System
sidebar_position: 35
status: finished
tags:
  - infrastructure
  - worker
  - scheduler
---

# Task System {#task-system}

OpenVLE executes resource-intensive and time-consuming operations asynchronously in the background. The task system is based on Redis Queue (RQ) and consists of **worker containers** for task execution and a **scheduler** for periodic tasks.

## Architecture {#architecture}

```
Backend/Scheduler → Redis Queue → Worker → Execution
```

1. **Enqueue** — The backend or scheduler places a task into a named Redis queue.
2. **Dequeue** — The responsible worker picks up the next task from its queue.
3. **Execution** — The worker executes the task (e.g., clone VM, send email).
4. **Result** — The result is stored in the database as a Task/SubTask and displayed to the user.

## Queues {#queues}

The system uses multiple named queues, each responsible for a specific area of tasks:

The environment variable `WORKER_MAX_RETRY` (default: `5`) controls the maximum number of retries for most queues. Some queues use a fixed value.

| Queue            | Purpose                                  | Max. retries       | Retry intervals |
| ---------------- | ---------------------------------------- | ------------------ | --------------- |
| `pve_vm_clone`   | VM cloning and deletion                  | `WORKER_MAX_RETRY` | 10s, 30s, 60s   |
| `pve_vm_actions` | VM actions (start, stop, reset, migrate) | `WORKER_MAX_RETRY` | 5s, 10s, 15s    |
| `pve_periodic`   | Proxmox polling (node info sync)         | 3 (fixed)          | 5s, 10s, 15s    |
| `mails`          | Email delivery                           | `WORKER_MAX_RETRY` | 30s, 60s, 120s  |
| `guacamole`      | Guacamole connection management          | `WORKER_MAX_RETRY` | 10s, 30s, 60s   |
| `moodle`         | Moodle course and user management        | `WORKER_MAX_RETRY` | 10s, 30s, 60s   |
| `core_periodic`  | Event lifecycle, email cleanup           | 3 (fixed)          | 5s, 10s, 15s    |

## Worker {#worker}

In production, three worker types run as separate Docker containers. Each type listens on specific queues:

| Worker type         | `SERVICE_ROLE`    | Queues                                                            | Replicas |
| ------------------- | ----------------- | ----------------------------------------------------------------- | -------- |
| **Worker**          | `worker`          | `core_periodic`, `guacamole`, `mails`, `moodle`, `pve_vm_actions` | 4        |
| **Worker VM-Clone** | `worker-vm-clone` | `pve_vm_clone`                                                    | 1        |
| **Worker Periodic** | `worker-periodic` | `pve_periodic`                                                    | 1        |

The separation into multiple worker types ensures that long-running VM clone operations do not block the processing of other tasks.

:::note Local development
In the local development environment, all queues can be processed by a single worker (`SERVICE_ROLE=worker-all`).
:::

### Task types {#task-types}

| Task                 | Queue            | Trigger        | Description                                                |
| -------------------- | ---------------- | -------------- | ---------------------------------------------------------- |
| Clone VM             | `pve_vm_clone`   | User/Scheduler | Creates a new VM from a VM template on Proxmox             |
| Start/stop/reset VM  | `pve_vm_actions` | User           | Starts, stops, or resets a VM on Proxmox                   |
| Delete VM            | `pve_vm_clone`   | User/Scheduler | Deletes a VM from Proxmox and cleans up the database       |
| Migrate VM           | `pve_vm_actions` | User           | Moves a VM to another Proxmox node                         |
| Send email           | `mails`          | System         | Sends notifications via SMTP                               |
| Provision Guacamole  | `guacamole`      | System         | Creates Guacamole users, connections, and sharing profiles |
| Clean up Guacamole   | `guacamole`      | System         | Deletes connections and sharing profiles                   |
| Deploy Moodle course | `moodle`         | System         | Duplicates Moodle template course for an event             |
| Enroll Moodle user   | `moodle`         | System         | Creates users in Moodle and enrolls them in courses        |
| Deploy event         | `core_periodic`  | Scheduler      | Creates all VMs and connections for an event               |
| Archive event        | `core_periodic`  | Scheduler      | Deletes all VMs and cleans up connections after event end  |

### Job dependencies {#job-dependencies}

Jobs can have dependencies on other jobs (`depends_on`). This creates execution chains, e.g.:

```
Delete Guacamole connection → Stop VM → Delete VM
```

The next job is only started when the previous one has completed successfully.

### Error handling {#error-handling}

Failed jobs are automatically retried. The maximum number of retries and the retry intervals are configured per queue (see [Queues](#queues)). After all attempts are exhausted, the job is marked as permanently failed.

Some errors are recognized as permanent and are not retried (e.g., SMTP error code 550 for an invalid recipient address).

:::note Logs
Failed jobs and their error messages are visible in the worker logs, e.g., `docker logs openvle-worker-vm-clone`. For more information on logging, see [Logs](../operations/logs).
:::

### Task tracking {#task-tracking}

Every asynchronous operation is tracked in the database via two models:

- **Task** — Represents a logical operation (e.g., "Clone VM")
- **SubTask** — Individual execution attempts of a task with status (`processing`, `success`, `error`), error message, and attempt number

Progress is displayed in the user interface.

## Scheduler {#scheduler}

The scheduler runs as its own container (`SERVICE_ROLE=scheduler`) and uses `rq cron` with cron expressions to enqueue periodic tasks into the Redis queue. The workers then execute them.

### Periodic tasks {#periodic-tasks}

| Task              | Queue           | Schedule                                                    | Description                                                                       |
| ----------------- | --------------- | ----------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Proxmox node info | `pve_periodic`  | Every `WORKER_PVE_PERIODIC_INTERVAL` seconds (default: 60s) | Synchronizes VM/template status and node information from the Proxmox cluster     |
| Event lifecycle   | `core_periodic` | Daily at 01:00 UTC                                          | Checks whether events need to be started or archived, sends advance notifications |
| Email cleanup     | `core_periodic` | Daily at 02:00 UTC                                          | Deletes sent emails older than `MAIL_MAX_AGE_WEEKS` (default: 4 weeks)            |

:::info Preparation time
The preparation time for automatic deployments and archiving is controlled via `EVENTS_START_PREP_TIME_DAYS` and `EVENTS_END_PREP_TIME_DAYS` (default: 7 days each). See [Configuration reference — Events](../install/configuration#events).
:::

## Component interaction {#interaction}

| Component           | Role                                 | Connections                                                  |
| ------------------- | ------------------------------------ | ------------------------------------------------------------ |
| **Backend**         | Creates tasks on user request        | → Redis (enqueue)                                            |
| **Scheduler**       | Creates periodic tasks on schedule   | → Redis (enqueue)                                            |
| **Redis**           | Queue system                         | Receives and holds jobs in named queues                      |
| **Worker** (4x)     | Processes general tasks              | → Redis, → MariaDB, → Proxmox, → Guacamole, → Moodle, → SMTP |
| **Worker VM-Clone** | Processes VM clone/delete operations | → Redis, → MariaDB, → Proxmox                                |
| **Worker Periodic** | Processes Proxmox polling            | → Redis, → MariaDB, → MongoDB, → Proxmox                     |

## Further reading {#further-reading}

- [Configuration reference — Worker](../install/configuration#worker) — Environment variables for worker and scheduler
- [Components](components) — Container details of all services
