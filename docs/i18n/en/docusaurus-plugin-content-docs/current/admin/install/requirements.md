---
id: requirements
sidebar_label: Requirements
sidebar_position: 11
status: finished
tags:
  - installation
  - requirements
---

# Requirements {#requirements}

Running OpenVLE requires a dedicated server.

Since OpenVLE requires Proxmox VE as its hypervisor (see [Proxmox VE Integration](proxmoxve)), we recommend running OpenVLE as a virtual machine directly on the Proxmox host. This avoids the need for additional hardware, and backups as well as snapshots of the OpenVLE VM can be handled by Proxmox itself.

:::tip Separation from production VMs
Create the OpenVLE VM outside the `OpenVLE-VMs` pool configured in Proxmox so that it is not managed by OpenVLE itself.
:::

## Resources {#resources}

The required resources depend on the expected load of the OpenVLE management interface. The more users accessing it simultaneously, the more resources are needed. For getting started, we recommend the following VM specifications:

- 4 CPU cores
- 8 GB RAM
- 50 GB disk space

## Operating system {#operating-system}

Officially supported are all Linux distributions on which Docker can be officially installed. This covers the most common distributions such as Ubuntu, Debian, and Red Hat Enterprise Linux.

## Installing Docker (Compose) {#install-docker}

First, the current official version of `docker` and `docker compose` must be installed on the server.

The fastest way is the official convenience script from Docker, which automatically detects all supported distributions and installs Docker including Compose V2:

```bash
curl -fsSL https://get.docker.com | sh
```

:::caution Production Environment
The convenience script is intended for quick setup. For production environments with special requirements (e.g., custom repositories, proxy configuration, specific versions), we recommend manual installation according to the [official Docker documentation](https://docs.docker.com/engine/install/).
:::

### Verification {#verify-docker}

After installation, verify that Docker and Compose are correctly installed:

```bash
docker --version
docker compose version
```

Both commands should output a version number. Additionally, test whether Docker is functioning properly:

```bash
docker run --rm hello-world
```

## Troubleshooting {#troubleshooting}

| Problem                                | Solution                                                                                           |
| -------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `docker compose` not found             | Make sure Docker Compose V2 is installed (as a Docker plugin, not as a separate `docker-compose`). |
| Permission errors with Docker commands | Add your user to the `docker` group: `sudo usermod -aG docker $USER` and log out and back in.      |
