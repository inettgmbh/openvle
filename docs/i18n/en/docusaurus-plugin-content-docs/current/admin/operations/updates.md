---
id: updates
sidebar_label: Updates
sidebar_position: 30
status: finished
tags:
  - operations
  - updates
---

# Updates {#updates}

Updates are delivered via new Docker images. Backend, frontend, and all workers share a common repository and are updated together.

:::caution Before every update
Create a backup of all databases before performing an update. See [Backups & Restore](backups-restore).
:::

## Procedure {#procedure}

1. **Create a backup** — see [Backups & Restore](backups-restore)
2. **Pull new images:**
   ```bash
   docker compose pull
   ```
3. **Restart containers:**
   ```bash
   docker compose down && docker compose up -d
   ```
4. **Check status:**
   ```bash
   docker ps -a
   ```
   All containers should show the status `Running (healthy)`.
5. **Check logs** — see [Logging](logs)

## Database Migrations {#migrations}

The backend automatically runs pending database migrations on startup. Which container executes the migration (backend or worker) is controlled via a lock mechanism — see [Databases — Initialization](../infrastructure/databases#mariadb-init).

Check the logs after startup for successful migrations:

```bash
docker logs openvle-backend 2>&1 | head -50
```

## Apache Guacamole {#guacamole}

Apache Guacamole runs as a separate Docker stack and is updated independently from OpenVLE.

:::caution Database Schema
For major version updates of Guacamole, a manual update of the database schema may be required. Check the Apache Guacamole release notes for schema changes and run the provided upgrade scripts if necessary.
:::

## Frontend Cache {#frontend-cache}

:::note Browser Cache
After an update, it may be necessary to clear the browser cache so that the new frontend files are loaded.
:::
