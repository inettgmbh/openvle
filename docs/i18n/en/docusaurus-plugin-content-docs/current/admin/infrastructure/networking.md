---
id: networking
sidebar_label: Networking & Docker
sidebar_position: 25
status: finished
tags:
  - infrastructure
  - networking
  - docker
---

# Networking & Docker {#networking}

All OpenVLE services run in Docker containers and communicate via an internal Docker network. Only a few ports are published externally. A reverse proxy in front is recommended for production use but is not strictly required.

## Docker Network {#docker-network}

The Docker Compose stack automatically creates an internal network (`openvle-internal`). All containers are connected via this network and can reach each other using their service names (e.g., `backend`, `mariadb`, `redis`).

:::note DNS Resolution
Docker Compose provides internal DNS resolution: containers can address other containers using the service name as hostname. This is why the environment variables use, for example, `MARIADB_HOST = "db"` instead of an IP address.
:::

## Exposed Ports {#exposed-ports}

In the default `docker-compose.yml`, only two ports are published externally:

| Service    | Container Port | Host Port | Purpose                      |
| ---------- | -------------- | --------- | ---------------------------- |
| `frontend` | 80             | 80        | Web interface (Vue.js/Nginx) |
| `backend`  | 80             | 8000      | REST API (FastAPI)           |

Both services must be reachable from the end user's browser: the frontend serves the web interface, and the browser communicates directly with the backend at runtime (API requests).

All other services (MariaDB, MongoDB, Redis, Worker, Scheduler) do **not publish any ports** and are only accessible internally.

:::note Reverse Proxy (recommended)
When using a [Reverse Proxy](../install/reverse-proxy), the port publications should be restricted to `127.0.0.1`, since external access then goes through the proxy:

```yaml
ports:
  - 127.0.0.1:80:80
  - 127.0.0.1:8000:8000
```

:::

## Communication Paths {#communication-paths}

### External Access {#external-access}

**With Reverse Proxy (recommended):**

```
Browser → Reverse Proxy → Frontend (Port 80)
Browser → Reverse Proxy → Backend (Port 8000)
```

**Without Reverse Proxy:**

```
Browser → Frontend (Port 80)
Browser → Backend (Port 8000)
```

A reverse proxy is optional but recommended for production use -- it handles SSL termination, routing, and optionally load balancing. See [Reverse Proxy](../install/reverse-proxy) for setup instructions.

### Internal Communication {#internal-communication}

| From        | To        | Purpose                               |
| ----------- | --------- | ------------------------------------- |
| `backend`   | `mariadb` | Reading/writing core entities         |
| `backend`   | `mongodb` | Writing activities and logs           |
| `backend`   | `redis`   | Enqueuing background tasks            |
| `worker`    | `mariadb` | Reading/writing during task execution |
| `worker`    | `redis`   | Fetching jobs from the queue          |
| `scheduler` | `mariadb` | Fetching jobs from the database       |
| `scheduler` | `redis`   | Enqueuing periodic tasks              |

### External Systems {#external-systems}

OpenVLE communicates with the following external systems:

| System                                         | Direction                  | Protocol          | Purpose                                                       |
| ---------------------------------------------- | -------------------------- | ----------------- | ------------------------------------------------------------- |
| **Proxmox VE**                                 | Backend/Worker → Proxmox   | HTTPS (8006/tcp)  | VM management via Proxmox API                                 |
| **SMTP Server**                                | Backend/Worker → SMTP      | SSL/TLS (465/tcp) | Email delivery                                                |
| **Apache Guacamole** _(optional, recommended)_ | Backend/Worker → Guacamole | HTTPS (443/tcp)   | Connection management via Guacamole API                       |
| **Moodle** _(optional)_                        | Backend/Worker → Moodle    | HTTPS (443/tcp)   | Course and participant management via Moodle Web Services API |
| **LDAP Server** _(optional)_                   | Backend/Worker → LDAP      | LDAP(S) (389/636) | User authentication                                           |
| **OIDC Provider** _(optional)_                 | Backend → OIDC             | HTTPS (443/tcp)   | Single Sign-On                                                |

:::info Firewall Rules
The OpenVLE server must be able to establish outbound connections to the external systems listed above. Make sure the corresponding ports are allowed in the firewall.
:::
