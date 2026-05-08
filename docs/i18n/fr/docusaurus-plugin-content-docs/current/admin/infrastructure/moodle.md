---
id: moodle
sidebar_label: Moodle
sidebar_position: 60
status: finished
tags:
  - infrastructure
  - moodle
---

# Moodle {#moodle}

OpenVLE peut être connecté à une instance Moodle existante pour provisionner automatiquement des environnements d'apprentissage. Les cours Moodle sont dupliqués, les participants sont synchronisés et les inscriptions sont gérées — le tout piloté par le cycle de vie des événements dans OpenVLE.

:::info Optionnel
L'intégration Moodle est entièrement optionnelle. En cas de non-utilisation, tous les éléments liés à Moodle ne sont pas affichés dans l'interface utilisateur. L'intégration est désactivée par défaut.
:::

## Architecture {#architecture}

OpenVLE communique avec Moodle exclusivement via l'**API REST Moodle Web Services**. Il n'y a pas de connexion directe à la base de données — toutes les opérations s'effectuent via des appels API HTTP.

| Composant               | Rôle                                                                                                  |
| ----------------------- | ----------------------------------------------------------------------------------------------------- |
| **OpenVLE Backend**     | Récupère les cours Moodle et vérifie les utilisateurs                                                 |
| **OpenVLE Worker**      | Exécute la duplication de cours, la création d'utilisateurs et les inscriptions de manière asynchrone |
| **Moodle Web Services** | Reçoit les requêtes API et exécute les opérations dans Moodle                                         |

:::note Accès réseau
Le backend OpenVLE doit pouvoir établir des connexions HTTPS sortantes vers l'instance Moodle. L'authentification s'effectue via un token API Moodle.
:::

## Concept : association de cours {#course-mapping}

L'intégration repose sur l'association de cours Moodle à des environnements OpenVLE :

1. **Environnement** — Un environnement OpenVLE peut être associé à un cours Moodle. Ce cours Moodle sert de **modèle**.
2. **Événement** — Lorsqu'un événement est démarré à partir de cet environnement, OpenVLE duplique automatiquement le cours modèle Moodle. Chaque événement reçoit son propre cours Moodle.

## Cycle de vie d'un événement {#event-lifecycle}

Les actions Moodle sont liées au cycle de vie d'un événement :

| Phase                           | Action Moodle                                                                       |
| ------------------------------- | ----------------------------------------------------------------------------------- |
| **Déploiement**                 | Le cours modèle est dupliqué, les participants sont créés et inscrits               |
| **Ajout de participants**       | L'utilisateur est créé dans Moodle si nécessaire et inscrit au cours                |
| **Suppression de participants** | L'utilisateur est désinscrit du cours Moodle                                        |
| **Fin de l'événement**          | Les étudiants sont désinscrits, les enseignants restent, le cours devient invisible |
| **Suppression de l'événement**  | Le cours Moodle est optionnellement supprimé (configurable)                         |

### Synchronisation des utilisateurs {#user-sync}

Lors du déploiement, OpenVLE vérifie pour chaque participant si un utilisateur correspondant existe dans Moodle. La correspondance s'effectue via le champ configuré (`MOODLE_USER_MATCH_FIELD` — soit `email`, soit `username`). Si aucun utilisateur Moodle n'est trouvé, OpenVLE en crée automatiquement un nouveau.

### Association des rôles {#role-mapping}

OpenVLE fait correspondre les rôles des participants aux rôles de cours Moodle :

| Rôle OpenVLE | Rôle Moodle                 |
| ------------ | --------------------------- |
| Enseignants  | Editing Teacher (Role ID 3) |
| Étudiants    | Student (Role ID 5)         |

:::caution Perte de données lors de la désinscription
Lors de la désinscription d'un participant, les soumissions, notes et progrès d'apprentissage dans le cours Moodle sont perdus. Il s'agit d'une limitation de l'API REST Moodle (voir [MDL-70582](https://tracker.moodle.org/browse/MDL-70582)).
:::

## Informations complémentaires {#further-reading}

- [Configurer Moodle](../install/moodle) — Installation, configuration et dépannage
- [Référence de configuration](../install/configuration) — Toutes les variables d'environnement Moodle
