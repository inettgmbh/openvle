---
id: openvle
sidebar_label: OpenVLE
sidebar_position: 40
status: finished
tags:
  - installation
  - docker
  - backend
  - frontend
---

# OpenVLE {#openvle}

OpenVLE is operated as a Docker Compose stack and includes all required services in a single repository. A single `docker compose up -d` starts the entire application.

## Architecture {#architecture}

The Docker Compose stack consists of the following services:

| Service     | Function                                                                       |
| ----------- | ------------------------------------------------------------------------------ |
| `backend`   | Python/FastAPI — API server, business logic                                    |
| `frontend`  | Vue.js/Nginx — Web interface                                                   |
| `worker`    | RQ Worker — asynchronous background tasks (VM operations, email sending, etc.) |
| `scheduler` | RQ Scheduler — periodic tasks (node info updates, etc.)                        |
| `mariadb`   | MariaDB — relational database for core entities                                |
| `mongodb`   | MongoDB — document database for activities and logs                            |
| `redis`     | Redis — task queue and cache for worker/scheduler                              |

## Prerequisites {#prerequisites}

- [Docker and Docker Compose](requirements) installed
- [Proxmox VE](proxmoxve) set up (required for VM management)
- An SMTP server for sending emails (have credentials ready)
- Optional: [Apache Guacamole](guacamole) for remote desktop access

## Installation {#installation}

### Download repository {#download}

Download the `docker-compose.yml` and `.env.sample` files from the official repository:

```bash
mkdir openvle && cd openvle
curl -fsSLO https://raw.githubusercontent.com/inettgmbh/openvle/main/docker-compose.yml
curl -fsSL -o .env         https://raw.githubusercontent.com/inettgmbh/openvle/main/backend/.env.sample
curl -fsSL -o frontend.env https://raw.githubusercontent.com/inettgmbh/openvle/main/frontend/.env.sample
```

### Pull Docker images {#pull}

```bash
docker compose pull
```

### Configuration {#configuration}

OpenVLE uses two configuration files at root level: `.env` for backend, workers, scheduler, and Compose variable interpolation, and `frontend.env` for the frontend runtime configuration.

#### Backend (`.env`) {#configure-backend}

First, generate secure, random passwords and secrets for all security-relevant variables:

```bash
sed -i \
  -e "s|AUTH_SECRET = \"\"|AUTH_SECRET = \"$(openssl rand -hex 32)\"|" \
  -e "s|SESSION_SECRET_TOKEN = \"\"|SESSION_SECRET_TOKEN = \"$(openssl rand -hex 32)\"|" \
  -e "s|MARIADB_PASSWORD = \"project\"|MARIADB_PASSWORD = \"$(openssl rand -hex 16)\"|" \
  -e "s|MARIADB_ROOT_PASSWORD = \"root\"|MARIADB_ROOT_PASSWORD = \"$(openssl rand -hex 16)\"|" \
  -e "s|MONGODB_PASSWORD = \"project\"|MONGODB_PASSWORD = \"$(openssl rand -hex 16)\"|" \
  -e "s|REDIS_PASSWORD = \"password\"|REDIS_PASSWORD = \"$(openssl rand -hex 16)\"|" \
  .env
```

:::caution
This command replaces the default passwords once with random values. Run it **only once** — running it again would have no effect since the already-set values would no longer match the defaults. Back up the generated `.env` afterwards, as the passwords cannot be recovered.

If you prefer not to use the `sed` command, you **must** manually set the following variables to secure values: `AUTH_SECRET`, `SESSION_SECRET_TOKEN`, `MARIADB_PASSWORD`, `MARIADB_ROOT_PASSWORD`, `MONGODB_PASSWORD`, `REDIS_PASSWORD`. The default values in the `.env.sample` are insecure and must not be used in production.
:::

:::note MARIADB_ROOT_PASSWORD
`MARIADB_ROOT_PASSWORD` is only needed during the **initial start** — MariaDB adopts the password during its first initialization and stores it in the database. After the first successful start, you can remove the variable from `.env` and instead store the password in a secure location (e.g., a password manager) in case you need it for maintenance or troubleshooting.
:::

Next, edit `.env` and set the remaining environment-specific variables:

**CORS**

| Variable       | Description                                             | Example                           |
| -------------- | ------------------------------------------------------- | --------------------------------- |
| `CORS_ORIGINS` | Allowed origins for CORS requests (URL of the frontend) | `["https://openvle.example.com"]` |

**Proxmox VE** — Credentials from the [Proxmox VE Integration](proxmoxve)

