"""add company description insights

Revision ID: 5a6d8c9f3b21
Revises: fea0bcc1a1eb
Create Date: 2025-11-15 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "5a6d8c9f3b21"
down_revision: Union[str, Sequence[str], None] = "fea0bcc1a1eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add company description insight flags."""
    op.add_column(
        "companies",
        sa.Column("has_own_products", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("is_recruiting_company", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    """Remove company description insight flags."""
    op.drop_column("companies", "is_recruiting_company")
    op.drop_column("companies", "has_own_products")
