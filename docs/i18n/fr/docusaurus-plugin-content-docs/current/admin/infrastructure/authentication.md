---
id: authentication
sidebar_label: Authentification
sidebar_position: 40
status: finished
tags:
  - infrastructure
  - authentication
---

# Authentification {#authentication}

OpenVLE prend en charge trois méthodes d'authentification : connexion locale, LDAP et OpenID Connect (OIDC). Toutes les méthodes peuvent être actives simultanément — les utilisateurs choisissent la méthode souhaitée lors de la connexion.

:::info Authentification vs. Autorisation
L'authentification détermine **qui** est un utilisateur (vérification d'identité). L'autorisation détermine **ce que** un utilisateur est autorisé à faire (contrôle d'accès). L'autorisation est gérée par le [système de permissions](permission-system) — il fonctionne indépendamment de la méthode d'authentification choisie.
:::

## Vue d'ensemble {#overview}

| Méthode   | Activation            | Prérequis                                         | Description                                                                          |
| --------- | --------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **Local** | Toujours actif        | Aucun                                             | Le nom d'utilisateur et le mot de passe sont stockés dans la base de données OpenVLE |
| **LDAP**  | `LDAP_ENABLED = True` | Serveur LDAP (par ex. Active Directory, OpenLDAP) | Connexion avec les identifiants du service d'annuaire existant                       |
| **OIDC**  | `OIDC_ENABLED = True` | Fournisseur OIDC (par ex. Keycloak, Azure AD)     | Single Sign-On via un fournisseur d'identité externe                                 |

## Sessions basées sur des tokens {#token-sessions}

Indépendamment de la méthode d'authentification choisie, chaque utilisateur reçoit un JWT (JSON Web Token) du backend après une connexion réussie. Ce token est utilisé pour toutes les requêtes API suivantes :

- **Access Token** — Token de courte durée pour l'accès API (durée d'expiration : `AUTH_ACCESS_TOKE_EXPIRE_MINUTES`, par défaut : 480 minutes)

Les tokens sont signés avec le `AUTH_SECRET` (algorithme : HS256). Un changement du `AUTH_SECRET` déconnecte immédiatement tous les utilisateurs actifs.

## Authentification locale {#local-auth}

L'authentification locale est la méthode par défaut et est toujours disponible. Les utilisateurs se connectent avec un nom d'utilisateur et un mot de passe stockés dans la base de données MariaDB. Les comptes utilisateur locaux sont créés manuellement dans l'interface utilisateur ou via l'API.

## LDAP {#ldap}

Lorsque LDAP est activé, les utilisateurs peuvent se connecter avec leurs identifiants de service d'annuaire existants (par ex. Active Directory, OpenLDAP). OpenVLE vérifie les identifiants auprès du serveur LDAP configuré sans stocker de mot de passe local.

### Flux {#ldap-flow}

1. L'utilisateur saisit ses identifiants LDAP sur la page de connexion
2. Le backend recherche l'utilisateur dans l'annuaire LDAP (basé sur `LDAP_DN_PEOPLE` et `LDAP_ATTR_USER`)
3. Le backend effectue un LDAP Bind avec les identifiants saisis
4. En cas de succès, une session locale est créée (token JWT)

### Auto-Enrollment {#ldap-enrollment}

Les utilisateurs LDAP sont automatiquement créés dans la base de données OpenVLE lors de leur première connexion réussie. Le nom d'utilisateur et l'adresse e-mail sont repris des attributs LDAP (`LDAP_ATTR_USER`, `LDAP_ATTR_MAIL`).

### Prérequis {#ldap-requirements}

- Un serveur LDAP doit être accessible depuis le backend OpenVLE (ports par défaut : 389 pour LDAP, 636 pour LDAPS)
- L'annuaire LDAP doit contenir les utilisateurs sous le DN configuré (`LDAP_DN_PEOPLE`)

## OIDC (OpenID Connect) {#oidc}

OIDC permet le Single Sign-On (SSO) via un fournisseur d'identité externe. Les utilisateurs sont redirigés vers la page de connexion du fournisseur et, après une connexion réussie, renvoyés vers OpenVLE.

### Flux {#oidc-flow}

1. L'utilisateur clique sur « Se connecter avec SSO » sur la page de connexion
2. OpenVLE redirige l'utilisateur vers le fournisseur OIDC
3. L'utilisateur se connecte auprès du fournisseur (par ex. Keycloak, Azure AD)
4. Le fournisseur redirige l'utilisateur avec un Authorization Code vers OpenVLE
5. Le backend échange le code contre les informations utilisateur et crée une session locale

