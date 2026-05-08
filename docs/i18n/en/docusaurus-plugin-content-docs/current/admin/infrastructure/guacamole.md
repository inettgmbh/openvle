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

Apache Guacamole enables web-based remote desktop access to virtual machines. Participants use it to access their VMs directly from the browser — without needing to install any additional software.

:::info Optional
Apache Guacamole is an optional component. Without Guacamole, OpenVLE can still be used to manage VMs and VM templates, but without remote desktop access in the browser.
:::

## Architecture {#architecture}

Apache Guacamole is an open-source software that provides access to remote resources via RDP, VNC, SSH, and other protocols through a standard web browser. The Guacamole stack consists of three components:

| Component         | Function                                                     |
| ----------------- | ------------------------------------------------------------ |
| **Guacamole Web** | Web interface and API server                                 |
| **guacd**         | Connection daemon that processes the actual remote protocols |
| **Guacamole DB**  | Database for users, connections, and configuration           |

## Communication with OpenVLE {#communication}

OpenVLE manages Guacamole connections automatically. The backend communicates with the Guacamole server via the Guacamole API and creates, updates, and deletes connections on the following events:

- **Connection created** — A new Guacamole connection is automatically created
- **VM deleted** — The associated connection is removed
- **Event started/ended** — Connections are activated or deactivated accordingly

For this, the OpenVLE backend requires a dedicated user account with administrative permissions in Guacamole.

## Requirements {#requirements}

The OpenVLE backend requires the following information to communicate with Guacamole:

| Information                     | Example                         |
| ------------------------------- | ------------------------------- |
| URL of the Guacamole server     | `https://guacamole.example.com` |
| Database type of Guacamole      | `mysql`                         |
| Username of the OpenVLE account | `OpenVLE`                       |
| Password of the OpenVLE account | _(secure password)_             |

This information is configured in `.env`. Additionally, network access from the backend server to the Guacamole server must be possible (HTTPS 443/tcp by default).

:::note Automatic management
After configuring the credentials, no further manual intervention in Guacamole is required. OpenVLE takes over the management of all connections fully automatically.
:::

## User authentication in Guacamole {#guacamole-auth}

Guacamole should ideally be connected to the same identity provider (LDAP or OIDC) as OpenVLE. The reason: OpenVLE provisions Guacamole connections for the same usernames that users have in OpenVLE. If Guacamole uses the same IdP, users can log in to the remote desktop directly with their existing credentials.

Manual user management in Guacamole is not necessary — OpenVLE automatically creates Guacamole users if they do not yet exist. Therefore, only authentication needs to be configured in Guacamole, not provisioning.

## Further reading {#further-reading}

- [Install Apache Guacamole](../install/guacamole) — Setup and installation
- [Configuration reference — Guacamole](../install/configuration#guacamole) — All available environment variables
