"""add seen_jobs table

Revision ID: add_seen_jobs_table
Revises: b9b158a9923f
Create Date: 2026-01-13 09:43:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_seen_jobs_table'
down_revision: Union[str, Sequence[str], None] = 'b9b158a9923f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create seen_jobs table."""
    op.create_table(
        'seen_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_seen_jobs_user_id'), 'seen_jobs', ['user_id'], unique=False)
    op.create_index(op.f('ix_seen_jobs_job_id'), 'seen_jobs', ['job_id'], unique=False)
    op.create_index('ix_seen_jobs_user_job', 'seen_jobs', ['user_id', 'job_id'], unique=True)


def downgrade() -> None:
    """Drop seen_jobs table."""
    op.drop_index('ix_seen_jobs_user_job', table_name='seen_jobs')
    op.drop_index(op.f('ix_seen_jobs_job_id'), table_name='seen_jobs')
    op.drop_index(op.f('ix_seen_jobs_user_id'), table_name='seen_jobs')
    op.drop_table('seen_jobs')
