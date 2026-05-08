"""description_column_add_missing

Add description String(1000) nullable=True to tables that gained
DescriptionMixin during the model-standardisation refactor but did not
previously have the column.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-03-13 00:02:00.000000+00:00

"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3e4f5a6b7c8"
down_revision: str | None = "c2d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = [
    "sys_users",
    "kvs_guacamole",
    "kvs_tags",
    "kvs_tasks",
    "kvs_sub_tasks",
]


def upgrade() -> None:
    """Upgrade schema."""
    for table in _TABLES:
        op.add_column(
            table,
            sa.Column("description", sa.String(length=1000), nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table in reversed(_TABLES):
        op.drop_column(table, "description")
