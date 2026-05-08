"""
Root conftest.py - Test infrastructure setup.

Sets up environment variables BEFORE any app imports to avoid
module-level side effects (mariadb.py, redis.py, mongodb.py).
Provides MariaDB testcontainer and session fixtures.
"""

import os
import sys
import types
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------
# 1. sys.path: make app code importable as top-level packages
# ---------------------------------------------------------------
CODE_DIR = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(CODE_DIR))

# ---------------------------------------------------------------
# 2. Environment variables BEFORE Settings/App imports
# ---------------------------------------------------------------
_TEST_ENV = {
    # App
    "app_env": "testing",
    "project_name": "test_openvle",
    "project_title": "Test KVS",
    "project_description": "Test environment",
    "project_version": "0.99",
    # Auth
    "auth_secret": "test-secret-key-for-jwt-testing-only",
    "auth_algorithm": "HS256",
    "auth_access_token_expire_minutes": "480",
    # Session
    "session_secret_token": "test-session-secret",
    # MariaDB - placeholder, overridden by testcontainer
    "mariadb_host": "localhost",
    "mariadb_port": "3306",
    "mariadb_user": "test",
    "mariadb_password": "test",
    "mariadb_database": "test_openvle",
    "mariadb_charset": "utf8mb4",
    "mariadb_timeout": "5",
    "mariadb_pool_min": "1",
    "mariadb_pool_max": "2",
    "mariadb_pool_acquire": "5000",
    "mariadb_pool_idle": "30000",
    "mariadb_query_result_limit": "500",
    # MongoDB - placeholder
    "mongodb_host": "localhost",
    "mongodb_port": "27017",
    "mongodb_user": "test",
    "mongodb_password": "test",
    "mongodb_database": "test_openvle",
    # Redis - placeholder
    "redis_host": "localhost",
    "redis_port": "6379",
    "redis_password": "",
    "redis_username": "",
    "redis_database": "0",
    # Proxmox
    "pve_hostname": "test-pve.local",
    "pve_fqdn": "test-pve.local",
    "pve_user": "test@pve",
    "pve_token_name": "test",
    "pve_token_value": "test-token",
    "pve_vm_subnet": "10.0.0.0/24",
    "pve_verify_ssl": "false",
    # Guacamole
    "guacamole_url": "http://localhost:8080/guacamole",
    "guacamole_user": "guacadmin",
    "guacamole_password": "guacadmin",
    "guacamole_db": "guacamole_db",
    # SMTP
    "smtp_host": "localhost",
    "smtp_port": "1025",
    "smtp_username": "",
    "smtp_password": "",
    "smtp_from_mail": "test@example.com",
    "smtp_from_name": "Test KVS",
    "smtp_method": "NONE",
    # Sentry
    "sentry_backend_enabled": "false",
    "sentry_worker_enabled": "false",
    # LDAP
    "ldap_enabled": "false",
    "ldap_host": "localhost",
    "ldap_port": "389",
    # OIDC
    "oidc_enabled": "false",
    # CORS
    "cors_origins": '["*"]',
    "cors_methods": '["*"]',
    "cors_headers": '["*"]',
    "cors_credentials": "true",
    # Events
    "events_start_prep_time_days": "7",
    "events_end_prep_time_days": "7",
    "events_start_require_students": "true",
    # Worker
    "worker_max_retry": "5",
    "worker_pve_periodic_interval": "60",
    # Contact
    "contact_mail": "test@example.com",
    "contact_name": "Test",
    "contact_url": "http://localhost",
    # Health
    "api_health_token": "test-health-token",
    # Mail
    "mail_max_age_weeks": "4",
    # Moodle
    "moodle_enabled": "false",
    "moodle_url": "https://moodle.test",
    "moodle_token": "test-token",
    "moodle_verify_ssl": "false",
    "moodle_timeout": "30",
    "moodle_sync_timeout": "10",
    "moodle_user_auth": "ldap",
    "moodle_user_match_field": "email",
    "moodle_course_visible": "true",
    "moodle_delete_course_on_event_delete": "false",
}

for key, value in _TEST_ENV.items():
    os.environ.setdefault(key, value)

