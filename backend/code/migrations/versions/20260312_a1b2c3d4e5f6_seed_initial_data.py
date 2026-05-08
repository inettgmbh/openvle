"""seed initial data

Revision ID: a1b2c3d4e5f6
Revises: 2209bf8f2d69
Create Date: 2026-03-12 16:00:00.000000+00:00

"""

from pathlib import Path
from typing import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "2209bf8f2d69"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SYSTEM_USER_ID = "1db3d8ac-22d9-4116-976a-93ad6e4fb234"

# Tables seeded, in FK-dependency order (reverse for downgrade)
SEEDED_TABLES = [
    "sys_users",
    "kvs_vendors",
    "kvs_apps",
    "kvs_os",
    "sys_roles",
    "sys_languages",
    "kvs_events_status",
    "sys_object_permissions",
    "sys_users_roles",
    "sys_mails_actions",
    "sys_mails_templates",
    "sys_settings",
]


def upgrade() -> None:
    bind = op.get_bind()

    # Idempotency: skip if system user already exists (existing DB)
    result = bind.execute(
        sa.text("SELECT COUNT(*) FROM sys_users WHERE id = :id"),
        {"id": SYSTEM_USER_ID},
    ).scalar()
    if result and result > 0:
        return

    # Read and execute seed SQL
    sql_path = Path(__file__).resolve().parent.parent / "seed_data.sql"
    sql = sql_path.read_text(encoding="utf-8")

    # Split on statement boundaries and execute each INSERT
    for statement in sql.split(";"):
        # Strip comment lines, then check for INSERT
        lines = [
            ln
            for ln in statement.strip().splitlines()
            if ln.strip() and not ln.strip().startswith("--")
        ]
        if not lines:
            continue
        body = "\n".join(lines)
        if body.lstrip().upper().startswith("INSERT"):
            # Use exec_driver_sql to avoid sa.text() interpreting
            # colons in data values (e.g. "[:100]") as bind params.
            bind.exec_driver_sql(body)


def downgrade() -> None:
    bind = op.get_bind()

    # Delete in reverse FK-dependency order
    for table in reversed(SEEDED_TABLES):
        if table == "sys_users_roles":
            # Delete all role assignments that reference seeded roles
            # or seeded users (covers openvle→admin_full mapping)
            bind.execute(
                sa.text(
                    f"DELETE FROM `{table}` WHERE role_id IN "
                    f"(SELECT id FROM sys_roles WHERE createdById = :uid) "
                    f"OR user_id IN "
                    f"(SELECT id FROM sys_users WHERE createdById = :uid "
                    f"OR id = :uid)"
                ),
                {"uid": SYSTEM_USER_ID},
            )
        elif table == "sys_users":
            # Collect seeded user IDs before breaking the FK
            rows = bind.execute(
                sa.text(
                    "SELECT id FROM sys_users "
                    "WHERE createdById = :uid OR id = :uid"
                ),
                {"uid": SYSTEM_USER_ID},
            ).fetchall()
            user_ids = tuple(str(r[0]) for r in rows)
            if not user_ids:
                continue
            placeholders = ",".join(["%s"] * len(user_ids))
            # Break self-referential FK (createdById → id)
            bind.exec_driver_sql(
                f"UPDATE sys_users "
                f"SET createdById = NULL, updatedById = NULL "
                f"WHERE id IN ({placeholders})",
                user_ids,
            )
            # Delete the seeded users
            bind.exec_driver_sql(
                f"DELETE FROM sys_users WHERE id IN ({placeholders})",
                user_ids,
            )
        else:
            bind.execute(
                sa.text(f"DELETE FROM `{table}` WHERE createdById = :uid"),
                {"uid": SYSTEM_USER_ID},
            )
