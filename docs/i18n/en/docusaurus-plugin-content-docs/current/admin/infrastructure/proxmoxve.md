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

Proxmox VE is the hypervisor on which OpenVLE manages virtual machines and VM templates. OpenVLE communicates exclusively via the Proxmox REST API with the cluster -- there is no direct access to the Proxmox hosts.

:::caution Required Component
Proxmox VE is a core dependency of OpenVLE. Without correct Proxmox configuration, the application will start, but all actions involving VMs and VM templates will fail.
:::

## Connection {#connection}

OpenVLE connects to the Proxmox API via the Python library `proxmoxer`. Authentication is performed using an **API token** (not a password):

| Parameter         | Description               | Example                    |
| ----------------- | ------------------------- | -------------------------- |
| `PVE_HOSTNAME`    | API endpoint (Host:Port)  | `proxmox.example.com:8006` |
| `PVE_USER`        | Proxmox user (User@Realm) | `OpenVLE@pve`              |
| `PVE_TOKEN_NAME`  | Token ID                  | `prod01`                   |
| `PVE_TOKEN_VALUE` | Token secret              | `xxxxxxxx-xxxx-...`        |
| `PVE_VERIFY_SSL`  | Verify SSL certificate    | `True`                     |

## Pool Concept {#pools}

All VMs and VM templates managed by OpenVLE are organized in a dedicated Proxmox pool (configured via `PVE_VMS_POOL`, default: `OpenVLE-VMs`). The Proxmox permissions of the OpenVLE API token are restricted to this pool -- OpenVLE therefore **cannot see, control, or delete any VMs outside the pool**. Other workloads on the same Proxmox cluster remain fully isolated and untouched.

By combining pool and privilege separation, multiple OpenVLE instances (e.g., production, staging) can be operated on the same Proxmox cluster: each instance receives its own API token with access to its own pool, without being able to see or affect the other instance.

## VM Lifecycle {#vm-lifecycle}

### VM Templates {#templates}

VM templates are stored directly in Proxmox as QEMU templates. OpenVLE periodically synchronizes their status and metadata (name, CPU, RAM, node) into its own database. Templates can be created, updated, and deleted through OpenVLE.

### VM Operations {#vm-operations}

When deploying an event or on manual request, OpenVLE creates VMs by cloning templates:

| Operation          | Description                                                                                                     |
| ------------------ | --------------------------------------------------------------------------------------------------------------- |
| **Clone**          | Creates a new VM from a VM template (full clone or linked clone, configurable via `PVE_VMS_FULL_CLONE_DEFAULT`) |
| **Start / Stop**   | Starts or stops a VM on Proxmox                                                                                 |
| **Shutdown**       | Gracefully shuts down a VM via the QEMU Guest Agent                                                             |
| **Restart**        | Restarts a running VM                                                                                           |
| **Reset**          | Hard reset of a VM                                                                                              |
| **Pause / Resume** | Pauses a VM or resumes it                                                                                       |
| **Migrate**        | Moves a VM to another Proxmox node (online or offline)                                                          |
| **Delete**         | Removes a VM from Proxmox and cleans up the database                                                            |

## Node Management {#node-management}

OpenVLE is fully multi-node capable and works with any number of Proxmox nodes:

- **Node Discovery** -- The periodic sync detects all nodes in the cluster and stores their status
- **Automatic Node Selection** -- When cloning a VM, OpenVLE automatically selects the node with the most available CPU capacity
- **Node Tracking** -- For each VM and VM template, the node it resides on is stored. During migrations, this is automatically updated

## Networking and IP Assignment {#networking}

OpenVLE supports two methods for network configuration of VMs.

:::note Without Apache Guacamole
If OpenVLE is operated without Apache Guacamole -- e.g., only for managing and deploying VMs without web-based remote desktop access -- the network information of VMs is not strictly required by OpenVLE. In this case, IP addresses are still read and displayed but are not necessary for core functionality.
:::

### DHCP (Default, recommended) {#dhcp}

In standard operation (`PVE_CI_ENABLED=False`), OpenVLE expects an external DHCP server to be active in the VM subnet/VLAN, dynamically assigning IP addresses to VMs. The VM templates only need to be configured for DHCP.

