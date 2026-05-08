"""rename_events_actions_end_to_stop

Rename permission_key 'events_actions_end' -> 'events_actions_stop' and
'object_actions_end' -> 'object_actions_stop' in sys_object_permissions
to align Events with the VMs naming convention.

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-04-07 00:00:00.000000+00:00

"""

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e4f5a6b7c8d9"
down_revision: str | None = "d3e4f5a6b7c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename events_actions_end -> events_actions_stop permission keys."""
    op.execute(
        "UPDATE sys_object_permissions "
        "SET permission_key = 'events_actions_stop' "
        "WHERE permission_key = 'events_actions_end'"
    )
    op.execute(
        "UPDATE sys_object_permissions "
        "SET permission_key = 'object_actions_stop' "
        "WHERE permission_key = 'object_actions_end'"
    )


def downgrade() -> None:
    """Revert events_actions_stop -> events_actions_end permission keys."""
    op.execute(
        "UPDATE sys_object_permissions "
        "SET permission_key = 'events_actions_end' "
        "WHERE permission_key = 'events_actions_stop' "
        "AND object_type = 'Event'"
    )
    op.execute(
        "UPDATE sys_object_permissions "
        "SET permission_key = 'object_actions_end' "
        "WHERE permission_key = 'object_actions_stop' "
        "AND object_type = 'Event'"
    )
