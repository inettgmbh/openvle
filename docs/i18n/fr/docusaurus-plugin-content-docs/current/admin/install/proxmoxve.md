---
id: proxmoxve
sidebar_label: Intégration Proxmox VE
sidebar_position: 20
status: finished
tags:
  - installation
  - proxmox
format: md
---

# Proxmox VE — Intégration {#proxmox-ve-integration}

Ce guide décrit les étapes pour intégrer OpenVLE avec Proxmox VE (PVE), y compris la configuration des utilisateurs, des permissions et de l'accès API.

:::caution Composant obligatoire
Proxmox VE est une dépendance essentielle d'OpenVLE. Sans configuration Proxmox correcte, l'application démarre, mais toutes les actions sur les VMs et les modèles de VM (création, clonage, démarrage, arrêt, suppression) échouent.
:::

## Configurer l'utilisateur et le token Proxmox {#setup-user-and-token}

Pour utiliser l'API Proxmox, il faut créer un pool, un utilisateur, un token API, des rôles et les permissions correspondantes.

### Créer un pool {#create-pool}

Créez un pool comme `OpenVLE-VMs`.
Ce pool sera utilisé pour tous les templates et VMs gérés par OpenVLE. Seuls les VMs et templates de ce pool sont visibles pour OpenVLE.

<details>
<summary>Commande CLI</summary>

```bash
pvesh create /pools --poolid 'OpenVLE-VMs'
```

</details>

<details>
<summary>WebGUI</summary>

```bash
Datacenter -> Permissions -> Pools -> Add
```

</details>

### Créer un compte utilisateur {#create-user}

Créez un utilisateur comme `OpenVLE@pve` — vous pouvez choisir n'importe quel nom d'utilisateur
(nous utilisons celui-ci comme référence dans la suite du guide).
Cet utilisateur sera utilisé pour toutes les interactions d'OpenVLE avec Proxmox. Il peut s'agir d'un compte `@pve`, `@pam`, `@ldap` ou de tout autre type.
Comme OpenVLE se connecte via un token API, le realm du backend n'a pas d'importance.
Le compte n'a pas besoin de mot de passe (remarque : les comptes sans mot de passe ne peuvent être créés que via la CLI PVE, pas via la WebGUI).
Les attributs utilisateur tels que `Prénom / Nom`, `E-mail` et `Commentaire` peuvent être définis librement — ils ne sont pas pertinents pour le fonctionnement d'OpenVLE. L'utilisateur doit simplement avoir le drapeau `Enabled` à true.

<details>
<summary>Commande CLI</summary>

```bash
pvesh create /access/users --userid 'OpenVLE@pve'
```

</details>

<details>
<summary>WebGUI</summary>

```bash
Datacenter -> Permissions -> Users -> Add
```

</details>

### Générer un token API {#generate-api-token}

Générez un token API pour l'utilisateur que vous venez de créer.
Comme `Token ID`, vous pouvez choisir un identifiant quelconque — nous utilisons ici `prod01`.
Définissez `Privilege Separation` sur **true**.
Notez les détails du token, car ils ne seront affichés qu'une seule fois.

:::note Pourquoi Privilege Separation ?
Sans Privilege Separation, un token API hérite automatiquement de toutes les permissions de son utilisateur. Avec Privilege Separation activée, un token ne dispose que des permissions qui lui sont **explicitement** attribuées.

Cela permet d'exploiter plusieurs instances OpenVLE de manière isolée avec un seul utilisateur Proxmox : créez pour chaque instance (par ex. production, staging, test) un token API distinct et attribuez à chaque token uniquement le pool de VMs correspondant. Ainsi, une instance staging ne peut accéder qu'à ses propres VMs, sans voir ni affecter les VMs de production.

**Exemple :** Un utilisateur `OpenVLE@pve` avec deux tokens :

- `OpenVLE@pve!prod01` → Pool `OpenVLE-Prod` (environnement de production)
- `OpenVLE@pve!staging01` → Pool `OpenVLE-Staging` (environnement de test)
  :::

<details>
<summary>Commande CLI</summary>

```bash
pvesh create /access/users/OpenVLE@pve/token/prod01
```

</details>

<details>
<summary>WebGUI</summary>

```bash
Datacenter -> Permissions -> API Tokens -> Add
```

</details>

### Créer deux rôles sur le PVE {#create-roles}

Comme l'utilisateur et le token API nécessitent des permissions différentes sur différents chemins au sein de PVE, deux rôles doivent être créés.

