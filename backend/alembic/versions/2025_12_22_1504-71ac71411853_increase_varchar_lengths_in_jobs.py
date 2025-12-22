"""increase varchar lengths in jobs

Revision ID: 71ac71411853
Revises: cad04a32a0ba
Create Date: 2025-12-22 15:04:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71ac71411853'
down_revision: Union[str, Sequence[str], None] = 'cad04a32a0ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Increase VARCHAR(255) fields to VARCHAR(512) to prevent truncation errors
    op.alter_column('jobs', 'company_name',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=512),
                    existing_nullable=True)
    op.alter_column('jobs', 'location_city',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=512),
                    existing_nullable=True)
    op.alter_column('jobs', 'location_state',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=512),
                    existing_nullable=True)
    op.alter_column('jobs', 'location_country',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=512),
                    existing_nullable=True)
    op.alter_column('jobs', 'company_industry',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=512),
                    existing_nullable=True)
    op.alter_column('jobs', 'company_headquarters',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=512),
                    existing_nullable=True)
    op.alter_column('jobs', 'required_education',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=512),
                    existing_nullable=True)
    op.alter_column('jobs', 'preferred_education',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=512),
                    existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert VARCHAR(512) fields back to VARCHAR(255)
    op.alter_column('jobs', 'preferred_education',
                    existing_type=sa.String(length=512),
                    type_=sa.String(length=255),
                    existing_nullable=True)
    op.alter_column('jobs', 'required_education',
                    existing_type=sa.String(length=512),
                    type_=sa.String(length=255),
                    existing_nullable=True)
    op.alter_column('jobs', 'company_headquarters',
                    existing_type=sa.String(length=512),
                    type_=sa.String(length=255),
                    existing_nullable=True)
    op.alter_column('jobs', 'company_industry',
                    existing_type=sa.String(length=512),
                    type_=sa.String(length=255),
                    existing_nullable=True)
    op.alter_column('jobs', 'location_country',
                    existing_type=sa.String(length=512),
                    type_=sa.String(length=255),
                    existing_nullable=True)
    op.alter_column('jobs', 'location_state',
                    existing_type=sa.String(length=512),
                    type_=sa.String(length=255),
                    existing_nullable=True)
    op.alter_column('jobs', 'location_city',
                    existing_type=sa.String(length=512),
                    type_=sa.String(length=255),
                    existing_nullable=True)
    op.alter_column('jobs', 'company_name',
                    existing_type=sa.String(length=512),
                    type_=sa.String(length=255),
                    existing_nullable=True)

