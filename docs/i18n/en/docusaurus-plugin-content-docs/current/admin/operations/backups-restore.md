---
id: backups-restore
sidebar_label: Backups & Restore
sidebar_position: 10
status: finished
tags:
  - operations
  - backup
---

# Backups & Restore {#backups-restore}

Once you are using the software in a production environment, we recommend performing regular backups. This helps protect against human errors, such as accidentally deleting objects, as well as data loss due to hardware failures.

## Proxmox VM Backup (recommended) {#proxmox-backup}

Since OpenVLE is typically operated as a VM on the Proxmox VE cluster, the simplest and recommended approach is a **native Proxmox backup of the entire VM**. This secures all databases, configuration files, and Docker volumes in a single step.

Proxmox supports various backup targets (e.g., Proxmox Backup Server, NFS, CIFS) and allows both manual and scheduled backups via the Proxmox web interface or CLI. In case of failure, the entire VM can be restored from the backup.

:::note
The Proxmox backup configuration is done on the Proxmox VE cluster itself and is not part of the OpenVLE configuration. For more information, see the [Proxmox VE Backup Documentation](https://pve.proxmox.com/wiki/Backup_and_Restore).
:::

## Database Dumps (supplementary) {#database-dumps}

In addition to VM backups, database dumps can be useful for granular restores — e.g., when only a single database needs to be reset without restoring the entire VM.

## What needs to be backed up? {#what-to-backup}

| Component            | Data                                            | Storage Location | Priority |
| -------------------- | ----------------------------------------------- | ---------------- | -------- |
| MariaDB              | Core entities (users, VMs, events, roles, etc.) | `./mariadb/data` | Critical |
| MongoDB              | Activities, logs, system events                 | `./mongodb`      | High     |
| Redis                | Task queue, cache                               | In-memory + AOF  | Low      |
| `.env`               | Backend configuration, secrets                  | `./`             | Critical |
| `frontend.env`       | Frontend configuration                          | `./`             | Critical |
| `docker-compose.yml` | Service definitions                             | `./`             | Medium   |

:::note Redis
Redis primarily serves as a task queue and cache. Data is automatically restored from the AOF file on restart. A separate backup is generally not necessary.
:::

## Create Backup {#create-backup}

### MariaDB {#backup-mariadb}

The MariaDB database contains all core entities and should be backed up daily:

```bash
docker exec openvle-mariadb mariadb-dump \
  -u "$MARIADB_USER" \
  -p"$MARIADB_PASSWORD" \
  "$MARIADB_DATABASE" > backup_mariadb_$(date +%Y%m%d).sql
```

The variables (`MARIADB_USER`, `MARIADB_PASSWORD`, `MARIADB_DATABASE`) can be found in your `.env`. See [Configuration Reference](../install/configuration#mariadb).

### MongoDB {#backup-mongodb}

MongoDB stores activities, logs, and system events:

```bash
docker exec openvle-mongodb mongodump \
  --username="$MONGODB_USER" \
  --password="$MONGODB_PASSWORD" \
  --db="$MONGODB_DATABASE" \
  --archive > backup_mongodb_$(date +%Y%m%d).archive
```

### Configuration Files {#backup-config}

Back up the `.env` files and Docker Compose configurations:

```bash
cp .env .env.backup_$(date +%Y%m%d)
cp frontend.env frontend.env.backup_$(date +%Y%m%d)
cp docker-compose.yml docker-compose.yml.backup_$(date +%Y%m%d)
```

## Restore {#restore}

:::caution
Stop the affected containers before importing a backup to avoid data inconsistencies.
:::

### MariaDB {#restore-mariadb}

```bash
docker compose stop backend worker worker-vm-clone worker-periodic scheduler
docker exec -i openvle-mariadb mariadb \
  -u "$MARIADB_USER" \
  -p"$MARIADB_PASSWORD" \
  "$MARIADB_DATABASE" < backup_mariadb_YYYYMMDD.sql
docker compose up -d backend worker worker-vm-clone worker-periodic scheduler
```

### MongoDB {#restore-mongodb}

```bash
docker compose stop backend worker worker-vm-clone worker-periodic scheduler
docker exec -i openvle-mongodb mongorestore \
  --username="$MONGODB_USER" \
  --password="$MONGODB_PASSWORD" \
  --db="$MONGODB_DATABASE" \
  --archive --drop < backup_mongodb_YYYYMMDD.archive
docker compose up -d backend worker worker-vm-clone worker-periodic scheduler
```

## Automation (Cron) {#automation}

The following example script backs up both databases daily and retains backups for the last 14 days:

```bash
#!/bin/bash
BACKUP_DIR="/opt/openvle/backups"
RETENTION_DAYS=14
DATE=$(date +%Y%m%d)

mkdir -p "$BACKUP_DIR"

# MariaDB
docker exec openvle-mariadb mariadb-dump \
  -u "$MARIADB_USER" -p"$MARIADB_PASSWORD" "$MARIADB_DATABASE" \
  > "$BACKUP_DIR/mariadb_$DATE.sql"

# MongoDB
docker exec openvle-mongodb mongodump \
  --username="$MONGODB_USER" --password="$MONGODB_PASSWORD" \
  --db="$MONGODB_DATABASE" --archive \
  > "$BACKUP_DIR/mongodb_$DATE.archive"

# Remove old backups
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete
```

You can set up this script as a daily cron job:

```bash
# Daily at 02:00
0 2 * * * /opt/openvle/backup.sh
```

## Recommended Backup Schedule {#schedule}

| Frequency           | Action                             |
| ------------------- | ---------------------------------- |
| Daily               | Database dumps (MariaDB + MongoDB) |
| Before every update | Manual backup of all components    |