After a VM starts, OpenVLE reads the DHCP-assigned IPv4 address from the VM via the QEMU Guest Agent and stores it in the database. This is the recommended default approach.

### Cloud-Init (experimental) {#cloud-init-networking}

When Cloud-Init is enabled (`PVE_CI_ENABLED=True`), OpenVLE handles IP assignment itself and writes a static IP configuration directly into the VM:

1. The subnet is formed from `PVE_VMS_NETWORK` and `PVE_VMS_SUBNET`
2. Already assigned IPs (from the database) and excluded IPs (`PVE_VMS_EXCLUDED_IPS`) are skipped
3. The first available IP is assigned to the new VM via Cloud-Init (including gateway and DNS)

:::caution Experimental
Cloud-Init-based IP assignment is currently an experimental feature. For more details and all Cloud-Init variables, see [Cloud-Init](#cloud-init) and the [Configuration Reference -- Proxmox VE](../install/configuration#proxmox).
:::

### QEMU Guest Agent {#guest-agent}

OpenVLE requires the QEMU Guest Agent to be installed in the VMs. It is needed for the following functions:

- **IP Detection** -- Reading the actual IPv4 address of a running VM (for both DHCP and Cloud-Init)
- **Graceful Shutdown** -- Clean shutdown via the agent

:::note Proxmox Permission
Starting with Proxmox VE 9, the `VM.GuestAudit` privilege is required on the pool for OpenVLE to execute guest agent queries and commands. For PVE < 9, this privilege does not exist and can be omitted. For setup details, see [Proxmox VE -- Integration](../install/proxmoxve#create-roles).
:::

## Periodic Sync {#periodic-sync}

The `worker-periodic` worker synchronizes the status between Proxmox and OpenVLE every `WORKER_PVE_PERIODIC_INTERVAL` seconds (default: 60):

1. **Fetch Cluster Resources** -- Complete list of all VMs, templates, and nodes from Proxmox
2. **Update MongoDB** -- Snapshot of cluster resources for fast access
3. **Update MariaDB** -- Status updates for all known VMs and templates (e.g., `cloning` → `running`, node change during migration)
4. **Create Changelog** -- All status changes are logged

VMs in transitional states (`starting`, `deleting`, `stopping`) are skipped during sync to avoid conflicts with ongoing operations.

## Optional Features {#optional-features}

### Cloud-Init (experimental) {#cloud-init}

When Cloud-Init is enabled (`PVE_CI_ENABLED=True`), OpenVLE additionally configures new VMs beyond [IP assignment](#cloud-init-networking) with:

- Username and password (`PVE_VMS_CIUSER`, `PVE_VMS_CIPASSWORD`)
- Optional package upgrade on first boot (`PVE_VMS_CIUPGRADE`)

All Cloud-Init variables can be found in the [Configuration Reference -- Proxmox VE](../install/configuration#proxmox).

### SMBIOS Metadata {#smbios}

When `PVE_VMS_SMBIOS_METADATA` is enabled (default: `True`), OpenVLE writes metadata from the application into the SMBIOS information (Type 1) of the VM:

| SMBIOS Field   | Content         |
| -------------- | --------------- |
| `manufacturer` | Project name    |
| `product`      | VM name         |
| `version`      | Template ID     |
| `serial`       | OpenVLE VM UUID |
| `family`       | Event slug      |

This metadata is readable within the guest operating system (e.g., via `dmidecode` on Linux or WMI on Windows) and enables you to run custom automations within the VMs. Scripts inside the VM can detect at runtime which event and environment they belong to, and based on that, automatically adjust configurations, start services, or synchronize data -- without needing to establish a direct API connection to OpenVLE.

### High Availability {#high-availability}

VMs from events are added to the Proxmox HA configuration by default and thus automatically benefit from cluster high availability: if a node fails, the VMs are automatically restarted on another node. OpenVLE manages the HA configuration entirely -- VMs are added during deployment and removed during archival.

## Further Information {#further-reading}

- [Configure Proxmox VE Integration](../install/proxmoxve) -- Setup of user, token, roles, and permissions
- [Configuration Reference -- Proxmox VE](../install/configuration#proxmox) -- All Proxmox environment variables
- [Task System](task-system) -- Queues and workers for VM operations