1. `OpenVLE-Infra-General` avec les privilèges suivants :
   1. `Sys.Audit`
   2. `Sys.Console`
2. `OpenVLE-Infra-VMs` avec les privilèges suivants :
   1. `VM.Allocate`
   2. `VM.Audit`
   3. `VM.Clone`
   4. `VM.Config.Disk`
   5. `VM.Config.CDROM`
   6. `VM.Config.CPU`
   7. `VM.Config.Memory`
   8. `VM.Config.Network`
   9. `VM.Config.HWType`
   10. `VM.Config.Options`
   11. `VM.Config.Cloudinit`
   12. `VM.GuestAudit`
   13. `VM.Migrate`
   14. `VM.Monitor`
   15. `VM.PowerMgmt`

:::note Proxmox VE < 9
Le privilège `VM.GuestAudit` n'existe qu'à partir de Proxmox VE 9. Si vous utilisez une version antérieure, omettez ce privilège.
:::

<details>
<summary>À quoi servent ces privilèges ?</summary>

**`OpenVLE-Infra-General`** — Attribué sur le chemin `/` et permet les requêtes à l'échelle du système :

| Privilège                                                                                       | Utilisation dans OpenVLE                                                                                                                         |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a>   | Interroger le statut et les ressources du cluster, consulter les statistiques des nœuds, vérifier le statut des tâches, lire la configuration HA |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Console</code></a> | Créer, modifier et supprimer la configuration HA pour les VMs                                                                                    |

**`OpenVLE-Infra-VMs`** — Attribué sur le pool de VMs et permet la gestion des VMs et des templates :

| Privilège                                                                                         | Utilisation dans OpenVLE                                                                          |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Allocate</code></a>   | Créer et supprimer des VMs et des templates                                                       |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Audit</code></a>      | Interroger le statut et la configuration des VMs, régénérer la configuration CloudInit            |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Clone</code></a>      | Cloner des VMs et des templates                                                                   |
| `VM.Config.*`                                                                                     | Modifier la configuration des VMs (Disk, CDROM, CPU, Memory, Network, HWType, Options, Cloudinit) |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.GuestAudit</code></a> | Exécuter les requêtes et commandes Guest Agent (à partir de PVE 9, omettre pour PVE < 9)          |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Migrate</code></a>    | Migrer les VMs entre les nœuds                                                                    |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Monitor</code></a>    | Lire les interfaces réseau (par ex. déterminer l'adresse IPv4 d'une VM)                           |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.PowerMgmt</code></a>  | Démarrer, arrêter, redémarrer, éteindre, suspendre et reprendre les VMs                           |

</details>

<details>
<summary>Commande CLI</summary>

```bash
pvesh create /access/roles --roleid 'OpenVLE-Infra-General' --privs 'Sys.Audit,Sys.Console'
pvesh create /access/roles --roleid 'OpenVLE-Infra-VMs' --privs 'VM.Allocate, VM.Audit, VM.Clone, VM.Config.Disk, VM.Config.CDROM, VM.Config.CPU, VM.Config.Memory, VM.Config.Network, VM.Config.HWType, VM.Config.Options, VM.Config.Cloudinit, VM.GuestAudit, VM.Migrate, VM.Monitor, VM.PowerMgmt'
```

</details>

<details>
<summary>WebGUI</summary>

```bash
Datacenter -> Permissions -> Roles -> Create
```

</details>

### Attribuer les permissions {#assign-permissions}

Toutes les permissions suivantes doivent être attribuées **aussi bien** à l'utilisateur (`OpenVLE@pve`) **qu'au** token API (`OpenVLE@pve!prod01`). En raison de la `Privilege Separation`, Proxmox valide les permissions des deux identités de manière indépendante — si une attribution manque, les appels API échouent.

#### Attribuer les rôles correspondants {#assign-roles}

Les rôles créés précédemment doivent être attribués sur les chemins respectifs.

**1. Permissions système générales (`OpenVLE-Infra-General`)**

- Chemin : `/`
- Rôle : `OpenVLE-Infra-General`
- Propagate : True

Cette attribution permet les opérations à l'échelle du système : interroger le statut et les ressources du cluster, consulter les statistiques des nœuds, vérifier le statut des tâches et gérer les configurations HA.

**2. Permissions VM dans le pool (`OpenVLE-Infra-VMs`)**

