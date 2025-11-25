"""add resume_json to users

Revision ID: f1a2b3c4d5e6
Revises: a1b2c3d4e5f6
Create Date: 2025-11-25 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add resume_json column to users table."""
    op.add_column("users", sa.Column("resume_json", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove resume_json column from users table."""
    op.drop_column("users", "resume_json")