| Variable          | Description                             | Example                                  |
| ----------------- | --------------------------------------- | ---------------------------------------- |
| `PVE_HOSTNAME`    | Hostname and port of the Proxmox server | `"proxmox.example.com:8006"`             |
| `PVE_USER`        | Proxmox user                            | `"OpenVLE@pve"`                          |
| `PVE_TOKEN_NAME`  | Name of the API token                   | `"prod01"`                               |
| `PVE_TOKEN_VALUE` | Secret value of the API token           | `"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"` |
| `PVE_FQDN`        | FQDN of the Proxmox server              | `"proxmox.example.com:8006"`             |
| `PVE_VMS_POOL`    | Proxmox pool for managed VMs            | `"OpenVLE-VMs"`                          |
| `PVE_VM_SUBNET`   | Subnet for VMs                          | `"10.1.1.0/24"`                          |

**Email / SMTP**

| Variable         | Description         | Example                 |
| ---------------- | ------------------- | ----------------------- |
| `SMTP_HOST`      | SMTP server         | `"mail.example.com"`    |
| `SMTP_PORT`      | SMTP port           | `465`                   |
| `SMTP_METHOD`    | Connection method   | `"ssl"`                 |
| `SMTP_USERNAME`  | SMTP username       | `"openvle@example.com"` |
| `SMTP_PASSWORD`  | SMTP password       | `"smtp-password"`       |
| `SMTP_FROM_MAIL` | Sender address      | `"openvle@example.com"` |
| `SMTP_FROM_NAME` | Sender display name | `"OpenVLE"`             |

:::info
The variables must be enclosed in **quotation marks (`" "`)**, otherwise parsing errors will occur at startup.
:::

:::note Full reference
The table above shows only the required variables. For optional settings (Guacamole, LDAP, OIDC, Moodle, Sentry, etc.) see the [Configuration reference](configuration).
:::

#### Frontend (`frontend.env`) {#configure-frontend}

For the frontend, you only need to set the backend URL:

```bash
VITE_BACKEND_URL='https://openvle.example.com/v1'
```

Additional optional frontend variables (e.g., Sentry) can be found in the [Configuration reference](configuration?stack=frontend).

### Start containers {#start}

```bash
docker compose up -d
```

Docker automatically creates all necessary directories, initializes the databases, and starts all services.

:::caution First start
On the first start, the backend automatically runs the database migration. This may take a few minutes. Wait until all containers reach the `healthy` status before proceeding.
:::

### Network and ports {#ports}

In the default `docker-compose.yml`, only two ports are exposed externally:

| Service    | Port | Binding        |
| ---------- | ---- | -------------- |
| `frontend` | 80   | `0.0.0.0:80`   |
| `backend`  | 8000 | `0.0.0.0:8000` |

All other containers (MariaDB, MongoDB, Redis, Worker, Scheduler) communicate exclusively internally via the Docker network and do not expose any ports — and it should stay that way.

:::note Using a reverse proxy
When a [reverse proxy](reverse-proxy) is used (recommended), the port exposures for frontend and backend in the `docker-compose.yml` can be removed or restricted to `127.0.0.1`, since all external access is then handled centrally through the reverse proxy. Example:

```yaml
ports:
  - 127.0.0.1:80:80 # only locally accessible
  - 127.0.0.1:8000:8000
```

:::

### Default administrator {#default-admin}

After the first successful start, a default administrator account is automatically created:

|              |           |
| ------------ | --------- |
| **Username** | `openvle` |
| **Password** | `openvle` |

:::caution Change password immediately
Change the default administrator password **immediately** after the first login. Then create a personal account for each administrator and disable or delete the default account once the individual accounts are set up.
:::

## Verification {#verification}

### Check container status {#verify-containers}

```bash
docker ps -a
```

All 7 containers should have the status `Running (healthy)`.

### Check logs {#verify-logs}

```bash
docker logs openvle-backend 2>&1 | head -50
```

The logs should show no error messages and confirm a successful database connection.

### Test API access {#verify-api}

Retrieve the system settings via the API:

```bash
curl -s https://openvle.example.com/v1/system/settings | head -20
```

A JSON response with the current settings confirms that the backend and reverse proxy are correctly configured. An empty or erroneous response indicates a configuration problem.

### Check web interface {#verify-frontend}

Open `https://openvle.example.com` in your browser. The login page should be displayed.

## Troubleshooting {#troubleshooting}

| Problem                     | Solution                                                                                                               |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Container does not start    | Check the logs using `docker logs <container-name>`. More information at [Logs](../operations/logs).                   |
| Database error on startup   | Make sure the MariaDB and MongoDB variables in `.env` are set correctly. See [Configuration reference](configuration). |
| Health check fails          | Wait a few minutes — the initial database migration may take longer on the first start.                                |
| Web interface not reachable | Make sure the frontend container is running and the [reverse proxy](reverse-proxy) is correctly configured.            |
| API calls fail              | Check `CORS_ORIGINS` in `.env` — it must contain the URL of the frontend.                                              |
| Email sending does not work | Check the SMTP variables in `.env` and test the connection to the SMTP server.                                         |
| Proxmox connection fails    | Check `PVE_HOSTNAME`, `PVE_USER`, `PVE_TOKEN_NAME`, and `PVE_TOKEN_VALUE`. See [Proxmox VE Integration](proxmoxve).    |
