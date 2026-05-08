---
id: databases
sidebar_label: Databases
sidebar_position: 30
status: finished
tags:
  - infrastructure
  - databases
---

# Databases {#databases}

OpenVLE uses three different database systems, each specialized for different tasks: MariaDB for structured core data, MongoDB for activities and logs, and Redis as a task queue and cache.

## Overview {#overview}

| Database    | Type                   | Stored Data                                                                       | Persistence                        |
| ----------- | ---------------------- | --------------------------------------------------------------------------------- | ---------------------------------- |
| **MariaDB** | Relational (SQL)       | Core entities: users, roles, permissions, environments, events, VMs, VM templates | Volume `./mariadb/data`            |
| **MongoDB** | Document-based (NoSQL) | Activities, system events, audit logs, change histories                           | Volume `./mongodb`                 |
| **Redis**   | In-Memory (Key-Value)  | Task queue, cache, worker/scheduler communication                                 | AOF persistence (`appendonly yes`) |

## MariaDB {#mariadb}

MariaDB is the primary database and stores all structured core entities of the system:

- **Users and Roles** -- Accounts, role assignments, password hashes
- **Permissions** -- Permission definitions and assignments (see [Permission System](permission-system))
- **Environments and Events** -- Environments, event schedules, participant assignments
- **VMs and VM Templates** -- Virtual machines, their status, and assignment to events
- **System Settings** -- Global configuration and settings

### Initialization and Migration {#mariadb-init}

On first startup, the backend and worker containers automatically handle database initialization and migration. Which container performs the migration is controlled via a lock mechanism -- the container that acquires the lock first executes the migration. This creates the database schema and initial data (e.g., the default administrator account and default permissions).

## MongoDB {#mongodb}

MongoDB stores non-relational data that does not require a fixed table structure:

- **Activities** -- User actions (e.g., "User X started VM Y") that are displayed in the activity overview of the user interface

Access is exclusively through the backend. MongoDB is not directly accessible from outside.

## Redis {#redis}

Redis does not serve as a traditional database but rather as a communication layer between application components:

- **Task Queue** -- The backend enqueues tasks into Redis queues that are processed by the worker (see [Task System](task-system))
- **Scheduler Queue** -- The scheduler places periodic tasks into Redis
- **Cache** -- Temporary storage for frequently accessed data

Redis is configured with AOF (Append Only File), so queue data is preserved even after a restart. Access is password-protected.

## Separation of Databases {#separation}

The division into three systems follows the principle of using each database for its area of strength:

| Requirement                     | Database | Rationale                                      |
| ------------------------------- | -------- | ---------------------------------------------- |
| Structured data with relations  | MariaDB  | Foreign keys, transactions, ACID guarantees    |
| Flexible, schema-free documents | MongoDB  | Varying document structures, efficient logging |
| Fast queue operations           | Redis    | In-memory speed, native queue support          |

## Further Information {#further-reading}

- [Configuration Reference -- MariaDB](../install/configuration#mariadb) -- All MariaDB environment variables
- [Configuration Reference -- MongoDB](../install/configuration#mongodb) -- All MongoDB environment variables
- [Configuration Reference -- Redis](../install/configuration#redis) -- All Redis environment variables
- [Backups & Restore](../operations/backups-restore) -- Backup and restoration of the databases