- Chemin : `/pool/OpenVLE-VMs`
- Rôle : `OpenVLE-Infra-VMs`
- Propagate : True

Cette attribution restreint la gestion des VMs au pool créé précédemment. OpenVLE peut ainsi créer, cloner, configurer, contrôler et supprimer des VMs et des templates au sein de ce pool — mais ne peut pas affecter les VMs en dehors du pool.

#### Attribuer les permissions de stockage et de réseau {#assign-storage-network}

Lors du clonage de VMs, Proxmox nécessite des permissions supplémentaires sur le stockage et le réseau utilisés. Sans ces permissions, le clonage échoue avec une erreur de permission, même si les droits sur la VM sont correctement définis.

:::caution Dépend de l'environnement
Les chemins suivants sont des exemples. Vous devez les adapter au stockage et au réseau de votre environnement.

Si vos VMs et templates utilisent différents stockages ou réseaux (par ex. VMs sur `local-lvm` et templates sur `ceph`, ou VMs dans différents VLANs), vous devez attribuer la permission respective **par stockage ou réseau** séparément. Créez simplement des attributions supplémentaires avec le même rôle sur les chemins additionnels.
:::

**3. Permissions de stockage**

Créez une attribution par stockage utilisé :

- Chemin : `/storage/ceph` (remplacez `ceph` par le nom de votre stockage)
- Rôle : `PVEDatastoreUser`
- Propagate : True

Permet l'allocation d'images disque lors du clonage et de la création de VMs sur le stockage spécifié. Si vos VMs et templates utilisent plusieurs stockages, répétez cette étape pour chaque stockage (par ex. `/storage/local-lvm`, `/storage/nfs-share`).

**4. Permissions SDN/réseau**

Créez une attribution par segment réseau utilisé :

- Chemin : `/sdn/zones/localnetwork/vmbr1/10` (remplacez par votre zone, bridge et VLAN)
- Rôle : `PVESDNUser`
- Propagate : True

Permet l'attribution d'interfaces réseau lors du clonage et de la configuration de VMs. Si les VMs sont exploitées dans différents VLANs ou bridges, répétez cette étape pour chaque segment réseau (par ex. `/sdn/zones/localnetwork/vmbr1/20`).

#### Commandes CLI et WebGUI {#cli-and-webgui}

<details>
<summary>Commandes CLI (les 4 attributions)</summary>

**Remplacez les valeurs pour l'utilisateur, le token API, le pool, le stockage et le réseau par les vôtres.**

```bash
# 1. Permissions système générales
pvesh set /access/acl --path '/' \
--roles 'OpenVLE-Infra-General' \
--users 'OpenVLE@pve' --tokens 'OpenVLE@pve!prod01'

# 2. Permissions VM dans le pool
pvesh set /access/acl --path '/pool/OpenVLE-VMs' \
--roles 'OpenVLE-Infra-VMs' \
--users 'OpenVLE@pve' --tokens 'OpenVLE@pve!prod01'

# 3. Permissions de stockage
pvesh set /access/acl --path '/storage/ceph' \
--roles 'PVEDatastoreUser' \
--users 'OpenVLE@pve' --tokens 'OpenVLE@pve!prod01'

# 4. Permissions SDN/réseau
pvesh set /access/acl --path '/sdn/zones/localnetwork/vmbr1/10' \
--roles 'PVESDNUser' \
--users 'OpenVLE@pve' --tokens 'OpenVLE@pve!prod01'
```

</details>

<details>
<summary>WebGUI</summary>

Pour chacune des 4 attributions :

```
Datacenter -> Permissions -> Add -> User Permission
Datacenter -> Permissions -> Add -> API Token Permission
```

Sélectionnez le chemin et le rôle, puis définissez Propagate sur True.

</details>

## Référence API {#api-reference}

OpenVLE utilise les endpoints API Proxmox VE suivants. Cette vue d'ensemble sert de référence pour l'analyse des erreurs liées aux permissions. La documentation API complète de Proxmox est disponible dans le <a href="https://pve.proxmox.com/pve-docs/api-viewer/"><code>PVE API Viewer</code></a>.

<details>
<summary>Vue d'ensemble complète des endpoints API</summary>

### Opérations cluster {#cluster-operations}

Les endpoints avec le privilège « Aucun\* » ne nécessitent pas de privilège explicite, mais ne retournent que les objets auxquels l'utilisateur ou le token a accès via d'autres permissions (par ex. `Sys.Audit`, `VM.Audit`). L'ensemble des résultats est filtré dynamiquement par Proxmox en fonction des permissions existantes.

