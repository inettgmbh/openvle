---
id: requirements
sidebar_label: Conditions requises
sidebar_position: 11
status: finished
tags:
  - installation
  - requirements
---

# Conditions requises {#requirements}

Pour faire fonctionner OpenVLE, un serveur dédié est nécessaire.

Puisque OpenVLE requiert Proxmox VE comme hyperviseur (voir [Intégration Proxmox VE](proxmoxve)), nous recommandons d'exécuter OpenVLE en tant que machine virtuelle directement sur l'hôte Proxmox. Cela évite d'avoir besoin de matériel supplémentaire, et les sauvegardes ainsi que les snapshots de la VM OpenVLE peuvent être gérés par Proxmox lui-même.

:::tip Séparation des VM de production
Créez la VM OpenVLE en dehors du pool `OpenVLE-VMs` configuré dans Proxmox afin qu'elle ne soit pas gérée par OpenVLE lui-même.
:::

## Ressources {#resources}

Les ressources nécessaires dépendent de la charge ultérieure de l'interface d'administration OpenVLE. Plus le nombre d'utilisateurs accédant simultanément est élevé, plus les ressources requises sont importantes. Pour commencer, nous recommandons la configuration suivante pour la VM :

- 4 cœurs CPU
- 8 Go de mémoire vive
- 50 Go d'espace disque

## Système d'exploitation {#operating-system}

Sont officiellement prises en charge toutes les distributions Linux sur lesquelles Docker peut être officiellement installé. Cela couvre les distributions les plus courantes comme Ubuntu, Debian et Red Hat Enterprise Linux.

## Installation de Docker (Compose) {#install-docker}

Il faut d'abord installer la version officielle actuelle de `docker` et `docker compose` sur le serveur.

Le moyen le plus rapide est le script Convenience officiel de Docker, qui détecte automatiquement toutes les distributions prises en charge et installe Docker ainsi que Compose V2 :

```bash
curl -fsSL https://get.docker.com | sh
```

:::caution Environnement de production
Le script Convenience est prévu pour une mise en place rapide. Pour les environnements de production avec des exigences particulières (par ex. dépôts propres, configuration proxy, versions spécifiques), nous recommandons l'installation manuelle conformément à la [documentation officielle de Docker](https://docs.docker.com/engine/install/).
:::

### Vérification {#verify-docker}

Vérifiez après l'installation que Docker et Compose sont correctement installés :

```bash
docker --version
docker compose version
```

Les deux commandes doivent afficher un numéro de version. Testez en outre que Docker est fonctionnel :

```bash
docker run --rm hello-world
```

## Dépannage {#troubleshooting}

| Problème                                      | Solution                                                                                                           |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `docker compose` introuvable                  | Assurez-vous que Docker Compose V2 est installé (en tant que plugin Docker, et non comme `docker-compose` séparé). |
| Erreur de permission sur les commandes Docker | Ajoutez votre utilisateur au groupe `docker` : `sudo usermod -aG docker $USER` puis reconnectez-vous.              |
