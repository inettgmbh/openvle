"""changelog_value_columns_widen

Widen sys_changelogs.valueOld and valueNew from VARCHAR(1500) to VARCHAR(2000)
to accommodate diff-compressed change records produced by the model
standardisation refactor.

Revision ID: b1c2d3e4f5a6
Revises: a0731f0209ef
Create Date: 2026-03-13 00:00:00.000000+00:00

"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "a0731f0209ef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "sys_changelogs",
        "valueOld",
        existing_type=sa.String(length=1500),
        type_=sa.String(length=2000),
        existing_nullable=True,
    )
    op.alter_column(
        "sys_changelogs",
        "valueNew",
        existing_type=sa.String(length=1500),
        type_=sa.String(length=2000),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "sys_changelogs",
        "valueNew",
        existing_type=sa.String(length=2000),
        type_=sa.String(length=1500),
        existing_nullable=True,
    )
    op.alter_column(
        "sys_changelogs",
        "valueOld",
        existing_type=sa.String(length=2000),
        type_=sa.String(length=1500),
        existing_nullable=True,
    )
