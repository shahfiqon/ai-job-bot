"""add saved_jobs table

Revision ID: 9b5c6d7e8f9a
Revises: 8a4187cce805
Create Date: 2025-11-20 18:01:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9b5c6d7e8f9a"
down_revision: Union[str, Sequence[str], None] = "8a4187cce805"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create saved_jobs table."""
    op.create_table(
        "saved_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="saved",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
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
            ["job_id"],
            ["jobs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "job_id", name="uq_saved_jobs_user_job"),
    )
    op.create_index(op.f("ix_saved_jobs_id"), "saved_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_saved_jobs_user_id"), "saved_jobs", ["user_id"], unique=False)
    op.create_index(op.f("ix_saved_jobs_job_id"), "saved_jobs", ["job_id"], unique=False)
    op.create_index(op.f("ix_saved_jobs_status"), "saved_jobs", ["status"], unique=False)


def downgrade() -> None:
    """Drop saved_jobs table."""
    op.drop_index(op.f("ix_saved_jobs_status"), table_name="saved_jobs")
    op.drop_index(op.f("ix_saved_jobs_job_id"), table_name="saved_jobs")
    op.drop_index(op.f("ix_saved_jobs_user_id"), table_name="saved_jobs")
    op.drop_index(op.f("ix_saved_jobs_id"), table_name="saved_jobs")
    op.drop_table("saved_jobs")

