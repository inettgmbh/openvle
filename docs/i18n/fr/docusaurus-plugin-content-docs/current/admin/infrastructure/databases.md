---
id: databases
sidebar_label: Bases de données
sidebar_position: 30
status: finished
tags:
  - infrastructure
  - databases
---

# Bases de données {#databases}

OpenVLE utilise trois systèmes de bases de données différents, chacun spécialisé pour des tâches distinctes : MariaDB pour les données structurées principales, MongoDB pour les activités et les journaux, ainsi que Redis comme file d'attente des tâches et cache.

## Vue d'ensemble {#overview}

| Base de données | Type                  | Données stockées                                                                                       | Persistance                        |
| --------------- | --------------------- | ------------------------------------------------------------------------------------------------------ | ---------------------------------- |
| **MariaDB**     | Relationnelle (SQL)   | Entités principales : utilisateurs, rôles, permissions, environnements, événements, VMs, modèles de VM | Volume `./mariadb/data`            |
| **MongoDB**     | Documentaire (NoSQL)  | Activités, événements système, journaux d'audit, historiques de modifications                          | Volume `./mongodb`                 |
| **Redis**       | In-Memory (Key-Value) | File d'attente des tâches, cache, communication Worker/Scheduler                                       | Persistance AOF (`appendonly yes`) |

## MariaDB {#mariadb}

MariaDB est la base de données principale et stocke toutes les entités structurées du système :

- **Utilisateurs et rôles** — Comptes, attributions de rôles, hachages de mots de passe
- **Permissions** — Définitions de permissions et attributions (voir [Système de permissions](permission-system))
- **Environnements et événements** — Environnements de cours, dates d'événements, affectations de participants
- **VMs et modèles de VM** — Machines virtuelles, leur statut et leur affectation aux événements
- **Paramètres système** — Configuration globale et paramètres

### Initialisation et migration {#mariadb-init}

Lors du premier démarrage, les conteneurs Backend et Worker prennent automatiquement en charge l'initialisation et la migration de la base de données. Le conteneur qui effectue la migration est déterminé par un mécanisme de verrouillage — le conteneur qui obtient le verrou en premier effectue la migration. Le schéma de la base de données est alors créé et les données initiales sont mises en place (par exemple le compte administrateur par défaut et les permissions par défaut).

## MongoDB {#mongodb}

MongoDB stocke des données non relationnelles qui ne nécessitent pas de structure de table fixe :

- **Activités** — Actions des utilisateurs (par exemple "L'utilisateur X a démarré la VM Y"), affichées dans la vue d'ensemble des activités de l'interface utilisateur

L'accès se fait exclusivement via le Backend. MongoDB n'est pas directement accessible de l'extérieur.

## Redis {#redis}

Redis ne sert pas de base de données classique, mais de couche de communication entre les composants de l'application :

- **File d'attente des tâches** — Le Backend met les tâches dans les files d'attente Redis, qui sont traitées par le Worker (voir [Système de tâches](task-system))
- **File d'attente du Scheduler** — Le Scheduler place les tâches périodiques dans Redis
- **Cache** — Stockage intermédiaire temporaire pour les données fréquemment consultées

Redis est configuré avec AOF (Append Only File), de sorte que les données de la file d'attente sont conservées même après un redémarrage. L'accès est protégé par mot de passe.

## Séparation des bases de données {#separation}

La répartition sur trois systèmes suit le principe d'utiliser chaque base de données dans son domaine de prédilection :

| Exigence                             | Base de données | Justification                                                  |
| ------------------------------------ | --------------- | -------------------------------------------------------------- |
| Données structurées avec relations   | MariaDB         | Clés étrangères, transactions, garanties ACID                  |
| Documents flexibles sans schéma fixe | MongoDB         | Structures de documents variables, journalisation efficace     |
| Opérations de file d'attente rapides | Redis           | Vitesse en mémoire, prise en charge native des files d'attente |

## Informations complémentaires {#further-reading}

- [Référence de configuration — MariaDB](../install/configuration#mariadb) — Toutes les variables d'environnement MariaDB
- [Référence de configuration — MongoDB](../install/configuration#mongodb) — Toutes les variables d'environnement MongoDB
- [Référence de configuration — Redis](../install/configuration#redis) — Toutes les variables d'environnement Redis
- [Sauvegardes & restauration](../operations/backups-restore) — Sauvegarde et restauration des bases de données