# Docker socket for Colima (testcontainers needs this)
try:
    _colima_sock = Path.home() / ".colima" / "default" / "docker.sock"
    if _colima_sock.exists() and "DOCKER_HOST" not in os.environ:
        os.environ["DOCKER_HOST"] = f"unix://{_colima_sock}"
        # Use /var/run/docker.sock inside the VM, not the host path
        os.environ["TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE"] = "/var/run/docker.sock"
except (PermissionError, OSError):
    pass


# ---------------------------------------------------------------
# 3. Pre-load modules with side effects to prevent connection
#    attempts during import. These modules create DB/Redis/Mongo
#    connections at module level; we replace them with stubs.
# ---------------------------------------------------------------
def _create_stub_mariadb():
    """Create a stub core.mariadb module that doesn't connect to any DB."""
    from sqlalchemy.orm import sessionmaker

    mod = types.ModuleType("core.mariadb")
    mod.engine = None  # Will be replaced by test_engine fixture
    mod.SessionLocal = sessionmaker()  # Unbound, overridden per test
    mod.Base = None
    mod.get_db = MagicMock()
    mod.SQLALCHEMY_DATABASE_URL = "mariadb+pymysql://test:test@localhost/test"
    mod.settings = None
    return mod


def _create_stub_redis():
    """Create a stub core.redis module with fake queues."""
    mod = types.ModuleType("core.redis")

    # Stub redis_connection with return values
    redis_mock = MagicMock()
    redis_mock.ttl.return_value = -2  # key does not exist
    redis_mock.get.return_value = None
    redis_mock.incr.return_value = 0
    redis_mock.delete.return_value = 0
    redis_mock.exists.return_value = 0
    redis_mock.expire.return_value = False
    redis_mock.setex.return_value = True
    redis_mock.scan_iter.return_value = iter([])
    mod.redis_connection = redis_mock

    # Create fake queues
    for name in [
        "queue_pve_periodic",
        "queue_pve_vm_clone",
        "queue_pve_vm_actions",
        "queue_mails",
        "queue_guacamole",
        "queue_moodle",
        "queue_core_periodic",
    ]:
        setattr(mod, name, MagicMock(name=name))

    mod.settings = None
    return mod


def _create_stub_mongodb():
    """Create a stub core.mongodb module."""
    mod = types.ModuleType("core.mongodb")
    mod.client = MagicMock()
    mod.db = MagicMock()
    mod.settings = None
    return mod


# Install stubs BEFORE any test file or app module can import them
sys.modules["core.mariadb"] = _create_stub_mariadb()
sys.modules["core.redis"] = _create_stub_redis()
sys.modules["core.mongodb"] = _create_stub_mongodb()


# ---------------------------------------------------------------
# 4. MariaDB: Testcontainer (local) or external service (CI)
#
#    Set MARIADB_TEST_URL to skip the testcontainer and connect
#    to an external MariaDB, e.g. a GitLab CI service:
#      MARIADB_TEST_URL=mariadb+pymysql://test:test@mariadb:3306/test_openvle
# ---------------------------------------------------------------
_MARIADB_TEST_URL = os.environ.get("MARIADB_TEST_URL")


@pytest.fixture(scope="session")
def mariadb_container():
    """Start a MariaDB testcontainer for the entire test session.

    Skipped when MARIADB_TEST_URL is set (CI mode).
    """
    if _MARIADB_TEST_URL:
        yield None
        return

    from testcontainers.mysql import MySqlContainer

    with MySqlContainer(
        "mariadb:10.11",
        username="test",
        password="test",
        dbname="test_openvle",
    ) as container:
        yield container


