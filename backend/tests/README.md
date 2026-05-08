# Tests

## Overview

| Category    | Directory            | Description                                             |
| ----------- | -------------------- | ------------------------------------------------------- |
| Unit        | `tests/unit/`        | Individual functions/classes in isolation               |
| Integration | `tests/integration/` | Single API endpoints (Route → Controller → DB)          |
| E2E         | `tests/e2e/`         | Multi-step business workflows across multiple endpoints |

---

## Directory Structure

```bash
tests/
├── conftest.py                     # Root fixtures: DB session, system user, mocks
├── factories/                      # factory-boy factories
├── helpers/                        # Test utilities / mocks
├── unit/                           # Unit tests
│   ├── controllers/                # CRUDBase + domain controllers
│   ├── core/                       # Auth, config, workers, mail, etc.
│   ├── schemas/                    # Pydantic schema validation
│   ├── middlewares/                # Auth, logging, i18n, language
│   └── pve/                        # Proxmox cluster, VMs, templates
├── integration/                    # Integration tests
│   ├── conftest.py                 # ASGIClient, client fixture, auth_headers
│   └── routes/                     # One test file per API endpoint
└── e2e/                            # End-to-end workflow tests
```

---

## Running Tests

```bash
# All tests
pytest tests/

# Coverage
pytest tests/ --cov=./code --cov-report=term-missing

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e/

# Single file
pytest tests/e2e/test_event_lifecycle.py -v

# Single test
pytest tests/unit/controllers/test_events.py::TestCRUDEventActionsStart -v
```

### Prerequisites

```bash
# Install test dependencies (from code/)
pip install --group test
```

**Docker must be running** — tests automatically start a MariaDB testcontainer via `testcontainers`.

Alternatively, an external database can be provided via the `MARIADB_TEST_URL` environment variable (for CI):

```bash
MARIADB_TEST_URL="mysql+pymysql://user:pass@host:3306/testdb" pytest tests/
```

---

## Test Infrastructure

### Database Isolation (SAVEPOINT)

Each test runs inside a nested transaction (SAVEPOINT). After the test, an automatic rollback is performed — the database is clean after every test without truncation or rebuild.

```
Connection.begin()              ← Outer transaction (per test)
  └─ Session.begin_nested()     ← SAVEPOINT (app code can call commit())
       └─ Controller: db.commit()  → SAVEPOINT released
       └─ Listener: begin_nested() → New SAVEPOINT started
  └─ Teardown: transaction.rollback() → Everything rolled back
```

This allows application code to call `db.commit()` normally without breaking test isolation.

### Stub Modules

Three modules are replaced with stubs before any app imports to prevent side effects during module loading:

| Module         | Stub                   | Reason                           |
| -------------- | ---------------------- | -------------------------------- |
| `core.mariadb` | `SessionLocal = None`  | Prevents DB connection on import |
| `core.redis`   | `FakeQueue`, `FakeJob` | No Redis connection needed       |
| `core.mongodb` | `mongodb = None`       | No MongoDB connection needed     |

### Mock Services

External services are fully mocked:

| Service    | Mock Class            | File                        |
| ---------- | --------------------- | --------------------------- |
| Proxmox VE | `MockProxmoxCluster`  | `helpers/mock_proxmox.py`   |
| Guacamole  | `MockGuacamoleClient` | `helpers/mock_guacamole.py` |
| LDAP       | `MockLDAPConnection`  | `helpers/mock_ldap.py`      |
| SMTP       | `MockSMTP`            | `helpers/mock_smtp.py`      |

---

## Key Fixtures

### Root Level (`tests/conftest.py`)

| Fixture                                        | Scope    | Description                                    |
| ---------------------------------------------- | -------- | ---------------------------------------------- |
| `mariadb_container`                            | session  | MariaDB testcontainer (or external DB via ENV) |
| `test_engine`                                  | session  | SQLAlchemy engine with connection pool         |
| `db_session`                                   | function | SAVEPOINT-isolated session per test            |
| `system_user`                                  | function | System user (UUID: `1db3d8ac-...`)             |
| `active_user`                                  | function | Active test user                               |
| `event_statuses`                               | function | All 7 event statuses                           |
| `role_admin` / `role_teacher` / `role_student` | function | Role fixtures                                  |
| `mock_permission_allow`                        | function | Patches `PermissionChecker` → always allows    |
| `mock_redis_queues`                            | function | Mocks all 6 Redis queues + 2 schedulers        |

### Integration (`tests/integration/conftest.py`)

| Fixture                | Description                                    |
| ---------------------- | ---------------------------------------------- |
| `client`               | FastAPI test client with full middleware stack |
| `auth_headers`         | JWT bearer token for `active_user`             |
| `expired_auth_headers` | Expired JWT for auth tests                     |
| `admin_user`           | User with `admin_full` role + all permissions  |
| `admin_headers`        | JWT for admin user                             |

### E2E (`tests/e2e/conftest.py`)

| Fixture                            | Description                                  |
| ---------------------------------- | -------------------------------------------- |
| `workflow_course`                  | Course with all FK relationships             |
| `workflow_template`                | Template with `proxmoxId` (ready status)     |
| `workflow_event`                   | Event in "Geplant" status                    |
| `teacher_user` / `teacher_headers` | Teacher user with JWT                        |
| `student_user` / `student_headers` | Student user with JWT                        |
| `login_user`                       | User with real bcrypt hash (for login tests) |
| `user_b` / `user_b_headers`        | Second user without special permissions      |

---

## Factory System

All factories use `factory-boy` with `SQLAlchemyModelFactory` and are automatically bound to the test session via the `_bind_factories()` fixture.

```python
from tests.factories.user_factory import UserFactory

def test_something(db_session):
    user = UserFactory()  # Creates user in test DB
    assert user.status == "Active"
```

Shared fields (via `BaseFactory`): `id` (UUID4), `createdAt`, `updatedAt`, `createdById`, `updatedById`.

---

## Configuration

Test dependencies and pytest settings are defined in `code/pyproject.toml`:

---

## Conventions

- **File name:** `test_{module}.py` — mirrors the file under test
- **Class name:** `TestClassName` — groups thematically related tests
- **Test name:** `test_{expected_behavior}` — describes the expected outcome
- **Fixtures:** Defined in the nearest `conftest.py` (local before global)
- **Imports:** Models and controllers are imported inside tests (lazy), not at module level
- **UUIDs:** Always `uuid.uuid4()` with hex suffix for uniqueness (`f"user_{uuid.uuid4().hex[:6]}"`)
- **No real services:** Proxmox, Guacamole, LDAP, SMTP are always mocked
