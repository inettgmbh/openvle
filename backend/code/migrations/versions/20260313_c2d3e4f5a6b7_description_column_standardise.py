"""description_column_standardise

Standardise description columns to String(1000) nullable=True across all
models that use DescriptionMixin.  Tables that were already at 1000 chars
(kvs_templates, kvs_vms) are untouched.

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-03-13 00:01:00.000000+00:00

"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c2d3e4f5a6b7"
down_revision: str | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (table, old_length) — all become String(1000) nullable=True
_TABLES = [
    ("kvs_courses", 255),
    ("kvs_documents", 255),
    ("kvs_vendors", 255),
    ("sys_mails_actions", 500),
    ("sys_policies", 250),
    ("sys_roles", 255),
    ("kvs_apps", 255),
    ("kvs_events", 255),
    ("kvs_os", 100),
    ("sys_mails_templates", 100),
]


def upgrade() -> None:
    """Upgrade schema."""
    for table, old_length in _TABLES:
        op.alter_column(
            table,
            "description",
            existing_type=sa.String(length=old_length),
            type_=sa.String(length=1000),
            existing_nullable=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table, old_length in reversed(_TABLES):
        op.alter_column(
            table,
            "description",
            existing_type=sa.String(length=1000),
            type_=sa.String(length=old_length),
            existing_nullable=True,
        )
