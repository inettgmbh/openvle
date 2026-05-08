---
id: proxmoxve
sidebar_label: Proxmox VE
sidebar_position: 50
status: finished
tags:
  - infrastructure
  - proxmox
---

# Proxmox VE {#proxmox}

Proxmox VE est l'hyperviseur sur lequel OpenVLE gère les machines virtuelles et les modèles de VM. OpenVLE communique exclusivement avec le cluster via l'API REST de Proxmox — il n'y a pas d'accès direct aux hôtes Proxmox.

:::caution Composant requis
Proxmox VE est une dépendance essentielle d'OpenVLE. Sans configuration correcte de Proxmox, l'application démarre certes, mais toutes les actions sur les VMs et les modèles de VM échoueront.
:::

## Connexion {#connection}

OpenVLE se connecte à l'API Proxmox via la bibliothèque Python `proxmoxer`. L'authentification se fait par **jeton API** (et non par mot de passe) :

| Paramètre         | Description                      | Exemple                    |
| ----------------- | -------------------------------- | -------------------------- |
| `PVE_HOSTNAME`    | Point d'accès API (hôte:port)    | `proxmox.example.com:8006` |
| `PVE_USER`        | Utilisateur Proxmox (User@Realm) | `OpenVLE@pve`              |
| `PVE_TOKEN_NAME`  | Identifiant du jeton             | `prod01`                   |
| `PVE_TOKEN_VALUE` | Secret du jeton                  | `xxxxxxxx-xxxx-...`        |
| `PVE_VERIFY_SSL`  | Vérifier le certificat SSL       | `True`                     |

## Concept de pool {#pools}

Toutes les VMs et modèles de VM gérés par OpenVLE sont organisés dans un pool Proxmox dédié (configuré via `PVE_VMS_POOL`, par défaut : `OpenVLE-VMs`). Les permissions Proxmox du jeton API OpenVLE sont restreintes à ce pool — OpenVLE ne peut donc **ni voir, ni contrôler, ni supprimer de VMs en dehors du pool**. Les autres charges de travail sur le même cluster Proxmox restent entièrement isolées et intactes.

Grâce à la combinaison du pool et de la séparation des privilèges, plusieurs instances OpenVLE (par exemple production, staging) peuvent être exploitées sur le même cluster Proxmox : chaque instance reçoit son propre jeton API avec accès à son propre pool, sans pouvoir voir ni influencer l'autre instance.

## Cycle de vie des VMs {#vm-lifecycle}

### Modèles de VM {#templates}

Les modèles de VM (templates) sont stockés directement dans Proxmox en tant que templates QEMU. OpenVLE synchronise périodiquement leur statut et leurs métadonnées (nom, CPU, RAM, noeud) dans sa propre base de données. Les templates peuvent être créés, mis à jour et supprimés via OpenVLE.

### Opérations sur les VMs {#vm-operations}

Lors du déploiement d'un événement ou sur demande manuelle, OpenVLE crée des VMs par clonage de templates :

| Opération                 | Description                                                                                                                 |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Cloner**                | Crée une nouvelle VM à partir d'un modèle de VM (Full Clone ou Linked Clone, configurable via `PVE_VMS_FULL_CLONE_DEFAULT`) |
| **Démarrer / Arrêter**    | Démarre ou arrête une VM sur Proxmox                                                                                        |
| **Éteindre**              | Éteint proprement une VM via le QEMU Guest Agent                                                                            |
| **Redémarrer**            | Redémarre une VM en cours d'exécution                                                                                       |
| **Réinitialiser**         | Hard-Reset d'une VM                                                                                                         |
| **Suspendre / Reprendre** | Suspend une VM ou la reprend                                                                                                |
| **Migrer**                | Déplace une VM vers un autre noeud Proxmox (en ligne ou hors ligne)                                                         |
| **Supprimer**             | Supprime une VM de Proxmox et nettoie la base de données                                                                    |

## Gestion des noeuds {#node-management}

OpenVLE est entièrement compatible multi-noeuds et fonctionne avec un nombre quelconque de noeuds Proxmox :

- **Découverte des noeuds** — La synchronisation périodique détecte tous les noeuds du cluster et enregistre leur statut
- **Sélection automatique du noeud** — Lors du clonage d'une VM, OpenVLE sélectionne automatiquement le noeud disposant de la plus grande capacité CPU disponible
- **Suivi des noeuds** — Pour chaque VM et modèle de VM, le noeud sur lequel il se trouve est enregistré. Lors des migrations, cette information est automatiquement mise à jour

## Réseau et attribution d'IP {#networking}

OpenVLE prend en charge deux méthodes de configuration réseau pour les VMs.

:::note Sans Apache Guacamole
Si OpenVLE est exploité sans Apache Guacamole — par exemple uniquement pour la gestion et le déploiement de VMs sans accès bureau à distance via le web — les informations réseau des VMs ne sont pas strictement nécessaires pour OpenVLE. Les adresses IP sont dans ce cas toujours lues et affichées, mais ne sont pas indispensables pour les fonctionnalités principales.
:::

### DHCP (standard, recommandé) {#dhcp}

En fonctionnement standard (`PVE_CI_ENABLED=False`), OpenVLE attend qu'un serveur DHCP externe soit actif dans le sous-réseau/VLAN des VMs pour leur attribuer dynamiquement des adresses IP. Les modèles de VM doivent simplement être configurés en DHCP.