@pytest.fixture(scope="session")
def test_engine(mariadb_container):
    """Create SQLAlchemy engine connected to testcontainer or CI service."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    if _MARIADB_TEST_URL:
        url = _MARIADB_TEST_URL
    else:
        url = mariadb_container.get_connection_url()
        # testcontainers may return mysql+mysqldb or mysql+pymysql
        if url.startswith("mysql+mysqldb://"):
            url = url.replace("mysql+mysqldb://", "mariadb+pymysql://", 1)
        elif url.startswith("mysql+pymysql://"):
            url = url.replace("mysql+pymysql://", "mariadb+pymysql://", 1)
        elif url.startswith("mysql://"):
            url = url.replace("mysql://", "mariadb+pymysql://", 1)

    # pytest-xdist: give each worker its own database
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    if worker_id and _MARIADB_TEST_URL:
        from sqlalchemy.engine import make_url

        parsed = make_url(url)
        worker_db = f"{parsed.database}_{worker_id}"

        admin_engine = create_engine(url, pool_pre_ping=True)
        with admin_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{worker_db}`"))
            conn.commit()
        admin_engine.dispose()

        url = parsed.set(database=worker_db).render_as_string(hide_password=False)

    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=2,
    )

    # Update the stub module with the real engine and SessionLocal
    import core.mariadb as mariadb_mod

    mariadb_mod.engine = engine
    mariadb_mod.SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )

    # Run Alembic migrations to create schema
    from alembic.config import Config as AlembicConfig
    from alembic import command as alembic_command

    alembic_cfg = AlembicConfig(str(CODE_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", url)
    alembic_cfg.set_main_option("script_location", str(CODE_DIR / "migrations"))
    alembic_command.upgrade(alembic_cfg, "head")

    return engine


@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    Per-test DB session with transaction rollback.
    Each test gets a clean slate without needing to truncate tables.

    Uses nested transactions (SAVEPOINTs) so that application code calling
    session.commit() / session.close() does not break test isolation.
    """
    from sqlalchemy import event
    from sqlalchemy.orm import sessionmaker

    connection = test_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    # Custom attribute used by the app (set in dependencies.get_db)
    session.current_user_id = None

    # Begin a nested transaction (SAVEPOINT).
    session.begin_nested()

    # Each time the application code calls session.commit() or the nested
    # transaction ends, automatically start a new SAVEPOINT so subsequent
    # operations still run inside the outer transaction.
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.expire_all()
            sess.begin_nested()

    # Prevent session.close() in application code from detaching the session
    _original_close = session.close

    def _noop_close():
        # Expire all so subsequent queries re-fetch, but don't actually close
        session.expire_all()

    session.close = _noop_close

    yield session

    # Remove the event listener to break the reference cycle
    # (listener closure → session → connection → pool fairy).
    # Without this, the fairy lingers until GC runs after the
    # testcontainer has already been stopped, causing a
    # "Lost connection to MySQL server" error during rollback.
    # fixme
    event.remove(session, "after_transaction_end", restart_savepoint)

    # Restore original close and clean up
    session.close = _original_close
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


# ---------------------------------------------------------------
# 5. Shared fixtures used by both unit and integration tests.
#    Previously in tests/unit/conftest.py, moved here so pytest
#    auto-discovers them for all test directories without needing
#    pytest_plugins (which fails with duplicate registration).
# ---------------------------------------------------------------
from models import Course, EventStatus, Role, User  # noqa: E402
from tests.helpers.mock_request import create_mock_request  # noqa: E402


@pytest.fixture(autouse=True)
def _bind_factories(request):
    """Bind all factory-boy factories to the current test session (if db_session is used)."""
    if "db_session" not in request.fixturenames:
        return
    db_session = request.getfixturevalue("db_session")
    from tests.factories.base import BaseFactory

    for cls in BaseFactory.__subclasses__():
        cls._meta.sqlalchemy_session = db_session


@pytest.fixture()
def system_user(db_session):
    """Return the 'system' user seeded by the Alembic migration."""
    user = db_session.get(User, uuid.UUID("1db3d8ac-22d9-4116-976a-93ad6e4fb234"))
    assert user is not None, "System user not found — seed migration missing?"
    return user


@pytest.fixture()
def active_user(db_session, system_user):
    """Create a regular active user for testing."""
    now = datetime.now(timezone.utc)
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        username="testuser",
        name="Test User",
        email="testuser@example.com",
        hashed_password="$2b$12$dummyhashvalue",
        status="Active",
        locale="de_DE",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture()
