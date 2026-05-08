---
id: proxmoxve
sidebar_label: Proxmox VE Integration
sidebar_position: 20
status: finished
tags:
  - installation
  - proxmox
format: md
---

# Proxmox VE — Integration {#proxmox-ve-integration}

This guide describes the steps to integrate OpenVLE with Proxmox VE (PVE), including setting up users, permissions, and API access.

:::caution Required Component
Proxmox VE is a core dependency of OpenVLE. Without proper Proxmox configuration, the application will start but all actions involving VMs and VM templates (creating, cloning, starting, stopping, deleting) will fail.
:::

## Set Up Proxmox User and Token {#setup-user-and-token}

To use the Proxmox API, a pool, a user, an API token, roles, and the corresponding permissions must be created.

### Create Pool {#create-pool}

Create a pool such as `OpenVLE-VMs`.  
This pool will be used for all templates and VMs managed by OpenVLE. Only VMs and templates in this pool are visible to OpenVLE.

<details>
<summary>CLI command</summary>

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

### Create User Account {#create-user}

Create a user such as `OpenVLE@pve` — you can use any username
(we use this one as a reference throughout the rest of this guide).  
This user will be used for all interactions between OpenVLE and Proxmox. It can be a `@pve`, `@pam`, `@ldap`, or any other account.  
Since OpenVLE connects via an API token, the backend realm does not matter.  
The account does not need a password (note: accounts without a password can only be created via the PVE CLI, not via the WebGUI).  
User attributes such as `First name / Last name`, `Email`, and `Comment` can be set to anything — they are not relevant for OpenVLE's functionality. The user only needs to have the `Enabled` flag set to true.

<details>
<summary>CLI command</summary>

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

### Generate API Token {#generate-api-token}

Generate an API token for the user you just created.  
For the `Token ID`, you can choose any ID — we use `prod01` here.  
Set `Privilege Separation` to **true**.  
Take note of the token details, as they are only displayed once.

:::note Why Privilege Separation?
Without Privilege Separation, an API token automatically inherits all permissions of its user. With Privilege Separation enabled, however, a token only has the permissions that are **explicitly** assigned to it.

This makes it possible to run multiple OpenVLE instances in isolation with a single Proxmox user: Create a separate API token for each instance (e.g., production, staging, testing) and assign each token only its respective VM pool. This way, a staging instance can only access its own VMs without seeing or affecting the production VMs.

**Example:** A user `OpenVLE@pve` with two tokens:

- `OpenVLE@pve!prod01` → Pool `OpenVLE-Prod` (production environment)
- `OpenVLE@pve!staging01` → Pool `OpenVLE-Staging` (test environment)
  :::

<details>
<summary>CLI command</summary>

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

### Create Two Roles on PVE {#create-roles}

Since the user and the API token require different permissions on different paths within PVE, two roles must be created.

1. `OpenVLE-Infra-General` with the following privileges:
   1. `Sys.Audit`
   2. `Sys.Console`
2. `OpenVLE-Infra-VMs` with the following privileges:
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
The `VM.GuestAudit` privilege only exists from Proxmox VE 9 onwards. If you are using an older version, omit this privilege.
:::

<details>
<summary>What are these privileges used for?</summary>

**`OpenVLE-Infra-General`** — Assigned to path `/` and enables system-wide queries:

| Privilege                                                                                       | Usage in OpenVLE                                                                                       |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a>   | Query cluster status and resources, retrieve node statistics, check task status, read HA configuration |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Console</code></a> | Create, modify, and delete HA configuration for VMs                                                    |

**`OpenVLE-Infra-VMs`** — Assigned to the VM pool and enables the management of VMs and templates:

| Privilege                                                                                         | Usage in OpenVLE                                                                        |
| ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Allocate</code></a>   | Create and delete VMs and templates                                                     |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Audit</code></a>      | Query VM status and configuration, regenerate CloudInit configuration                   |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Clone</code></a>      | Clone VMs and templates                                                                 |
| `VM.Config.*`                                                                                     | Modify VM configuration (Disk, CDROM, CPU, Memory, Network, HWType, Options, Cloudinit) |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.GuestAudit</code></a> | Execute guest agent queries and commands (from PVE 9, omit for PVE < 9)                 |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Migrate</code></a>    | Migrate VMs between nodes                                                               |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Monitor</code></a>    | Read network interfaces (e.g., determine the IPv4 address of a VM)                      |
| <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.PowerMgmt</code></a>  | Start, stop, restart, shut down, pause, and resume VMs                                  |

