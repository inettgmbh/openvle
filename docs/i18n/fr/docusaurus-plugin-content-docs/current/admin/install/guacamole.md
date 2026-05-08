---
id: guacamole
sidebar_label: Intégration Apache Guacamole
sidebar_position: 30
status: finished
tags:
  - installation
  - guacamole
---

# Apache Guacamole — Intégration {#guacamole-integration}

Apache Guacamole permet un accès bureau à distance via le navigateur (RDP, VNC, SSH) sans logiciel client. OpenVLE utilise Guacamole pour permettre aux utilisateurs d'accéder aux machines virtuelles directement dans le navigateur.

Guacamole fonctionne comme un service séparé et ne fait **pas** partie du stack Docker standard d'OpenVLE. Pour l'installation et l'exploitation de Guacamole, nous renvoyons à la documentation officielle.

:::info Composant optionnel
Guacamole est optionnel, mais recommandé. Sans Guacamole, OpenVLE peut toujours être utilisé pour gérer les VMs et les modèles de VM — l'accès bureau à distance via le navigateur n'est alors pas disponible.
:::

## Prérequis {#prerequisites}

- Serveur séparé ou hôte Docker pour Guacamole
- Accès réseau du backend OpenVLE au serveur Guacamole (par défaut : port 8080, ou 443 pour HTTPS)
- Une base de données MariaDB/MySQL pour Guacamole

:::caution Base de données séparée
Guacamole nécessite sa **propre** base de données — n'utilisez pas l'instance MariaDB d'OpenVLE.
:::

## Installation {#installation}

La documentation officielle Docker d'Apache Guacamole décrit la configuration en détail :

- [Apache Guacamole Docker Installation](https://guacamole.apache.org/doc/gug/guacamole-docker.html)

Une installation Guacamole typique se compose de trois conteneurs :

| Conteneur      | Fonction                                                                  |
| -------------- | ------------------------------------------------------------------------- |
| `guacd`        | Proxy de connexion — gère les connexions bureau à distance                |
| `guacamole`    | Frontend web — fournit l'interface utilisateur                            |
| `guacamole-db` | Base de données — stocke les utilisateurs, connexions et la configuration |

## Créer un utilisateur OpenVLE dans Guacamole {#create-openvle-user}

OpenVLE nécessite un compte administrateur dédié dans Guacamole pour pouvoir gérer automatiquement les connexions. Créez cet utilisateur via l'interface web de Guacamole :

1. Connectez-vous en tant qu'administrateur dans l'interface web de Guacamole
2. Naviguez vers **Paramètres → Utilisateurs → Nouvel utilisateur**
3. Créez un utilisateur avec des droits d'administrateur
4. Notez le nom d'utilisateur et le mot de passe — ils seront nécessaires à l'étape suivante

## Configurer le backend OpenVLE {#configure-backend}

Saisissez les informations de connexion Guacamole dans le fichier `.env` du backend. La référence complète de toutes les variables d'environnement se trouve sous [Configuration](configuration?stack=backend).

| Variable                              | Description                                                | Exemple                        |
| ------------------------------------- | ---------------------------------------------------------- | ------------------------------ |
| `GUACAMOLE_URL`                       | URL du serveur Guacamole                                   | `http://guacamole-server:8080` |
| `GUACAMOLE_DB`                        | Type de base de données de Guacamole                       | `mysql`                        |
| `GUACAMOLE_USER`                      | Nom d'utilisateur du compte OpenVLE                        | `OpenVLE`                      |
| `GUACAMOLE_PASSWORD`                  | Mot de passe du compte OpenVLE                             | `sicheres-passwort`            |
| `GUACAMOLE_CONNECTIONS_PREFIX`        | Préfixe pour les connexions créées automatiquement         | `openvle-`                     |
| `GUACAMOLE_CONNECTIONS_PREFIX_EVENTS` | Utiliser le préfixe aussi pour les connexions d'événements | `True`                         |

## Vérification {#verification}

1. Accédez à l'**interface web Guacamole** et vérifiez que la connexion fonctionne
2. Vérifiez dans les **logs du backend OpenVLE** que la connexion à Guacamole est réussie :
   ```bash
   docker logs openvle-backend 2>&1 | grep -i guacamole
   ```
3. Créez dans OpenVLE une **VM de test avec connexion** et vérifiez que la connexion Guacamole est créée automatiquement

## Dépannage {#troubleshooting}

| Problème                                          | Solution                                                                                                                                                                                               |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Le backend ne peut pas atteindre Guacamole        | Vérifiez que `GUACAMOLE_URL` est correctement défini dans le fichier `.env` et que l'accès réseau entre le backend et Guacamole est assuré.                                                            |
| La connexion à l'interface web Guacamole échoue   | Vérifiez que la configuration initiale de la base de données a été correctement effectuée.                                                                                                             |
| Les connexions ne sont pas créées automatiquement | Vérifiez les logs du backend (`docker logs openvle-backend`) pour les messages d'erreur liés à Guacamole et assurez-vous que l'utilisateur OpenVLE dispose des droits d'administrateur dans Guacamole. |

## Documentation complémentaire {#further-reading}

- [Infrastructure : Guacamole](/docs/admin/infrastructure/guacamole) — Architecture et exigences réseau
- [Utilisation : Guacamole](/docs/usage/guacamole/) — Guide pour les utilisateurs finaux