def mock_request(active_user):
    """Create a mock FastAPI Request with an authenticated user."""
    return create_mock_request(active_user)


@pytest.fixture()
def mock_request_system(system_user):
    """Create a mock FastAPI Request with the system user."""
    return create_mock_request(system_user)


@pytest.fixture()
def event_statuses(db_session, system_user):
    """Return seeded event statuses from the Alembic migration."""
    rows = db_session.query(EventStatus).all()
    return {s.name: s for s in rows}


@pytest.fixture()
def sample_course(db_session, system_user):
    """Create a sample course."""
    now = datetime.now(timezone.utc)
    course = Course(
        id=uuid.uuid4(),
        name="Test Course",
        description="A test course",
        guacamole=True,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(course)
    db_session.flush()
    return course


@pytest.fixture()
def role_admin(db_session, system_user):
    """Return the seeded admin_full role."""
    role = db_session.query(Role).filter_by(key="admin_full").one()
    return role


@pytest.fixture()
def role_teacher(db_session, system_user):
    """Return the seeded lehrende role."""
    role = db_session.query(Role).filter_by(key="lehrende").one()
    return role


@pytest.fixture()
def role_student(db_session, system_user):
    """Return the seeded studierende role."""
    role = db_session.query(Role).filter_by(key="studierende").one()
    return role


@pytest.fixture()
def mock_permission_allow(monkeypatch):
    """Patch PermissionChecker to always allow."""
    from core.dependencies import PermissionChecker

    monkeypatch.setattr(PermissionChecker, "has_permission", lambda self: True)


@pytest.fixture()
def mock_redis_queues(monkeypatch):
    """Mock all Redis queues to capture enqueued jobs."""
    enqueued_jobs = []

    class FakeJob:
        def __init__(self, func, *args, **kwargs):
            self.id = str(uuid.uuid4())
            self.func = func
            self.args = args
            self.kwargs = kwargs

    class FakeQueue:
        def __init__(self, name="default"):
            self.name = name

        def enqueue(self, func, *args, **kwargs):
            job = FakeJob(func, *args, **kwargs)
            enqueued_jobs.append(
                {
                    "queue": self.name,
                    "func": func,
                    "args": args,
                    "kwargs": kwargs,
                    "job": job,
                }
            )
            return job

    queue_names = [
        "queue_pve_periodic",
        "queue_pve_vm_clone",
        "queue_pve_vm_actions",
        "queue_mails",
        "queue_guacamole",
        "queue_core_periodic",
        "queue_moodle",
    ]

    import core.redis as redis_module

    for name in queue_names:
        fake = FakeQueue(name)
        monkeypatch.setattr(redis_module, name, fake)

    # Also patch direct references in controller modules that did
    # `from core.redis import queue_*` at module level.
    _controller_queue_map = {
        "controllers.events": [
            "queue_core_periodic",
            "queue_guacamole",
            "queue_moodle",
            "queue_pve_vm_actions",
            "queue_pve_vm_clone",
        ],
        "controllers.virtual_machines": [
            "queue_guacamole",
            "queue_pve_vm_actions",
            "queue_pve_vm_clone",
        ],
        "controllers.users": [
            "queue_pve_vm_actions",
            "queue_pve_vm_clone",
        ],
        "controllers.templates": [
            "queue_pve_vm_actions",
            "queue_pve_vm_clone",
        ],
        "controllers.mails": ["queue_mails"],
        "controllers.guacamole": ["queue_guacamole"],
        "controllers.tags": ["queue_pve_vm_actions"],
        "controllers.sub_tasks": [
            "queue_pve_vm_actions",
            "queue_pve_vm_clone",
            "queue_pve_periodic",
            "queue_core_periodic",
        ],
        "core.events_worker": [
            "queue_core_periodic",
            "queue_pve_vm_actions",
            "queue_pve_vm_clone",
        ],
    }

    for mod_path, queues in _controller_queue_map.items():
        mod = sys.modules.get(mod_path)
        if mod is None:
            continue
        for q_name in queues:
            if hasattr(mod, q_name):
                monkeypatch.setattr(mod, q_name, FakeQueue(q_name))

    return enqueued_jobs
