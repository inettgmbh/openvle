# OpenVLE

**OpenVLE** is an open, web-based platform for running IT teaching and lab environments at scale.

Course administrators design VM-based lessons, schedule them, and assign them to groups; learners spin up their own isolated environments and access them straight from the browser — anywhere, with no local software install. Under the hood, OpenVLE orchestrates **Proxmox VE** for virtualization, **Apache Guacamole** for browser-based VM access, and **Cloud-Init** + the **QEMU Guest Agent** for automated provisioning and runtime control.

End-user and administrator documentation lives at [docs.openvle.org](https://docs.openvle.org) — start there for installation guides, configuration references, and how-tos.

---

## Components

OpenVLE ships as three components in a single repository — all versioned, built, and released together under one shared version.

| Component | Stack | Purpose |
|-----------|-------|---------|
| [`backend/`](backend/README.md) | Python 3.10, FastAPI, SQLAlchemy, MariaDB / MongoDB / Redis | REST API, background workers, scheduler, Proxmox & Guacamole integration |
| [`frontend/`](frontend/README.md) | Vue 3, Vite, Pinia | Web interface for course administrators and end users |
| [`docs/`](docs/README.md) | Docusaurus 3, MDX, i18n (DE / EN / FR) | End-user and administrator documentation, published at [docs.openvle.org](https://docs.openvle.org) |

Backend and frontend together form the application stack and are deployed side-by-side. The docs site is independent and runs on its own host.

---

## Repository layout

```
openvle/
├── .mise.toml                 # Pinned dev runtimes (python, node)
├── docker-compose.yml         # Prod-style stack (backend + frontend)
├── CHANGELOG.md               # Unified changelog from v0.100.0 onward
│
├── backend/
│   ├── code/                  # Python source (pyproject.toml is the version anchor)
│   ├── tests/
│   ├── Dockerfile
│   ├── docker-compose.yml     # Standalone backend stack
│   ├── docker-compose.dev.yml # Local dev stack with profiles (moodle/smtp/phpmyadmin)
│   ├── .env.sample
│   └── README.md
│
├── frontend/
│   ├── code/                  # Vue source (package.json is the semantic-release anchor)
│   ├── static/
│   ├── Dockerfile
│   ├── docker-compose.yml     # Standalone frontend service
│   ├── env_injection.sh
│   ├── nginx.conf
│   ├── .env.sample
│   └── README.md
│
└── docs/
    ├── docs/                  # Docusaurus content (DE)
    ├── i18n/{en,fr}/          # English & French translations
    ├── src/
    ├── static/
    ├── package.json
    ├── docusaurus.config.js
    ├── Dockerfile
    ├── docker-compose.yml     # Standalone docs service
    ├── nginx.conf
    ├── .env.sample
    └── README.md
```

---

## Prerequisites

**To run the integration stack from prebuilt images:**
- **Docker** + **Docker Compose v2**
- **Proxmox VE** as hypervisor (only required to run the full system end-to-end against real VMs)

**Additionally, for local development:**
- **[mise](https://mise.jdx.dev/)** for managing Python and Node versions. The runtimes pinned in [`.mise.toml`](.mise.toml) (`python = "3.10"`, `node = "24"`) match what the production containers run on; install via `mise install` from any directory inside the repo.

---

## Quick start (integration stack from prebuilt images)

```bash
mkdir openvle && cd openvle
curl -fsSLO https://raw.githubusercontent.com/inettgmbh/openvle/main/docker-compose.yml
curl -fsSL -o .env          https://raw.githubusercontent.com/inettgmbh/openvle/main/backend/.env.sample
curl -fsSL -o frontend.env  https://raw.githubusercontent.com/inettgmbh/openvle/main/frontend/.env.sample
nano .env frontend.env              # set credentials, hosts, secrets
docker compose up
```

For the full install walkthrough — what each `.env` value means, hostnames, certificates, Proxmox/Guacamole configuration, first login — follow the admin guide: [docs.openvle.org/docs/admin/install/openvle](https://docs.openvle.org/docs/admin/install/openvle).

The root `docker-compose.yml` brings up the prod-style stack (MariaDB, MongoDB, Redis, backend, workers, scheduler, frontend) using prebuilt images from `${IMAGE_REGISTRY:-ghcr.io/inettgmbh}/openvle/{backend,frontend}`. Override `IMAGE_REGISTRY` in `.env` to pull from a different registry. Use this for integration testing or when you don't want to build from source.

`.env` is read by compose for variable interpolation **and** mounted into the backend/worker/scheduler containers as the application config. `frontend.env` is mounted into the frontend (nginx) container for runtime config injection.

The root stack does **not** include `docs` — the docs site is served separately on its own host (see [Deployment](#deployment)).

For active development on a single component, see the per-component workflows below.

---

## Component dev workflows

Each component has its own README with detailed setup steps. The condensed flow:

### Backend

```bash
cd backend
cp .env.sample .env
docker compose -f docker-compose.dev.yml up                          # core stack (db, cache, backend, workers)
docker compose -f docker-compose.dev.yml --profile phpmyadmin up     # adds phpMyAdmin (port 8888)
docker compose -f docker-compose.dev.yml --profile smtp up           # adds Fake-SMTP (1025 / 8088)
docker compose -f docker-compose.dev.yml --profile moodle up         # adds Moodle stack (port 8080)
```

Profiles can be combined: `--profile phpmyadmin --profile smtp`. The dev compose builds the backend image from source via `Dockerfile`; rebuild with `--build` after code changes. See [`backend/README.md`](backend/README.md) for tests, migrations, and API docs.

### Frontend

```bash
cd frontend/code
cp .env.sample .env
npm install
npm run dev      # vite dev server with HMR
npm run format
npm run lint
npm run test:unit
npm run build
```

Point `VITE_API_URL` at a running backend (local or testing server). See [`frontend/README.md`](frontend/README.md).

### Docs

```bash
cd docs
npm install
npm run dev          # German (default)
npm run dev:en       # English
npm run dev:fr       # French
npm run format
npm run lint
npm run build
```

See [`docs/README.md`](docs/README.md).

---

## Versioning & releases

OpenVLE uses **a single version number** for all three components. Every release tags backend, frontend, and docs with the same version and ships one shared `CHANGELOG.md` entry. Tags follow the format `v${version}` (e.g. `v1.0.0`).

Versions are computed automatically from commit history using [semantic-release](https://semantic-release.gitbook.io/), driven by [Conventional Commits](https://www.conventionalcommits.org/):

| Commit prefix | Effect |
|---------------|--------|
| `fix(scope): …` | Patch bump (e.g. `1.0.0` → `1.0.1`) |
| `feat(scope): …` | Minor bump (e.g. `1.0.0` → `1.1.0`) |
| `feat(scope)!: …` or `BREAKING CHANGE:` in body | Major bump |
| `chore`, `docs`, `style`, `refactor`, `test`, `ci` | No release |

Use the component name as the scope (`feat(backend): …`, `fix(frontend): …`) for component-touching changes, or a cross-cutting area (`feat(compose): …`, `feat(ci): …`) for repo-wide work.

---

## CI/CD

CI/CD runs on the core team's internal GitLab and is not part of the public mirror. Public-facing GitHub Actions workflows may follow at a later point.

---

## Deployment

Each release publishes container images to `ghcr.io/inettgmbh/openvle/{backend,frontend,docs}` with tags `:latest`, `:v${VERSION}`, `:v${MAJOR}`, and `:v${MAJOR.MINOR}`.

---

## Contributing

Bug reports, feature requests, and code contributions are welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for setup, code style, commit conventions, and how to open a pull request.

---

## License

OpenVLE is licensed under the [GNU Affero General Public License v3.0](https://www.gnu.org/licenses/agpl-3.0.html). The AGPL grants you the right to use, modify, and distribute the software, with provisions covering modified versions, source availability, and network use.

The full license text, including any applicable third-party notices, is in [`LICENSE`](LICENSE) at the repo root.