Après le démarrage d'une VM, OpenVLE lit l'adresse IPv4 attribuée par le DHCP via le QEMU Guest Agent depuis la VM et l'enregistre dans la base de données. C'est la méthode standard recommandée.

### Cloud-Init (expérimental) {#cloud-init-networking}

Lorsque Cloud-Init est activé (`PVE_CI_ENABLED=True`), OpenVLE prend en charge l'attribution des IP lui-même et écrit une configuration IP statique directement dans la VM :

1. Le sous-réseau est formé à partir de `PVE_VMS_NETWORK` et `PVE_VMS_SUBNET`
2. Les IP déjà attribuées (depuis la base de données) et les IP exclues (`PVE_VMS_EXCLUDED_IPS`) sont ignorées
3. La première IP libre est attribuée à la nouvelle VM via Cloud-Init (y compris la passerelle et le DNS)

:::caution Expérimental
L'attribution d'IP basée sur Cloud-Init est actuellement une fonctionnalité expérimentale. Vous trouverez plus de détails et toutes les variables Cloud-Init sous [Cloud-Init](#cloud-init) et dans la [Référence de configuration — Proxmox VE](../install/configuration#proxmox).
:::

### QEMU Guest Agent {#guest-agent}

OpenVLE requiert que le QEMU Guest Agent soit installé dans les VMs. Il est nécessaire pour les fonctionnalités suivantes :

- **Détection d'IP** — Lecture de l'adresse IPv4 réelle d'une VM en cours d'exécution (avec DHCP et Cloud-Init)
- **Arrêt propre** — Graceful Shutdown via l'agent

:::note Permission Proxmox
À partir de Proxmox VE 9, le privilège `VM.GuestAudit` est requis sur le pool pour qu'OpenVLE puisse exécuter les requêtes et commandes du Guest Agent. Pour PVE < 9, ce privilège n'existe pas et peut être omis. Vous trouverez les détails de la mise en place sous [Proxmox VE — Intégration](../install/proxmoxve#create-roles).
:::

## Synchronisation périodique {#periodic-sync}

Le Worker `worker-periodic` synchronise le statut entre Proxmox et OpenVLE toutes les `WORKER_PVE_PERIODIC_INTERVAL` secondes (par défaut : 60) :

1. **Récupérer les ressources du cluster** — Liste complète de toutes les VMs, templates et noeuds depuis Proxmox
2. **Mettre à jour MongoDB** — Instantané des ressources du cluster pour un accès rapide
3. **Mettre à jour MariaDB** — Mises à jour de statut pour toutes les VMs et templates connus (par exemple `cloning` → `running`, changement de noeud lors d'une migration)
4. **Créer le changelog** — Toutes les modifications de statut sont consignées

Les VMs dans des états transitoires (`starting`, `deleting`, `stopping`) sont ignorées lors de la synchronisation pour éviter les conflits avec les opérations en cours.

## Fonctionnalités optionnelles {#optional-features}

### Cloud-Init (expérimental) {#cloud-init}

Lorsque Cloud-Init est activé (`PVE_CI_ENABLED=True`), OpenVLE configure automatiquement les nouvelles VMs, en plus de l'[attribution d'IP](#cloud-init-networking), avec :

- Nom d'utilisateur et mot de passe (`PVE_VMS_CIUSER`, `PVE_VMS_CIPASSWORD`)
- Mise à jour optionnelle des paquets au premier démarrage (`PVE_VMS_CIUPGRADE`)

Vous trouverez toutes les variables Cloud-Init dans la [Référence de configuration — Proxmox VE](../install/configuration#proxmox).

### Métadonnées SMBIOS {#smbios}

Lorsque `PVE_VMS_SMBIOS_METADATA` est activé (par défaut : `True`), OpenVLE écrit des métadonnées de l'application dans les informations SMBIOS (Type 1) de la VM :

| Champ SMBIOS   | Contenu             |
| -------------- | ------------------- |
| `manufacturer` | Nom du projet       |
| `product`      | Nom de la VM        |
| `version`      | ID du template      |
| `serial`       | UUID VM OpenVLE     |
| `family`       | Slug de l'événement |

Ces métadonnées sont lisibles depuis le système d'exploitation invité (par exemple via `dmidecode` sous Linux ou WMI sous Windows) et permettent de mettre en place des automatisations personnalisées au sein des VMs. Les scripts dans la VM peuvent ainsi identifier à l'exécution à quel événement et environnement ils appartiennent, et ajuster automatiquement des configurations, démarrer des services ou synchroniser des données en conséquence — sans avoir à établir une connexion API directe avec OpenVLE.

### Haute disponibilité {#high-availability}

Les VMs des événements sont par défaut intégrées dans la configuration HA de Proxmox et bénéficient ainsi automatiquement de la haute disponibilité du cluster : en cas de défaillance d'un noeud, les VMs sont automatiquement redémarrées sur un autre noeud. OpenVLE gère entièrement la configuration HA — les VMs sont ajoutées lors du déploiement et retirées lors de l'archivage.

## Informations complémentaires {#further-reading}

- [Configurer l'intégration Proxmox VE](../install/proxmoxve) — Mise en place de l'utilisateur, du jeton, des rôles et des permissions
- [Référence de configuration — Proxmox VE](../install/configuration#proxmox) — Toutes les variables d'environnement Proxmox
- [Système de tâches](task-system) — Queues et Workers pour les opérations VM