### Auto-Enrollment {#oidc-enrollment}

Si `OIDC_ENROLL_USERS = True` (par défaut), les utilisateurs sont automatiquement enregistrés dans OpenVLE lors de leur première connexion SSO. Le nom d'utilisateur, le nom et l'adresse e-mail sont repris des attributs OIDC (`OIDC_ATTR_USERNAME`, `OIDC_ATTR_NAME`, `OIDC_ATTR_EMAIL`).

Lorsque l'Auto-Enrollment est désactivé (`OIDC_ENROLL_USERS = False`), l'utilisateur doit avoir été créé manuellement au préalable dans OpenVLE.

### Synchronisation des données {#oidc-sync}

À chaque connexion OIDC, le nom et l'adresse e-mail de l'utilisateur sont mis à jour avec les valeurs actuelles du fournisseur d'identité. Ainsi, les données utilisateur dans OpenVLE restent automatiquement synchronisées avec l'IdP — que l'utilisateur ait été créé par Auto-Enrollment ou manuellement.

### Prérequis {#oidc-requirements}

- Un fournisseur OIDC doit être configuré et accessible depuis le backend
- Un client avec `OIDC_CLIENT_ID` et `OIDC_CLIENT_SECRET` doit être enregistré auprès du fournisseur
- L'URL de redirection vers OpenVLE doit être enregistrée comme URL de redirection autorisée auprès du fournisseur

## Gestion des utilisateurs et provisionnement {#user-provisioning}

LDAP et OIDC servent exclusivement à l'**authentification** et au **provisionnement à la volée** lors de la connexion. Il n'y a pas de synchronisation automatique en arrière-plan des utilisateurs — OpenVLE ne récupère pas de listes d'utilisateurs depuis LDAP ou le fournisseur OIDC.

Pour assigner un utilisateur à des objets OpenVLE (par ex. en tant que participant d'un événement), celui-ci doit être connu d'OpenVLE. Cela signifie :

- L'utilisateur s'est **connecté au moins une fois** (il est alors automatiquement créé), ou
- L'utilisateur a été **créé manuellement** — via l'import CSV dans le frontend ou via l'API

:::note Extensions prévues

- **Intégration SCIM** (fournisseur et client) — Une intégration SCIM complète est prévue dans un avenir proche et permettra le provisionnement et la synchronisation automatiques des utilisateurs avec des systèmes externes de gestion des identités.
- **Synchronisation LDAP périodique** — Sur demande client, une synchronisation LDAP périodique peut être mise en place pour synchroniser automatiquement les utilisateurs en arrière-plan.
  :::

## Remarque concernant Apache Guacamole {#guacamole-auth}

Si [Apache Guacamole](guacamole) est utilisé pour l'accès Bureau à distance, Guacamole devrait idéalement être connecté au même fournisseur d'identité (LDAP ou OIDC) qu'OpenVLE. OpenVLE provisionne les connexions Guacamole avec les mêmes noms d'utilisateur que dans OpenVLE — une gestion des utilisateurs dans Guacamole n'est pas nécessaire, car OpenVLE crée automatiquement les utilisateurs manquants. Dans Guacamole, seule l'authentification doit donc être configurée. Vous trouverez plus de détails sous [Apache Guacamole — Authentification des utilisateurs](guacamole#guacamole-auth).

## Remarque concernant Moodle {#moodle-auth}

Si [Moodle](moodle) est connecté, Moodle devrait idéalement être connecté au même fournisseur d'identité (LDAP ou OIDC) qu'OpenVLE. OpenVLE provisionne les utilisateurs Moodle avec les mêmes noms d'utilisateur que dans OpenVLE — une gestion des utilisateurs dans Moodle n'est pas nécessaire, car OpenVLE crée automatiquement les utilisateurs manquants. Dans Moodle, seule l'authentification doit donc être configurée. Vous trouverez plus de détails sous [Moodle — Synchronisation des utilisateurs](moodle#user-sync).

## Informations complémentaires {#further-reading}

- [Référence de configuration — Authentification](../install/configuration#auth) — Variables d'authentification générales
- [Référence de configuration — LDAP](../install/configuration#ldap) — Variables d'environnement LDAP
- [Référence de configuration — OIDC](../install/configuration#oidc) — Variables d'environnement OIDC
- [Système de permissions](permission-system) — Autorisation et contrôle d'accès
