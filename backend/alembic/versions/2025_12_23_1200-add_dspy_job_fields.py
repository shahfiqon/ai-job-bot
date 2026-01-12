"""add dspy job fields

Revision ID: b9b158a9923f
Revises: 71ac71411853
Create Date: 2025-12-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b9b158a9923f'
down_revision: Union[str, Sequence[str], None] = '71ac71411853'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new DSPy-parsed fields to jobs table."""
    op.add_column('jobs', sa.Column('is_python_main', sa.Boolean(), nullable=True))
    op.add_column('jobs', sa.Column('contract_feasible', sa.Boolean(), nullable=True))
    op.add_column('jobs', sa.Column('relocate_required', sa.Boolean(), nullable=True))
    op.add_column('jobs', sa.Column('specific_locations', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('jobs', sa.Column('accepts_non_us', sa.Boolean(), nullable=True))
    op.add_column('jobs', sa.Column('screening_required', sa.Boolean(), nullable=True))
    op.add_column('jobs', sa.Column('company_size', sa.String(length=64), nullable=True))


def downgrade() -> None:
    """Remove DSPy-parsed fields from jobs table."""
    op.drop_column('jobs', 'company_size')
    op.drop_column('jobs', 'screening_required')
    op.drop_column('jobs', 'accepts_non_us')
    op.drop_column('jobs', 'specific_locations')
    op.drop_column('jobs', 'relocate_required')
    op.drop_column('jobs', 'contract_feasible')
    op.drop_column('jobs', 'is_python_main')
