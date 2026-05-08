---
id: task-system
sidebar_label: Système de tâches
sidebar_position: 35
status: finished
tags:
  - infrastructure
  - worker
  - scheduler
---

# Système de tâches {#task-system}

OpenVLE exécute les opérations gourmandes en ressources et chronophages de manière asynchrone en arrière-plan. Le système de tâches repose sur Redis Queue (RQ) et se compose de **conteneurs Worker** pour l'exécution des tâches et d'un **Scheduler** pour les tâches périodiques.

## Architecture {#architecture}

```
Backend/Scheduler → Redis Queue → Worker → Exécution
```

1. **Enqueue** — Le backend ou le scheduler place une tâche dans une queue Redis nommée.
2. **Dequeue** — Le worker responsable récupère la prochaine tâche de sa queue.
3. **Exécution** — Le worker exécute la tâche (par ex. cloner une VM, envoyer un e-mail).
4. **Résultat** — Le résultat est enregistré dans la base de données sous forme de Task/SubTask et affiché à l'utilisateur.

## Queues {#queues}

Le système utilise plusieurs queues nommées, chacune dédiée à un domaine de tâches spécifique :

La variable d'environnement `WORKER_MAX_RETRY` (par défaut : `5`) contrôle le nombre maximal de tentatives pour la plupart des queues. Certaines queues utilisent une valeur fixe.

| Queue            | Objectif                                           | Max. Retries       | Intervalles de retry |
| ---------------- | -------------------------------------------------- | ------------------ | -------------------- |
| `pve_vm_clone`   | Clonage et suppression de VMs                      | `WORKER_MAX_RETRY` | 10s, 30s, 60s        |
| `pve_vm_actions` | Actions VM (démarrage, arrêt, reset, migration)    | `WORKER_MAX_RETRY` | 5s, 10s, 15s         |
| `pve_periodic`   | Polling Proxmox (synchronisation info nœuds)       | 3 (fixe)           | 5s, 10s, 15s         |
| `mails`          | Envoi d'e-mails                                    | `WORKER_MAX_RETRY` | 30s, 60s, 120s       |
| `guacamole`      | Gestion des connexions Guacamole                   | `WORKER_MAX_RETRY` | 10s, 30s, 60s        |
| `moodle`         | Gestion des cours et utilisateurs Moodle           | `WORKER_MAX_RETRY` | 10s, 30s, 60s        |
| `core_periodic`  | Cycle de vie des événements, nettoyage des e-mails | 3 (fixe)           | 5s, 10s, 15s         |

## Worker {#worker}

En production, trois types de workers fonctionnent comme des conteneurs Docker séparés. Chaque type écoute des queues spécifiques :

| Type de worker      | `SERVICE_ROLE`    | Queues                                                            | Réplicas |
| ------------------- | ----------------- | ----------------------------------------------------------------- | -------- |
| **Worker**          | `worker`          | `core_periodic`, `guacamole`, `mails`, `moodle`, `pve_vm_actions` | 4        |
| **Worker VM-Clone** | `worker-vm-clone` | `pve_vm_clone`                                                    | 1        |
| **Worker Periodic** | `worker-periodic` | `pve_periodic`                                                    | 1        |

La répartition sur plusieurs types de workers garantit que les opérations de clonage de VMs de longue durée ne bloquent pas le traitement des autres tâches.

:::note Développement local
Dans l'environnement de développement local, toutes les queues peuvent être traitées par un seul worker (`SERVICE_ROLE=worker-all`).
:::

### Types de tâches {#task-types}

| Tâche                                 | Queue            | Déclencheur           | Description                                                                   |
| ------------------------------------- | ---------------- | --------------------- | ----------------------------------------------------------------------------- |
| Cloner une VM                         | `pve_vm_clone`   | Utilisateur/Scheduler | Crée une nouvelle VM à partir d'un modèle de VM sur Proxmox                   |
| Démarrer/arrêter/réinitialiser une VM | `pve_vm_actions` | Utilisateur           | Démarre, arrête ou réinitialise une VM sur Proxmox                            |
| Supprimer une VM                      | `pve_vm_clone`   | Utilisateur/Scheduler | Supprime une VM de Proxmox et nettoie la base de données                      |
| Migrer une VM                         | `pve_vm_actions` | Utilisateur           | Déplace une VM vers un autre nœud Proxmox                                     |
| Envoyer un e-mail                     | `mails`          | Système               | Envoie des notifications via SMTP                                             |
| Provisionner Guacamole                | `guacamole`      | Système               | Crée des utilisateurs, connexions et profils de partage Guacamole             |
| Nettoyer Guacamole                    | `guacamole`      | Système               | Supprime les connexions et profils de partage                                 |
| Déployer un cours Moodle              | `moodle`         | Système               | Duplique le cours modèle Moodle pour un événement                             |
| Inscrire des utilisateurs Moodle      | `moodle`         | Système               | Crée des utilisateurs dans Moodle et les inscrit aux cours                    |
| Déployer un événement                 | `core_periodic`  | Scheduler             | Crée toutes les VMs et connexions pour un événement                           |
| Archiver un événement                 | `core_periodic`  | Scheduler             | Supprime toutes les VMs et nettoie les connexions après la fin de l'événement |

