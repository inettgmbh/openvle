---
id: permission-system
sidebar_label: Système de permissions
sidebar_position: 45
status: finished
tags:
  - infrastructure
  - permissions
---

# Système de permissions {#permission-system}

Le système de permissions d'OpenVLE contrôle quelles actions les utilisateurs peuvent effectuer sur quelles ressources. Il repose sur un modèle ObjectPermission qui prend en charge aussi bien les permissions globales que les permissions liées à des objets spécifiques.

:::info Authentification vs. Autorisation
L'autorisation (que peut faire un utilisateur ?) est gérée par le système de permissions décrit ici. L'authentification (qui est l'utilisateur ?) est traitée séparément — voir [Authentification](authentication).
:::

## Concept {#concept}

Chaque permission dans OpenVLE est une combinaison de :

- **Type d'objet** — La ressource à laquelle la permission se rapporte (par ex. `VirtualMachine`, `Event`, `User`, `Role`)
- **ID d'objet** — Une instance spécifique (ou vide pour une permission globale)
- **Clé de permission** — L'action autorisée (par ex. `object_read`, `object_update`, `object_full`)
- **Entité** — L'utilisateur ou le rôle qui reçoit la permission

## Clés de permission {#permission-keys}

### Permissions CRUD standard {#crud-permissions}

Les permissions CRUD suivent une hiérarchie — une permission de niveau supérieur inclut automatiquement les permissions de niveau inférieur :

| Clé             | Accorde                            | Description                                  |
| --------------- | ---------------------------------- | -------------------------------------------- |
| `object_full`   | full, delete, update, read, create | Accès complet à la ressource                 |
| `object_delete` | delete, update, read               | Supprimer, modifier et lire                  |
| `object_update` | update, read                       | Modifier et lire                             |
| `object_read`   | read                               | Lecture seule                                |
| `object_create` | create                             | Créer de nouveaux objets (global uniquement) |

:::note Exemple de hiérarchie
Si un utilisateur possède `object_delete` sur les VMs, il peut supprimer, modifier et lire les VMs — une permission `object_read` séparée n'est pas nécessaire.
:::

### Permissions spéciales {#special-permissions}

En plus des permissions CRUD standard, il existe des permissions spéciales pour certains types d'objets :

| Clé                                                | Type d'objet          | Description                                         |
| -------------------------------------------------- | --------------------- | --------------------------------------------------- |
| `object_actions_start`, `object_actions_stop`, ... | VirtualMachine, Event | Actions individuelles (démarrer, arrêter, etc.)     |
| `object_set_password`                              | User                  | Modifier le mot de passe d'un utilisateur           |
| `object_search`                                    | User                  | Rechercher des utilisateurs                         |
| `object_send`, `object_send_bulk`                  | Mail                  | Envoyer des e-mails                                 |
| `object_reset`                                     | VirtualMachine        | Réinitialiser une VM                                |
| `object_templates_update`                          | Event                 | Mettre à jour les modèles de VM dans les événements |

## Permissions globales vs. liées à un objet {#scopes}

Le système distingue deux portées :

| Portée              | ID d'objet          | Effet                                                 |
| ------------------- | ------------------- | ----------------------------------------------------- |
| **Globale**         | vide                | S'applique à **toutes** les instances du type d'objet |
| **Liée à un objet** | UUID d'une instance | S'applique uniquement à l'instance **spécifique**     |

**Exemple :** Un utilisateur avec `object_read` global sur `VirtualMachine` peut lire toutes les VMs. Un utilisateur avec `object_read` lié à un objet sur un ID de VM spécifique ne peut lire que cette seule VM.

Lors de la vérification des permissions, le système recherche d'abord une permission liée à un objet. Si aucune n'est trouvée, il se rabat sur la permission globale.

:::note Types d'objets uniquement globaux
Certains types d'objets ne prennent en charge que les permissions globales (pas de permissions liées à un objet) : Activity, Changelog, Dashboard, Language, Mail, ObjectPermission, Proxmox, SubTask, System, Tag, Task.
:::

## Rôles {#roles}

Les rôles regroupent des permissions et peuvent être attribués à plusieurs utilisateurs. Les utilisateurs héritent de toutes les permissions de leurs rôles attribués.

- **Rôles personnalisés** — Peuvent être librement créés, modifiés et supprimés
- **Rôles système** — Rôles prédéfinis et protégés qui ne peuvent pas être supprimés

Un utilisateur peut avoir plusieurs rôles. Les permissions effectives résultent de la combinaison de toutes les permissions directes et de toutes les permissions des rôles.

## Vérification des permissions {#authorization-flow}

Pour chaque action protégée, le backend vérifie la permission via le `PermissionChecker` :

1. **Charger les permissions effectives** — Toutes les permissions directes de l'utilisateur et toutes les permissions de ses rôles sont fusionnées
2. **Résoudre la permission** — La clé de permission demandée est vérifiée par rapport aux permissions effectives (y compris la hiérarchie)
3. **Résultat** — Si la permission existe, l'action est exécutée, sinon `403 Forbidden` est renvoyé

## Visibilité dans le frontend {#frontend-visibility}

Le frontend récupère les permissions effectives de l'utilisateur connecté via l'API. Sur cette base, les actions et éléments de l'interface utilisateur sont affichés ou masqués — les boutons pour créer, modifier ou supprimer ne sont affichés que si l'utilisateur possède la permission correspondante.

## Modèle de données {#data-model}

Le système de permissions repose sur les tables de base de données suivantes :

| Table                    | Description                                                                  |
| ------------------------ | ---------------------------------------------------------------------------- |
| `sys_users`              | Comptes utilisateur                                                          |
| `sys_roles`              | Rôles avec nom, clé et statut de protection                                  |
| `sys_users_roles`        | Association des utilisateurs aux rôles (n:m)                                 |
| `sys_object_permissions` | Toutes les permissions — aussi bien pour les utilisateurs que pour les rôles |

La table `sys_object_permissions` réunit toutes les attributions de permissions dans une structure unique :

| Champ            | Description                                           |
| ---------------- | ----------------------------------------------------- |
| `object_type`    | Type de ressource (par ex. `VirtualMachine`, `Event`) |
| `object_id`      | Instance spécifique (vide = global)                   |
| `entity_id`      | ID de l'utilisateur ou du rôle                        |
| `entity_type`    | `User` ou `Role`                                      |
| `permission_key` | Clé de permission (par ex. `object_read`)             |
