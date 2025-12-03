"""add blocked_companies table

Revision ID: a1b2c3d4e5f6
Revises: 9b5c6d7e8f9a
Create Date: 2025-11-24 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "9b5c6d7e8f9a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create blocked_companies table."""
    op.create_table(
        "blocked_companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "company_id", name="uq_blocked_companies_user_company"),
    )
    op.create_index(op.f("ix_blocked_companies_id"), "blocked_companies", ["id"], unique=False)
    op.create_index(op.f("ix_blocked_companies_user_id"), "blocked_companies", ["user_id"], unique=False)
    op.create_index(op.f("ix_blocked_companies_company_id"), "blocked_companies", ["company_id"], unique=False)


def downgrade() -> None:
    """Drop blocked_companies table."""
    op.drop_index(op.f("ix_blocked_companies_company_id"), table_name="blocked_companies")
    op.drop_index(op.f("ix_blocked_companies_user_id"), table_name="blocked_companies")
    op.drop_index(op.f("ix_blocked_companies_id"), table_name="blocked_companies")
    op.drop_table("blocked_companies")









