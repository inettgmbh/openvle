"""
Concurrency-safe Alembic migration runner.

Uses MariaDB advisory locks (GET_LOCK/RELEASE_LOCK) so that multiple
containers (backend replicas, workers) starting simultaneously don't
race on schema changes. Only one process migrates; others wait and
then proceed (upgrade head is a no-op if already at head).
"""

import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import NullPool

from core.config import Settings

LOCK_NAME = "openvle_migration"
LOCK_TIMEOUT = 120  # seconds


def _get_url() -> str:
    s = Settings()
    return (
        f"mariadb+pymysql://{s.mariadb_user}:{s.mariadb_password}"
        f"@{s.mariadb_host}:{s.mariadb_port}/{s.mariadb_database}"
        f"?charset={s.mariadb_charset}&connect_timeout={s.mariadb_timeout}"
    )


def run() -> None:
    url = _get_url()
    engine = create_engine(url, poolclass=NullPool)

    with engine.connect() as conn:
        # Acquire advisory lock
        result = conn.execute(
            text(f"SELECT GET_LOCK('{LOCK_NAME}', {LOCK_TIMEOUT})")
        ).scalar()

        if result != 1:
            print(
                f"[migrate] Could not acquire lock '{LOCK_NAME}' "
                f"within {LOCK_TIMEOUT}s. Aborting.",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            alembic_cfg = Config("alembic.ini")

            inspector = inspect(conn)
            existing_tables = inspector.get_table_names()
            has_alembic_version = "sys_alembic_version" in existing_tables
            has_existing_schema = "sys_users" in existing_tables

            if not has_alembic_version and has_existing_schema:
                # Existing DB without Alembic — stamp as current head
                print("[migrate] Existing database detected. Stamping head.")
                command.stamp(alembic_cfg, "head")
            else:
                # Fresh DB or already tracked — run pending migrations
                print("[migrate] Running alembic upgrade head...")
                command.upgrade(alembic_cfg, "head")

            print("[migrate] Migrations complete.")
        finally:
            conn.execute(text(f"SELECT RELEASE_LOCK('{LOCK_NAME}')"))

    engine.dispose()


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"[migrate] Migration failed: {e}", file=sys.stderr)
        sys.exit(1)
