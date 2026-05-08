---
id: backups-restore
sidebar_label: Sauvegardes et restauration
sidebar_position: 10
status: finished
tags:
  - operations
  - backup
---

# Sauvegardes et restauration {#backups-restore}

Dès que vous utilisez le logiciel en environnement de production, nous vous recommandons d'effectuer des sauvegardes régulières. Cela protège aussi bien contre les erreurs humaines, comme la suppression accidentelle d'objets, que contre la perte de données due à des défaillances matérielles.

## Sauvegarde de VM Proxmox (recommandé) {#proxmox-backup}

Étant donné qu'OpenVLE est généralement exploité en tant que VM sur le cluster Proxmox VE, le moyen le plus simple et recommandé est une **sauvegarde native Proxmox de l'ensemble de la VM**. Cela permet de sécuriser toutes les bases de données, fichiers de configuration et volumes Docker en une seule étape.

Proxmox prend en charge différentes cibles de sauvegarde (par ex. Proxmox Backup Server, NFS, CIFS) et permet des sauvegardes aussi bien manuelles que planifiées via l'interface web de Proxmox ou la ligne de commande. En cas de problème, l'ensemble de la VM peut être restaurée à partir de la sauvegarde.

:::note
La configuration de la sauvegarde Proxmox s'effectue sur le cluster Proxmox VE lui-même et ne fait pas partie de la configuration OpenVLE. Vous trouverez de plus amples informations dans la [documentation de sauvegarde Proxmox VE](https://pve.proxmox.com/wiki/Backup_and_Restore).
:::

## Dumps de base de données (complémentaire) {#database-dumps}

En complément des sauvegardes de VM, les dumps de base de données peuvent être utiles pour des restaurations granulaires — par ex. lorsqu'une seule base de données doit être réinitialisée sans restaurer l'ensemble de la VM.

## Que faut-il sauvegarder ? {#what-to-backup}

| Composant            | Données                                                          | Emplacement      | Priorité |
| -------------------- | ---------------------------------------------------------------- | ---------------- | -------- |
| MariaDB              | Entités principales (utilisateurs, VMs, événements, rôles, etc.) | `./mariadb/data` | Critique |
| MongoDB              | Activités, journaux, événements système                          | `./mongodb`      | Élevée   |
| Redis                | File de tâches, cache                                            | In-Memory + AOF  | Faible   |
| `.env`               | Configuration du backend, secrets                                | `./`             | Critique |
| `frontend.env`       | Configuration du frontend                                        | `./`             | Critique |
| `docker-compose.yml` | Définitions des services                                         | `./`             | Moyenne  |

:::note Redis
Redis sert principalement de file de tâches et de cache. Les données sont automatiquement restaurées à partir du fichier AOF lors d'un redémarrage. Une sauvegarde séparée n'est généralement pas nécessaire.
:::

## Créer une sauvegarde {#create-backup}

### MariaDB {#backup-mariadb}

La base de données MariaDB contient toutes les entités principales et doit être sauvegardée quotidiennement :

```bash
docker exec openvle-mariadb mariadb-dump \
  -u "$MARIADB_USER" \
  -p"$MARIADB_PASSWORD" \
  "$MARIADB_DATABASE" > backup_mariadb_$(date +%Y%m%d).sql
```

Les variables (`MARIADB_USER`, `MARIADB_PASSWORD`, `MARIADB_DATABASE`) se trouvent dans votre `.env`. Voir [Référence de configuration](../install/configuration#mariadb).

### MongoDB {#backup-mongodb}

MongoDB stocke les activités, les journaux et les événements système :

```bash
docker exec openvle-mongodb mongodump \
  --username="$MONGODB_USER" \
  --password="$MONGODB_PASSWORD" \
  --db="$MONGODB_DATABASE" \
  --archive > backup_mongodb_$(date +%Y%m%d).archive
```

### Fichiers de configuration {#backup-config}

Sauvegardez les fichiers `.env` et les configurations Docker Compose :

```bash
cp .env .env.backup_$(date +%Y%m%d)
cp frontend.env frontend.env.backup_$(date +%Y%m%d)
cp docker-compose.yml docker-compose.yml.backup_$(date +%Y%m%d)
```

## Restauration {#restore}

:::caution
Arrêtez les conteneurs concernés avant de restaurer une sauvegarde afin d'éviter des incohérences de données.
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

## Automatisation (Cron) {#automation}

Le script suivant sauvegarde les deux bases de données quotidiennement et conserve les sauvegardes des 14 derniers jours :

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

# Supprimer les anciennes sauvegardes
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete
```

Vous pouvez configurer ce script en tant que tâche cron quotidienne :

```bash
# Quotidiennement à 02h00
0 2 * * * /opt/openvle/backup.sh
```

## Calendrier de sauvegarde recommandé {#schedule}

| Fréquence                | Mesure                                       |
| ------------------------ | -------------------------------------------- |
| Quotidien                | Dumps de base de données (MariaDB + MongoDB) |
| Avant chaque mise à jour | Sauvegarde manuelle de tous les composants   |
