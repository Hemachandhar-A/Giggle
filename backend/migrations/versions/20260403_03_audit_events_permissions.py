"""Revoke UPDATE and DELETE permissions on audit_events (append-only enforcement).

Revision ID: 20260403_03
Revises: 20260403_02
Create Date: 2026-04-03 00:20:00
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260403_03"
down_revision = "20260403_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Revoke UPDATE and DELETE on audit_events from PUBLIC role.
    # This enforces append-only constraint at the PostgreSQL level per IRDAI requirement.
    op.execute(
        """
        REVOKE UPDATE ON audit_events FROM PUBLIC
        """
    )
    op.execute(
        """
        REVOKE DELETE ON audit_events FROM PUBLIC
        """
    )


def downgrade() -> None:
    # Intentionally a no-op.
    # audit_events append-only constraint must never be reversed — downgrade is not permitted for this migration.
    # If rollback is needed, drop and recreate the table.
    pass
