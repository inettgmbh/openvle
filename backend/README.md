# OpenVLE Backend

REST API, background workers, and scheduler for OpenVLE — Python 3.10, FastAPI, SQLAlchemy, MariaDB / MongoDB / Redis. Integrates with Proxmox VE, Apache Guacamole, Cloud-Init, and the QEMU Guest Agent.

For an overview of the whole project, see the [root README](../README.md). For installation guides, configuration references, and admin/usage how-tos, see [docs.openvle.org](https://docs.openvle.org).

## Layout

```
backend/
├── code/                # Python source (pyproject.toml is the version anchor)
│   ├── main.py          # FastAPI entrypoint
│   ├── routes/          # API routes
│   ├── controllers/     # Business logic
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── migrations/      # Alembic migrations
│   ├── pve/             # Proxmox integration
│   ├── fixtures/        # Seed-data fixtures
│   └── scripts/         # CLI scripts (seed_fixtures, ...)
├── tests/               # unit / integration / e2e
├── Dockerfile           # Production image
├── docker-compose.yml   # Standalone backend stack
├── docker-compose.dev.yml # Local dev stack with profiles
└── .env.sample
```

## Development

The dev compose file builds the backend from source and starts the supporting databases (MariaDB, MongoDB, Redis) plus backend, workers, and scheduler.

```bash
cd backend
cp .env.sample .env
docker compose -f docker-compose.dev.yml up                          # core stack
docker compose -f docker-compose.dev.yml --profile phpmyadmin up     # + phpMyAdmin (port 8888)
docker compose -f docker-compose.dev.yml --profile smtp up           # + Fake-SMTP (1025 / 8088)
docker compose -f docker-compose.dev.yml --profile moodle up         # + Moodle stack (port 8080)
```

Profiles can be combined: `--profile phpmyadmin --profile smtp`. Profiles are opt-in — without `--profile`, only the core stack starts. Rebuild with `--build` after code changes.

For native Python development (no Docker), `cd backend/code`, install with `pip install -r requirements.txt` (a venv is recommended), point `.env` at running databases, and run `uvicorn main:app --reload`.

### Initial login

On a fresh database, Alembic migrations create the schema and insert seed data, including a default admin:

- **Username:** `openvle`
- **Password:** `openvle`

Change the password after first login.

### API documentation (Swagger)

API documentation is **disabled by default**. Set `DOCS_ENABLED=true` in `.env` to expose:

- `http://localhost:8000/docs` — Swagger UI
- `http://localhost:8000/redoc` — ReDoc
- `http://localhost:8000/openapi.json` — raw OpenAPI schema

With `DOCS_ENABLED=false` (the default) all three return 404. Keep it off in production.

## Tests

Test suite lives in `backend/tests/` and covers three levels:

| Category    | Directory            | Description                                              |
|-------------|----------------------|----------------------------------------------------------|
| Unit        | `tests/unit/`        | Individual functions/classes in isolation                |
| Integration | `tests/integration/` | Single API endpoints (route → controller → DB)           |
| E2E         | `tests/e2e/`         | Multi-step business workflows across multiple endpoints  |

Tests automatically start a MariaDB testcontainer — Docker must be running. To target an external database instead:

```bash
MARIADB_TEST_URL="mysql+pymysql://user:pass@host:3306/testdb" pytest tests/
```

```bash
pytest tests/                   # all tests
pytest tests/unit/              # unit only
pytest tests/integration/
pytest tests/e2e/
```

For test infrastructure, fixtures, and factories, see [`tests/README.md`](tests/README.md).

## Seed fixtures

To populate the database with realistic demo data (users, courses, events, VMs, …):

```bash
cd backend/code
python -m scripts.seed_fixtures -p demo
```

| Profile   | Description                              |
|-----------|------------------------------------------|
| `testing` | Minimal data for CI/integration tests    |
| `staging` | Moderate data for staging/QA             |
| `demo`    | Realistic data for demos (~750 users)    |

```bash
python -m scripts.seed_fixtures -p demo --purge       # delete & re-seed
python -m scripts.seed_fixtures -p demo --purge-only  # delete only
python -m scripts.seed_fixtures -p testing --dry-run  # no commit
```

Fixture data is idempotent (safe to re-run) and removable via `--purge` without touching seed data. Set `SEED_FIXTURES_PROFILE` in the container env to seed automatically on startup.

## Database migrations

Schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/). Migration files live in `code/migrations/versions/`.

- **Container startup:** the entrypoint (`code/scripts/entrypoint.sh`) runs `python migrate.py` before any service starts. MariaDB advisory locks ensure only one container migrates at a time; the others wait.
- **Fresh database:** `alembic upgrade head` creates all tables (baseline migration) and inserts seed data (system user, default admin, roles, vendors, apps, OS, languages, event statuses, permissions, mail actions/templates, settings).
- **Existing database (first Alembic adoption):** `migrate.py` detects an existing schema without `sys_alembic_version` and runs `alembic stamp head` to mark it current without re-running migrations.
- **Subsequent deployments:** `alembic upgrade head` applies only pending migrations.

Common commands (run from `backend/code/`):

```bash
alembic upgrade head           # apply all pending migrations
alembic check                  # exit non-zero if models drifted from DB
alembic current                # show current revision
alembic history                # show migration history
alembic downgrade -1           # one revision back
alembic downgrade base         # back to empty
```

Creating a new migration:

```bash
# 1. Edit models in code/models/
# 2. Generate migration
alembic revision --autogenerate -m "short description"
# 3. Review the generated file in code/migrations/versions/
#    autogenerate is not perfect — check data migrations and custom indexes
# 4. Test
alembic upgrade head && alembic downgrade -1 && alembic upgrade head
```

The version-tracking table is named `sys_alembic_version` (configured in `alembic.ini` and `migrations/env.py`).

## Production image

Published per release at `${IMAGE_REGISTRY:-ghcr.io/inettgmbh}/openvle/backend:v${VERSION}`. The standalone backend stack:

```bash
cd backend
cp .env.sample .env
docker compose up
```

## Logging

The backend writes structured logs to MongoDB. Query them via the MongoDB CLI or any client.

## Versioning, contributing, license

See the [root README](../README.md) for versioning, [`CONTRIBUTING.md`](../CONTRIBUTING.md) for contribution guidelines, and [`LICENSE`](../LICENSE) for the AGPL v3.0 license.
