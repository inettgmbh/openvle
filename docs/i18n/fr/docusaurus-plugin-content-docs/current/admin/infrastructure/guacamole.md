---
id: guacamole
sidebar_label: Apache Guacamole
sidebar_position: 55
status: finished
tags:
  - infrastructure
  - guacamole
---

# Apache Guacamole {#guacamole}

Apache Guacamole permet l'accès Bureau à distance aux machines virtuelles via le navigateur web. Les participants accèdent ainsi directement à leurs VMs depuis le navigateur — sans avoir à installer de logiciel supplémentaire.

:::info Optionnel
Apache Guacamole est un composant optionnel. Sans Guacamole, OpenVLE peut toujours être utilisé pour gérer les VMs et les modèles de VM, mais sans accès Bureau à distance dans le navigateur.
:::

## Architecture {#architecture}

Apache Guacamole est un logiciel open source qui permet l'accès à des ressources distantes via RDP, VNC, SSH et d'autres protocoles à travers un navigateur web standard. La pile Guacamole se compose de trois composants :

| Composant         | Fonction                                                                  |
| ----------------- | ------------------------------------------------------------------------- |
| **Guacamole Web** | Interface web et serveur API                                              |
| **guacd**         | Démon de connexion qui traite les protocoles distants proprement dits     |
| **Guacamole DB**  | Base de données pour les utilisateurs, les connexions et la configuration |

## Communication avec OpenVLE {#communication}

OpenVLE gère automatiquement les connexions Guacamole. Le backend communique via l'API Guacamole avec le serveur Guacamole et crée, met à jour et supprime les connexions lors des événements suivants :

- **Connexion créée** — Une nouvelle connexion Guacamole est automatiquement créée
- **VM supprimée** — La connexion associée est supprimée
- **Événement démarré/terminé** — Les connexions sont activées ou désactivées en conséquence

Pour cela, le backend OpenVLE nécessite un compte utilisateur dédié avec des permissions administratives dans Guacamole.

## Prérequis {#requirements}

Le backend OpenVLE nécessite les informations suivantes pour communiquer avec Guacamole :

| Information                         | Exemple                         |
| ----------------------------------- | ------------------------------- |
| URL du serveur Guacamole            | `https://guacamole.example.com` |
| Type de base de données Guacamole   | `mysql`                         |
| Nom d'utilisateur du compte OpenVLE | `OpenVLE`                       |
| Mot de passe du compte OpenVLE      | _(mot de passe sécurisé)_       |

Ces informations sont configurées dans le fichier `.env`. De plus, un accès réseau du serveur backend au serveur Guacamole doit être possible (par défaut HTTPS 443/tcp).

:::note Gestion automatique
Après la configuration des identifiants d'accès, aucune intervention manuelle supplémentaire dans Guacamole n'est nécessaire. OpenVLE prend en charge la gestion de toutes les connexions de manière entièrement automatique.
:::

## Authentification des utilisateurs dans Guacamole {#guacamole-auth}

Guacamole devrait idéalement être connecté au même fournisseur d'identité (LDAP ou OIDC) qu'OpenVLE. La raison : OpenVLE provisionne les connexions Guacamole avec les mêmes noms d'utilisateur que ceux utilisés dans OpenVLE. Si Guacamole utilise le même IdP, les utilisateurs peuvent se connecter directement au Bureau à distance avec leurs identifiants existants.

Une gestion manuelle des utilisateurs dans Guacamole n'est pas nécessaire — OpenVLE crée automatiquement les utilisateurs Guacamole s'ils n'existent pas encore. Dans Guacamole, seule l'authentification doit donc être configurée, pas le provisionnement.

## Informations complémentaires {#further-reading}

- [Installer Apache Guacamole](../install/guacamole) — Installation et configuration
- [Référence de configuration — Guacamole](../install/configuration#guacamole) — Toutes les variables d'environnement disponibles
