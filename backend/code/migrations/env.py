import os
import sys
from logging.config import fileConfig

import sqlalchemy as sa
from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.dialects.mysql.base import MySQLDialect

# MariaDB 10.11+ has a native UUID column type that SQLAlchemy's
# MariaDB dialect doesn't recognise during reflection. Register it
# so that autogenerate / check can compare columns correctly.
MySQLDialect.ischema_names["uuid"] = sa.UUID

# Make app code importable
sys.path.insert(0, os.path.dirname(__file__) + "/..")

# Alembic Config object
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models so metadata is fully populated
import models
from models.base import DBBaseModel
from models.changelog import Base as ChangelogBase

target_metadata = [DBBaseModel.metadata, ChangelogBase.metadata]


def _get_url() -> str:
    """Build DB URL from env vars (same logic as core/mariadb.py)."""
    # If already set via alembic.ini or programmatically, use that
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url

    # Build from environment / Settings
    from core.config import Settings

    s = Settings()
    return (
        f"mariadb+pymysql://{s.mariadb_user}:{s.mariadb_password}"
        f"@{s.mariadb_host}:{s.mariadb_port}/{s.mariadb_database}"
        f"?charset={s.mariadb_charset}&connect_timeout={s.mariadb_timeout}"
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL)."""
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="sys_alembic_version",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (against live DB)."""
    connectable = create_engine(_get_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="sys_alembic_version",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