</details>

<details>
<summary>CLI command</summary>

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

### Assign Permissions {#assign-permissions}

All of the following permissions must be assigned to **both** the user (`OpenVLE@pve`) **and** the API token (`OpenVLE@pve!prod01`). Due to `Privilege Separation`, Proxmox validates the permissions of both identities independently — if an assignment is missing, API calls will fail.

#### Assign Corresponding Roles {#assign-roles}

The previously created roles must be assigned to their respective paths.

**1. General System Permissions (`OpenVLE-Infra-General`)**

- Path: `/`
- Role: `OpenVLE-Infra-General`
- Propagate: True

This assignment enables system-wide operations: querying cluster status and resources, retrieving node statistics, checking task status, and managing HA configurations.

**2. VM Permissions in the Pool (`OpenVLE-Infra-VMs`)**

- Path: `/pool/OpenVLE-VMs`
- Role: `OpenVLE-Infra-VMs`
- Propagate: True

This assignment restricts VM management to the previously created pool. OpenVLE can then create, clone, configure, control, and delete VMs and templates within this pool — but cannot affect VMs outside the pool.

#### Assign Storage and Network Permissions {#assign-storage-network}

When cloning VMs, Proxmox requires additional permissions on the storage and network being used. Without these permissions, cloning will fail with a permission error even though the VM permissions are correctly set.

:::caution Environment-Specific
The following paths are examples. You must adapt them to the storage and network of your environment.

If your VMs and templates use different storages or networks (e.g., VMs on `local-lvm` and templates on `ceph`, or VMs in different VLANs), you must assign the respective permission **per storage or network** separately. Simply create additional assignments with the same role on the additional paths.
:::

**3. Storage Permissions**

Create one assignment per storage used:

- Path: `/storage/ceph` (replace `ceph` with your storage name)
- Role: `PVEDatastoreUser`
- Propagate: True

Allows allocating disk images when cloning and creating VMs on the specified storage. If your VMs and templates use multiple storages, repeat this step for each storage (e.g., `/storage/local-lvm`, `/storage/nfs-share`).

**4. SDN/Network Permissions**

Create one assignment per network segment used:

- Path: `/sdn/zones/localnetwork/vmbr1/10` (replace with your zone, bridge, and VLAN)
- Role: `PVESDNUser`
- Propagate: True

Allows assigning network interfaces when cloning and configuring VMs. If VMs are running in different VLANs or bridges, repeat this step for each network segment (e.g., `/sdn/zones/localnetwork/vmbr1/20`).

#### CLI Commands and WebGUI {#cli-and-webgui}

<details>
<summary>CLI commands (all 4 assignments)</summary>

**Replace the values for user, API token, pool, storage, and network with your own.**

```bash
# 1. General system permissions
pvesh set /access/acl --path '/' \
--roles 'OpenVLE-Infra-General' \
--users 'OpenVLE@pve' --tokens 'OpenVLE@pve!prod01'

# 2. VM permissions in the pool
pvesh set /access/acl --path '/pool/OpenVLE-VMs' \
--roles 'OpenVLE-Infra-VMs' \
--users 'OpenVLE@pve' --tokens 'OpenVLE@pve!prod01'

# 3. Storage permissions
pvesh set /access/acl --path '/storage/ceph' \
--roles 'PVEDatastoreUser' \
--users 'OpenVLE@pve' --tokens 'OpenVLE@pve!prod01'

# 4. SDN/network permissions
pvesh set /access/acl --path '/sdn/zones/localnetwork/vmbr1/10' \
--roles 'PVESDNUser' \
--users 'OpenVLE@pve' --tokens 'OpenVLE@pve!prod01'
```

</details>

<details>
<summary>WebGUI</summary>

For each of the 4 assignments:

```
Datacenter -> Permissions -> Add -> User Permission
Datacenter -> Permissions -> Add -> API Token Permission
```

Select the respective path and role, and set Propagate to True.

</details>

## API Reference {#api-reference}

OpenVLE uses the following Proxmox VE API endpoints. This overview serves as a reference for troubleshooting permission issues. The complete Proxmox API documentation can be found in the <a href="https://pve.proxmox.com/pve-docs/api-viewer/"><code>PVE API Viewer</code></a>.

