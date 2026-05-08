import sys
import warnings

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SAWarning, SQLAlchemyError

warnings.filterwarnings(
    "ignore",
    message=r"Object of type .* not in session",
    category=SAWarning,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from core.config import Settings
from core.exceptions import MariaDBConnectionError

settings = Settings()

SQLALCHEMY_DATABASE_URL = (
    f"mariadb+pymysql://{settings.mariadb_user}:{settings.mariadb_password}"
    f"@{settings.mariadb_host}:{settings.mariadb_port}/{settings.mariadb_database}"
    f"?charset={settings.mariadb_charset}&connect_timeout={settings.mariadb_timeout}"
)

_connect_args = {
    "connect_timeout": settings.mariadb_timeout,
    "read_timeout": settings.mariadb_timeout,
    "write_timeout": settings.mariadb_timeout,
}

# Pooling is disabled when either:
#  1. MARIADB_POOL_ENABLED=false is set explicitly (env / .env), or
#  2. Auto-detected as RQ worker (core.config_worker loaded via -c flag)
_pool_enabled = settings.mariadb_pool_enabled
if _pool_enabled and "core.config_worker" in sys.modules:
    _pool_enabled = False

if _pool_enabled:
    pool_acquire_s = max(
        1, int(getattr(settings, "mariadb_pool_acquire", 8000) / 1000)
    )
    pool_recycle_s = max(
        30, int(getattr(settings, "mariadb_pool_idle", 180000) / 1000)
    )
    pool_min = int(getattr(settings, "mariadb_pool_min", 2))
    pool_max = int(getattr(settings, "mariadb_pool_max", 10))
    max_overflow = max(0, pool_max - pool_min)

    engine_kwargs = {
        "connect_args": _connect_args,
        "pool_size": pool_min,
        "max_overflow": max_overflow,
        "pool_timeout": pool_acquire_s,
        "pool_recycle": pool_recycle_s,
        "pool_pre_ping": True,
        "pool_use_lifo": True,
        "future": True,
    }
else:
    engine_kwargs = {
        "connect_args": _connect_args,
        "poolclass": NullPool,
        "future": True,
    }

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        **engine_kwargs,
        isolation_level="READ COMMITTED",
    )
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except OperationalError as e:
    # Add local logger call with exception msg
    raise MariaDBConnectionError()
except SQLAlchemyError as e:
    # Add local logger call with exception msg
    raise MariaDBConnectionError()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    except OperationalError as e:
        # Add local logger call with exception msg
        raise MariaDBConnectionError()
    finally:
        db.close()
