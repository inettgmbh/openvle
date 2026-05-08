---
id: backups-restore
sidebar_label: Backups & Wiederherstellung
sidebar_position: 10
status: finished
tags:
  - operations
  - backup
---

# Backups & Wiederherstellung {#backups-restore}

Sobald du die Software in einem produktiven Betrieb verwendest, empfehlen wir regelmäßige Backups durchzuführen. Dies hilft einerseits gegen menschliche Fehler, wie zum Beispiel das unbeabsichtigte Löschen von Objekten, als auch gegen Datenverlust aufgrund von Hardwaredefekten.

## Proxmox VM-Backup (empfohlen) {#proxmox-backup}

Da OpenVLE in der Regel als VM auf dem Proxmox VE Cluster betrieben wird, ist der einfachste und empfohlene Weg ein **natives Proxmox-Backup der gesamten VM**. Damit werden alle Datenbanken, Konfigurationsdateien und Docker-Volumes in einem Schritt gesichert.

Proxmox unterstützt verschiedene Backup-Ziele (z. B. Proxmox Backup Server, NFS, CIFS) und erlaubt sowohl manuelle als auch zeitgesteuerte Backups über die Proxmox-Weboberfläche oder CLI. Im Fehlerfall kann die gesamte VM aus dem Backup wiederhergestellt werden.

:::note
Die Proxmox-Backup-Konfiguration erfolgt auf dem Proxmox VE Cluster selbst und ist nicht Teil der OpenVLE-Konfiguration. Weitere Informationen findest du in der [Proxmox VE Backup-Dokumentation](https://pve.proxmox.com/wiki/Backup_and_Restore).
:::

## Datenbank-Dumps (ergänzend) {#database-dumps}

Ergänzend zu VM-Backups können Datenbank-Dumps für granulare Wiederherstellungen nützlich sein — z. B. wenn nur eine einzelne Datenbank zurückgesetzt werden soll, ohne die gesamte VM wiederherzustellen.

## Was muss gesichert werden? {#what-to-backup}

| Komponente           | Daten                                                        | Speicherort      | Priorität |
| -------------------- | ------------------------------------------------------------ | ---------------- | --------- |
| MariaDB              | Kernentitäten (Benutzer, VMs, Veranstaltungen, Rollen, etc.) | `./mariadb/data` | Kritisch  |
| MongoDB              | Aktivitäten, Logs, System-Events                             | `./mongodb`      | Hoch      |
| Redis                | Task-Queue, Cache                                            | In-Memory + AOF  | Niedrig   |
| `.env`               | Backend-Konfiguration, Secrets                               | `./`             | Kritisch  |
| `frontend.env`       | Frontend-Konfiguration                                       | `./`             | Kritisch  |
| `docker-compose.yml` | Service-Definitionen                                         | `./`             | Mittel    |

:::note Redis
Redis dient primär als Task-Queue und Cache. Die Daten werden bei einem Neustart automatisch aus der AOF-Datei wiederhergestellt. Ein separates Backup ist in der Regel nicht notwendig.
:::

## Backup erstellen {#create-backup}

### MariaDB {#backup-mariadb}

Die MariaDB-Datenbank enthält alle Kernentitäten und sollte täglich gesichert werden:

```bash
docker exec openvle-mariadb mariadb-dump \
  -u "$MARIADB_USER" \
  -p"$MARIADB_PASSWORD" \
  "$MARIADB_DATABASE" > backup_mariadb_$(date +%Y%m%d).sql
```

Die Variablen (`MARIADB_USER`, `MARIADB_PASSWORD`, `MARIADB_DATABASE`) findest du in deiner `.env`. Siehe [Konfigurationsreferenz](../install/configuration#mariadb).

### MongoDB {#backup-mongodb}

MongoDB speichert Aktivitäten, Logs und System-Events:

```bash
docker exec openvle-mongodb mongodump \
  --username="$MONGODB_USER" \
  --password="$MONGODB_PASSWORD" \
  --db="$MONGODB_DATABASE" \
  --archive > backup_mongodb_$(date +%Y%m%d).archive
```

### Konfigurationsdateien {#backup-config}

Sichere die `.env`-Dateien und Docker-Compose-Konfigurationen:

```bash
cp .env .env.backup_$(date +%Y%m%d)
cp frontend.env frontend.env.backup_$(date +%Y%m%d)
cp docker-compose.yml docker-compose.yml.backup_$(date +%Y%m%d)
```

## Wiederherstellung {#restore}

:::caution
Stoppe die betroffenen Container, bevor du ein Backup einspielst, um Dateninkonsistenzen zu vermeiden.
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

## Automatisierung (Cron) {#automation}

Das folgende Beispiel-Skript sichert beide Datenbanken täglich und behält die Backups der letzten 14 Tage:

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

# Alte Backups entfernen
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete
```

Dieses Skript kannst du als täglichen Cron-Job einrichten:

```bash
# Täglich um 02:00 Uhr
0 2 * * * /opt/openvle/backup.sh
```

## Empfohlener Backup-Zeitplan {#schedule}

| Häufigkeit       | Maßnahme                            |
| ---------------- | ----------------------------------- |
| Täglich          | Datenbank-Dumps (MariaDB + MongoDB) |
| Vor jedem Update | Manuelles Backup aller Komponenten  |
