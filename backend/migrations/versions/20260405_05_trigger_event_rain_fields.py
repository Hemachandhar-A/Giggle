"""Add rain surge and peak multiplier flags to trigger_events.

Revision ID: 20260405_05
Revises: 20260404_04
Create Date: 2026-04-05 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260405_05"
down_revision = "20260404_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "trigger_events",
        sa.Column(
            "rain_surge_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "trigger_events",
        sa.Column(
            "peak_multiplier_applied",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("trigger_events", "peak_multiplier_applied")
    op.drop_column("trigger_events", "rain_surge_active")
