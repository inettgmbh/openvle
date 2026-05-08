---
id: guacamole
sidebar_label: Apache Guacamole Integration
sidebar_position: 30
status: finished
tags:
  - installation
  - guacamole
---

# Apache Guacamole — Integration {#guacamole-integration}

Apache Guacamole provides web-based remote desktop access (RDP, VNC, SSH) without client software. OpenVLE uses Guacamole to give users access to virtual machines directly in the browser.

Guacamole runs as a separate service and is **not** part of the standard OpenVLE Docker stack. For the installation and operation of Guacamole, we refer to the official documentation.

:::info Optional Component
Guacamole is optional but recommended. Without Guacamole, OpenVLE can still be used to manage VMs and VM templates — however, web-based remote desktop access will not be available.
:::

## Prerequisites {#prerequisites}

- Separate server or Docker host for Guacamole
- Network access from the OpenVLE backend to the Guacamole server (default: port 8080, or 443 for HTTPS)
- A MariaDB/MySQL database for Guacamole

:::caution Separate Database
Guacamole requires its **own** database — do not use the OpenVLE MariaDB instance.
:::

## Installation {#installation}

The official Apache Guacamole Docker documentation describes the setup in detail:

- [Apache Guacamole Docker Installation](https://guacamole.apache.org/doc/gug/guacamole-docker.html)

A typical Guacamole installation consists of three containers:

| Container      | Function                                                  |
| -------------- | --------------------------------------------------------- |
| `guacd`        | Connection Proxy — manages the remote desktop connections |
| `guacamole`    | Web frontend — provides the user interface                |
| `guacamole-db` | Database — stores users, connections, and configuration   |

## Create OpenVLE User in Guacamole {#create-openvle-user}

OpenVLE requires a dedicated admin account in Guacamole to automatically manage connections. Create this user via the Guacamole web interface:

1. Log in as an administrator to the Guacamole web interface
2. Navigate to **Settings -> Users -> New User**
3. Create a user with administrator privileges
4. Take note of the username and password — these will be needed in the next step

## Configure OpenVLE Backend {#configure-backend}

Enter the Guacamole connection details in the backend's `.env` file. The complete reference of all environment variables can be found under [Configuration](configuration?stack=backend).

| Variable                              | Description                                  | Example                        |
| ------------------------------------- | -------------------------------------------- | ------------------------------ |
| `GUACAMOLE_URL`                       | URL of the Guacamole server                  | `http://guacamole-server:8080` |
| `GUACAMOLE_DB`                        | Guacamole database type                      | `mysql`                        |
| `GUACAMOLE_USER`                      | Username of the OpenVLE account              | `OpenVLE`                      |
| `GUACAMOLE_PASSWORD`                  | Password of the OpenVLE account              | `secure-password`              |
| `GUACAMOLE_CONNECTIONS_PREFIX`        | Prefix for automatically created connections | `openvle-`                     |
| `GUACAMOLE_CONNECTIONS_PREFIX_EVENTS` | Also use prefix for event connections        | `True`                         |

## Verification {#verification}

1. Open the **Guacamole web interface** and verify that the login works
2. Check the **OpenVLE backend logs** for a successful Guacamole connection:
   ```bash
   docker logs openvle-backend 2>&1 | grep -i guacamole
   ```
3. Create a **test VM with a connection** in OpenVLE and verify that the Guacamole connection is automatically created

## Troubleshooting {#troubleshooting}

| Problem                                   | Solution                                                                                                                                                              |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend cannot reach Guacamole            | Check whether `GUACAMOLE_URL` is correctly set in the `.env` file and that network access between the backend and Guacamole exists.                                   |
| Login to Guacamole WebUI fails            | Check whether the initial database setup was performed correctly.                                                                                                     |
| Connections are not automatically created | Check the backend logs (`docker logs openvle-backend`) for Guacamole-related error messages and make sure the OpenVLE user has administrator privileges in Guacamole. |

## Further Reading {#further-reading}

- [Infrastructure: Guacamole](/docs/admin/infrastructure/guacamole) — Architecture and network requirements
- [Usage: Guacamole](/docs/usage/guacamole/) — Guide for end users
