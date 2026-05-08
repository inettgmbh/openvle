---
id: components
sidebar_label: Composants utilisés
sidebar_position: 20
status: finished
tags:
  - infrastructure
  - architecture
---

# Composants utilisés {#used-components}

Cette page décrit en détail les conteneurs Docker du stack OpenVLE : configuration, ports, dépendances et Health Checks. Pour une vue d'ensemble de tous les composants et le diagramme d'architecture, consultez la [vue d'ensemble de l'infrastructure](infrastructure).

:::caution Applicable uniquement à la configuration standard
Cette page se réfère à l'état standard du dépôt officiel. En cas de configurations différentes (par exemple avec des Dockerfiles personnalisés, des fichiers `.env`/`frontend.env` modifiés ou une autre infrastructure), les informations peuvent différer.
:::

## Application {#application}

Le Backend et le Frontend constituent la couche applicative d'OpenVLE. Le Backend fournit l'API REST, le Frontend l'interface web.

| Service    | Description                                                                                           | Port      | Dépendances                                |
| ---------- | ----------------------------------------------------------------------------------------------------- | --------- | ------------------------------------------ |
| `backend`  | Python 3 / FastAPI — API REST, logique métier, authentification, intégration Proxmox, envoi d'e-mails | 8000 → 80 | MariaDB, MongoDB, Redis (tous healthy)     |
| `frontend` | Vue.js / Nginx — Interface web depuis laquelle toutes les fonctionnalités sont accessibles            | 80 → 80   | `backend` (côté client dans le navigateur) |

- Le **Backend** (`SERVICE_ROLE=backend`) est le composant central : il traite les requêtes API, vérifie les permissions, coordonne tous les processus et met les tâches en arrière-plan dans la file d'attente Redis.
- Le **Frontend** est compilé lors du build et déployé dans un conteneur Nginx. L'URL de l'API et les paramètres optionnels (par exemple le DSN Sentry) sont configurés via `frontend.env`. Des logos personnalisés peuvent optionnellement être intégrés via des montages `static/`.

## Traitement en arrière-plan {#background-processing}

Le système de tâches se compose de plusieurs conteneurs Worker et d'un Scheduler. La répartition sur des Workers spécialisés garantit que les opérations de longue durée (par exemple le clonage de VMs) ne bloquent pas les autres tâches. Tous les Workers et le Scheduler nécessitent MariaDB (healthy) et Redis (healthy).

| Service           | `SERVICE_ROLE`    | Queues                                                            | Replicas | Description                                                              |
| ----------------- | ----------------- | ----------------------------------------------------------------- | -------- | ------------------------------------------------------------------------ |
| `worker`          | `worker`          | `core_periodic`, `guacamole`, `mails`, `moodle`, `pve_vm_actions` | 4        | Tâches générales : actions VM, e-mail, Guacamole, Moodle                 |
| `worker-vm-clone` | `worker-vm-clone` | `pve_vm_clone`                                                    | 1        | Opérations de clonage et de suppression de VMs (longue durée)            |
| `worker-periodic` | `worker-periodic` | `pve_periodic`                                                    | 1        | Polling Proxmox (statut VM/modèle, informations noeud)                   |
| `scheduler`       | `scheduler`       | —                                                                 | 1        | Met les tâches périodiques dans la file d'attente selon un planning cron |

Vous trouverez plus de détails sur le système de tâches, les queues et la gestion des erreurs sous [Système de tâches](task-system).

## Bases de données {#databases}

Trois systèmes de bases de données couvrent des besoins différents. Aucun des conteneurs de base de données ne publie de ports — ils sont exclusivement accessibles en interne.

| Service   | Type              | Fonction                                                                                | Persistance                  | Health Check                           |
| --------- | ----------------- | --------------------------------------------------------------------------------------- | ---------------------------- | -------------------------------------- |
| `mariadb` | MariaDB (SQL)     | Entités principales : utilisateurs, rôles, permissions, environnements, événements, VMs | `./mariadb/data`             | `mariadb-admin ping`                   |
| `mongodb` | MongoDB (NoSQL)   | Activités, événements système, journaux d'audit, historiques de modifications           | `./mongodb`                  | `mongosh eval db.adminCommand('ping')` |
| `redis`   | Redis (In-Memory) | File d'attente des tâches et cache pour Worker/Scheduler                                | AOF + Snapshot (`save 60 1`) | `redis-cli incr ping`                  |

- **MariaDB** — Le schéma et les données initiales sont créés automatiquement lors du premier démarrage par le Backend/Worker (migration avec mécanisme de verrouillage). Accès par le Backend, le Worker et le Scheduler.
- **MongoDB** — Accès exclusivement via le Backend. Authentification via l'utilisateur root depuis `.env`.
- **Redis** — Protégé par mot de passe via `.env`. Configuré avec AOF (`appendonly yes`) et snapshot périodique pour le stockage persistant.

Vous trouverez plus de détails sur l'architecture des données sous [Bases de données](databases).

## Environnement de développement {#dev-environment}

Les services suivants ne sont pas inclus dans le stack de production et ne sont disponibles que dans l'environnement de développement ou local :

| Service      | Configuration            | Fonction                                         | Port                       |
| ------------ | ------------------------ | ------------------------------------------------ | -------------------------- |
| `phpmyadmin` | `docker-compose.dev.yml` | Interface web pour l'administration de MariaDB   | 8888                       |
| `fake-smtp`  | `docker-compose.dev.yml` | Serveur SMTP local pour tester l'envoi d'e-mails | 1025 (SMTP), 8088 (Web-UI) |

:::note Réseau interne
Tous les services sont connectés en interne via le réseau Docker `openvle-internal`. Seuls le Frontend et le Backend sont exposés à l'extérieur. Vous trouverez plus de détails sous [Réseau & Docker](networking).
:::