### Dépendances entre jobs {#job-dependencies}

Les jobs peuvent avoir des dépendances avec d'autres jobs (`depends_on`). Cela permet de former des chaînes d'exécution, par exemple :

```
Supprimer la connexion Guacamole → Arrêter la VM → Supprimer la VM
```

Le job suivant n'est démarré que lorsque le précédent s'est terminé avec succès.

### Gestion des erreurs {#error-handling}

Les jobs échoués sont automatiquement relancés. Le nombre maximal de tentatives et les intervalles de retry sont configurés par queue (voir [Queues](#queues)). Après épuisement de toutes les tentatives, le job est marqué comme définitivement échoué.

Certaines erreurs sont reconnues comme permanentes et ne sont pas relancées (par ex. code d'erreur SMTP 550 pour une adresse de destinataire invalide).

:::note Logs
Les jobs en erreur et leurs messages d'erreur sont visibles dans les logs des workers, par ex. `docker logs openvle-worker-vm-clone`. Vous trouverez plus d'informations sur la journalisation sous [Logs](../operations/logs).
:::

### Suivi des tâches {#task-tracking}

Chaque opération asynchrone est suivie dans la base de données via deux modèles :

- **Task** — Représente une opération logique (par ex. « Cloner une VM »)
- **SubTask** — Tentatives d'exécution individuelles d'une tâche avec statut (`processing`, `success`, `error`), message d'erreur et numéro de tentative

La progression est affichée dans l'interface utilisateur.

## Scheduler {#scheduler}

Le scheduler fonctionne comme un conteneur séparé (`SERVICE_ROLE=scheduler`) et utilise `rq cron` avec des expressions Cron pour mettre en file d'attente des tâches périodiques dans la queue Redis. Les workers les exécutent ensuite.

### Tâches périodiques {#periodic-tasks}

| Tâche                       | Queue           | Planification                                                         | Description                                                                                      |
| --------------------------- | --------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Info nœuds Proxmox          | `pve_periodic`  | Toutes les `WORKER_PVE_PERIODIC_INTERVAL` secondes (par défaut : 60s) | Synchronise le statut des VMs/modèles et les informations des nœuds depuis le cluster Proxmox    |
| Cycle de vie des événements | `core_periodic` | Quotidiennement à 01:00 UTC                                           | Vérifie si des événements doivent être démarrés ou archivés, envoie des notifications préalables |
| Nettoyage des e-mails       | `core_periodic` | Quotidiennement à 02:00 UTC                                           | Supprime les e-mails envoyés datant de plus de `MAIL_MAX_AGE_WEEKS` (par défaut : 4 semaines)    |

:::info Temps de préparation
Le temps de préparation pour les déploiements et archivages automatiques est contrôlé via `EVENTS_START_PREP_TIME_DAYS` et `EVENTS_END_PREP_TIME_DAYS` (par défaut : 7 jours chacun). Voir [Référence de configuration — Événements](../install/configuration#events).
:::

## Interaction des composants {#interaction}

| Composant           | Rôle                                                | Connexions                                                   |
| ------------------- | --------------------------------------------------- | ------------------------------------------------------------ |
| **Backend**         | Crée des tâches sur demande de l'utilisateur        | → Redis (Enqueue)                                            |
| **Scheduler**       | Crée des tâches périodiques selon la planification  | → Redis (Enqueue)                                            |
| **Redis**           | Système de queues                                   | Reçoit et conserve les jobs dans des queues nommées          |
| **Worker** (4x)     | Traite les tâches générales                         | → Redis, → MariaDB, → Proxmox, → Guacamole, → Moodle, → SMTP |
| **Worker VM-Clone** | Traite les opérations de clonage/suppression de VMs | → Redis, → MariaDB, → Proxmox                                |
| **Worker Periodic** | Traite le polling Proxmox                           | → Redis, → MariaDB, → MongoDB, → Proxmox                     |

## Informations complémentaires {#further-reading}

- [Référence de configuration — Worker](../install/configuration#worker) — Variables d'environnement pour les workers et le scheduler
- [Composants utilisés](components) — Détails des conteneurs de tous les services
