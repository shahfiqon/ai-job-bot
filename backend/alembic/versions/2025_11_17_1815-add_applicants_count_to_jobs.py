"""add applicants_count to jobs

Revision ID: a1b2c3d4e5f6
Revises: 360fe7900b74
Create Date: 2025-11-17 18:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9081e4da991e"
down_revision: Union[str, Sequence[str], None] = "360fe7900b74"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add applicants_count column to jobs table."""
    op.add_column(
        "jobs",
        sa.Column("applicants_count", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Remove applicants_count column from jobs table."""
    op.drop_column("jobs", "applicants_count")

