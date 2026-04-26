"""Add upi_mandate_active to worker_profiles.

Revision ID: 20260425_05
Revises: 20260404_04_platform_partners_seed
Create Date: 2026-04-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260425_05"
down_revision = "20260404_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "worker_profiles",
        sa.Column(
            "upi_mandate_active",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("worker_profiles", "upi_mandate_active")