| Endpoint                                                                                                      | Méthode | Privilège requis                                                                              | Fonction                                                        |
| ------------------------------------------------------------------------------------------------------------- | ------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/resources"><code>/cluster/resources</code></a> | GET     | Aucun\*                                                                                       | Interroger les ressources du cluster et l'affectation des nœuds |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/status"><code>/cluster/status</code></a>       | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a> | Interroger le statut du cluster                                 |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/nextid"><code>/cluster/nextid</code></a>       | GET     | Aucun\*                                                                                       | Déterminer le prochain ID de VM disponible                      |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/log"><code>/cluster/log</code></a>             | GET     | Aucun\*                                                                                       | Récupérer les logs PVE                                          |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/tasks"><code>/cluster/tasks</code></a>         | GET     | Aucun\*                                                                                       | Lister les tâches du cluster en cours                           |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes"><code>/nodes</code></a>                         | GET     | Aucun                                                                                         | Lister tous les nœuds PVE                                       |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/rrd"><code>/nodes/{node}/rrd</code></a>   | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a> | Consulter les statistiques du nœud                              |

### Haute disponibilité (HA) {#high-availability}

| Endpoint                                                                                                                        | Méthode | Privilège requis                                                                                | Fonction                              |
| ------------------------------------------------------------------------------------------------------------------------------- | ------- | ----------------------------------------------------------------------------------------------- | ------------------------------------- |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources"><code>/cluster/ha/resources</code></a>             | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a>   | Lister toutes les ressources HA       |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources"><code>/cluster/ha/resources</code></a>             | POST    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Console</code></a> | Activer la HA pour une VM             |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources/{sid}"><code>/cluster/ha/resources/{sid}</code></a> | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a>   | Interroger le statut HA d'une VM      |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources/{sid}"><code>/cluster/ha/resources/{sid}</code></a> | PUT     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Console</code></a> | Modifier la configuration HA d'une VM |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources/{sid}"><code>/cluster/ha/resources/{sid}</code></a> | DELETE  | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Console</code></a> | Désactiver la HA pour une VM          |

### Gestion des VMs {#vm-management}

| Endpoint                                                                                                                                                                              | Méthode | Privilège requis                                                                                                                                                                              | Fonction                             |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/config"><code>/nodes/{node}/qemu/{vmid}/config</code></a>                                             | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Audit</code></a>                                                                                                  | Interroger la configuration de la VM |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/config"><code>/nodes/{node}/qemu/{vmid}/config</code></a>                                             | PUT     | `VM.Config.*`                                                                                                                                                                                 | Modifier la configuration de la VM   |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/status/current"><code>/nodes/{node}/qemu/{vmid}/status/current</code></a>                             | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Audit</code></a>                                                                                                  | Interroger le statut actuel de la VM |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/clone"><code>/nodes/{node}/qemu/{vmid}/clone</code></a>                                               | POST    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Clone</code></a>, <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Allocate</code></a> | Cloner une VM ou un template         |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}"><code>/nodes/{node}/qemu/{vmid}</code></a>                                                           | DELETE  | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Allocate</code></a>                                                                                               | Supprimer une VM                     |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/migrate"><code>/nodes/{node}/qemu/{vmid}/migrate</code></a>                                           | POST    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Migrate</code></a>                                                                                                | Migrer une VM vers un autre nœud     |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/cloudinit"><code>/nodes/{node}/qemu/{vmid}/cloudinit</code></a>                                       | PUT     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Audit</code></a>                                                                                                  | Régénérer la configuration CloudInit |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces"><code>/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces</code></a> | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Monitor</code></a>                                                                                                | Lire les interfaces réseau (IPv4)    |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/tasks/{upid}/status"><code>/nodes/{node}/tasks/{upid}/status</code></a>                                           | GET     | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a>                                                                                                 | Interroger le statut d'une tâche     |

### Contrôle des VMs (Power Management) {#power-management}

| Endpoint                                                                                                                                           | Méthode | Privilège requis                                                                                 | Fonction                                                                              |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/status"><code>/nodes/{node}/qemu/{vmid}/status/{action}</code></a> | POST    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.PowerMgmt</code></a> | Contrôler la VM : `start`, `stop`, `shutdown`, `reboot`, `reset`, `resume`, `suspend` |

</details>