<details>
<summary>Complete API endpoint overview</summary>

### Cluster Operations {#cluster-operations}

Endpoints with privilege "None\*" do not require an explicit privilege but only return objects that the user or token has access to through other permissions (e.g., `Sys.Audit`, `VM.Audit`). The result set is dynamically filtered by Proxmox based on existing permissions.

| Endpoint                                                                                                      | Method | Required Privilege                                                                            | Function                                     |
| ------------------------------------------------------------------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------- | -------------------------------------------- |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/resources"><code>/cluster/resources</code></a> | GET    | None\*                                                                                        | Query cluster resources and node assignments |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/status"><code>/cluster/status</code></a>       | GET    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a> | Query cluster status                         |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/nextid"><code>/cluster/nextid</code></a>       | GET    | None\*                                                                                        | Determine next available VM ID               |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/log"><code>/cluster/log</code></a>             | GET    | None\*                                                                                        | Retrieve PVE logs                            |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/tasks"><code>/cluster/tasks</code></a>         | GET    | None\*                                                                                        | List current cluster tasks                   |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes"><code>/nodes</code></a>                         | GET    | None                                                                                          | List all PVE nodes                           |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/rrd"><code>/nodes/{node}/rrd</code></a>   | GET    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a> | Retrieve node statistics                     |

### High Availability (HA) {#high-availability}

| Endpoint                                                                                                                        | Method | Required Privilege                                                                              | Function                        |
| ------------------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------- | ------------------------------- |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources"><code>/cluster/ha/resources</code></a>             | GET    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a>   | List all HA resources           |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources"><code>/cluster/ha/resources</code></a>             | POST   | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Console</code></a> | Enable HA for a VM              |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources/{sid}"><code>/cluster/ha/resources/{sid}</code></a> | GET    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a>   | Query HA status of a VM         |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources/{sid}"><code>/cluster/ha/resources/{sid}</code></a> | PUT    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Console</code></a> | Modify HA configuration of a VM |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/ha/resources/{sid}"><code>/cluster/ha/resources/{sid}</code></a> | DELETE | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Console</code></a> | Disable HA for a VM             |

### VM Management {#vm-management}

| Endpoint                                                                                                                                                                              | Method | Required Privilege                                                                                                                                                                            | Function                           |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/config"><code>/nodes/{node}/qemu/{vmid}/config</code></a>                                             | GET    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Audit</code></a>                                                                                                  | Query VM configuration             |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/config"><code>/nodes/{node}/qemu/{vmid}/config</code></a>                                             | PUT    | `VM.Config.*`                                                                                                                                                                                 | Modify VM configuration            |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/status/current"><code>/nodes/{node}/qemu/{vmid}/status/current</code></a>                             | GET    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Audit</code></a>                                                                                                  | Query current VM status            |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/clone"><code>/nodes/{node}/qemu/{vmid}/clone</code></a>                                               | POST   | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Clone</code></a>, <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Allocate</code></a> | Clone VM or template               |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}"><code>/nodes/{node}/qemu/{vmid}</code></a>                                                           | DELETE | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Allocate</code></a>                                                                                               | Delete VM                          |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/migrate"><code>/nodes/{node}/qemu/{vmid}/migrate</code></a>                                           | POST   | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Migrate</code></a>                                                                                                | Migrate VM to another node         |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/cloudinit"><code>/nodes/{node}/qemu/{vmid}/cloudinit</code></a>                                       | PUT    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Audit</code></a>                                                                                                  | Regenerate CloudInit configuration |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces"><code>/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces</code></a> | GET    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.Monitor</code></a>                                                                                                | Read network interfaces (IPv4)     |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/tasks/{upid}/status"><code>/nodes/{node}/tasks/{upid}/status</code></a>                                           | GET    | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>Sys.Audit</code></a>                                                                                                 | Query task status                  |

### VM Control (Power Management) {#power-management}

| Endpoint                                                                                                                                           | Method | Required Privilege                                                                               | Function                                                                        |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| <a href="https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/status"><code>/nodes/{node}/qemu/{vmid}/status/{action}</code></a> | POST   | <a href="https://pve.proxmox.com/wiki/User_Management#_privileges"><code>VM.PowerMgmt</code></a> | Control VM: `start`, `stop`, `shutdown`, `reboot`, `reset`, `resume`, `suspend` |

</details>
