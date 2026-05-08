---
id: logs
sidebar_label: Journalisation
sidebar_position: 20
status: finished
tags:
  - operations
  - logs
---

# Journalisation {#logging}

## Vue d'ensemble {#overview}

Cette page décrit l'infrastructure de journalisation d'OpenVLE. Tous les conteneurs écrivent leurs journaux sur stdout, de sorte qu'ils sont accessibles via les mécanismes standard de Docker (`docker logs`, `docker compose logs`).

## Services et leurs journaux {#service-logs}

| Service               | Fonction                                   | Particularités                                                         |
| --------------------- | ------------------------------------------ | ---------------------------------------------------------------------- |
| `backend`             | Serveur API FastAPI                        | Journaux basés sur Uvicorn, incl. accès HTTP, erreurs, démarrage/arrêt |
| `worker` (4 Replicas) | Tâches d'arrière-plan générales            | Exécution de tâches, erreurs, tentatives de réessai                    |
| `worker-vm-clone`     | Opérations de clonage et suppression de VM | Opérations Proxmox de longue durée                                     |
| `worker-periodic`     | Polling Proxmox                            | Synchronisation périodique de l'état                                   |
| `scheduler`           | Tâches planifiées (`rq cron`)              | Tâches périodiques planifiées et exécutées                             |
| `frontend`            | Serveur web Vue.js/Nginx                   | Journaux d'accès et d'erreurs HTTP                                     |
| `mariadb`             | Base de données SQL                        | Messages de démarrage/arrêt, avertissements                            |
| `mongodb`             | Base de données NoSQL                      | Informations de connexion, authentification                            |
| `redis`               | File de tâches et cache                    | `loglevel warning`, sortie minimale                                    |

## Consulter les journaux {#view-logs}

Docker propose deux commandes pour consulter les journaux : `docker logs` pour un conteneur individuel (adressé par le nom du conteneur) et `docker compose logs` pour un ou plusieurs services à la fois (adressés par le nom du service dans le `docker-compose.yml`). Les deux supportent les mêmes options de base.

### Conteneur individuel {#single-container}

```bash
docker logs [OPTIONS] <container_name>
```

| Option          | Description                                                                |
| --------------- | -------------------------------------------------------------------------- |
| `-f`            | **Follow** — affiche les journaux en temps réel, similaire à `tail -f`     |
| `-n` / `--tail` | Affiche uniquement les `n` dernières lignes                                |
| `--since`       | Affiche les journaux depuis un moment donné (`10m`, `2026-04-28T12:00:00`) |
| `--timestamps`  | Affiche les horodatages dans les lignes de journal                         |

**Exemple :**

```bash
docker logs -f -n 100 openvle-backend
```

Affiche les 100 dernières lignes du conteneur `openvle-backend` puis continue le suivi en temps réel. L'affichage peut être interrompu avec `Ctrl+C`.

### Plusieurs services {#multiple-services}

```bash
docker compose logs [OPTIONS] [service_name ...]
```

| Option          | Description                                                   |
| --------------- | ------------------------------------------------------------- |
| `-f`            | **Follow** — affiche continuellement les nouveaux journaux    |
| `-n` / `--tail` | Affiche uniquement les `n` dernières lignes par conteneur     |
| `--timestamps`  | Affiche les horodatages                                       |
| `--no-color`    | Désactive la coloration syntaxique (par ex. pour les scripts) |

**Exemple :**

```bash
docker compose logs -f -n 50 backend worker scheduler
```

Affiche les 50 dernières lignes des trois services et continue le suivi des journaux en temps réel.

### Recherche d'erreurs {#error-search}

```bash
# Rechercher les erreurs dans le backend
docker compose logs backend | grep ERROR

# Rechercher les erreurs dans tous les workers
docker compose logs worker worker-vm-clone worker-periodic | grep ERROR
```

## Format des journaux {#log-format}

FastAPI utilise Uvicorn, qui produit par défaut des lignes de journal au format suivant :

```
INFO:     127.0.0.1:54321 - "GET /v1/users HTTP/1.1" 200 OK
ERROR:    Exception in ASGI application: ...
```

Les journaux des workers affichent l'exécution des tâches avec leur statut, leur durée et, le cas échéant, les messages d'erreur.

## Agrégation centralisée des journaux {#log-aggregation}

Pour les environnements de production, il est recommandé de configurer tous les services avec un driver de journalisation centralisé (par ex. `gelf`, `fluentd`, ou une stack ELK/EFK). Un fichier `docker-compose.override.yml` est adapté pour cela afin de préserver la capacité de mise à jour.

**Exemple pour GELF (Graylog) :**

```yaml
logging:
  driver: gelf
  options:
    gelf-address: udp://graylog.example.org:12201
    tag: openvle-backend
```

:::note Workers répliqués
Étant donné que le service `worker` fonctionne avec 4 réplicas en production, il est recommandé lors de l'agrégation centralisée des journaux d'ajouter le nom du service et de l'instance en tant que métadonnées, afin de pouvoir attribuer les journaux aux réplicas individuels.
:::

## Cas d'utilisation typiques {#use-cases}

- **Recherche d'erreurs** — Erreurs et tracebacks dans les journaux du backend ou des workers
- **Analyse des tâches** — Vérification de la durée et du statut des jobs des workers
- **Surveillance du scheduler** — Vérification que les tâches périodiques s'exécutent comme prévu
- **Audit** — Détection des accès API non autorisés
- **Débogage du frontend** — Journaux d'accès et d'erreurs Nginx en cas de problèmes d'accès
