"""add job sync fields

Revision ID: f35fe1df4134
Revises: 0001_initial
Create Date: 2026-09-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f35fe1df4134"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Track when a job was last seen from the job source.
    op.add_column(
        "jobs",
        sa.Column(
            "last_seen_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
        ),
    )

    # Existing jobs should be active by default.
    op.add_column(
        "jobs",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    # Optional expiry date supplied by the job source.
    op.add_column(
        "jobs",
        sa.Column(
            "expires_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    # Prevent the same source listing from being inserted twice.
    op.create_unique_constraint(
        "uq_jobs_source_url",
        "jobs",
        ["source_url"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_jobs_source_url",
        "jobs",
        type_="unique",
    )

    op.drop_column("jobs", "expires_at")
    op.drop_column("jobs", "is_active")
    op.drop_column("jobs", "last_seen_at")