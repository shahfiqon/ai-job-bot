"""add_llm_parsed_job_fields

Revision ID: 360fe7900b74
Revises: 5a6d8c9f3b21
Create Date: 2025-11-14 07:28:11.347533

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '360fe7900b74'
down_revision: Union[str, Sequence[str], None] = '5a6d8c9f3b21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add LLM-parsed job fields to jobs table
    op.add_column('jobs', sa.Column('required_skills', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('jobs', sa.Column('preferred_skills', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('jobs', sa.Column('required_years_experience', sa.Integer(), nullable=True))
    op.add_column('jobs', sa.Column('required_education', sa.String(length=255), nullable=True))
    op.add_column('jobs', sa.Column('preferred_education', sa.String(length=255), nullable=True))
    op.add_column('jobs', sa.Column('responsibilities', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('jobs', sa.Column('benefits', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('jobs', sa.Column('work_arrangement', sa.String(length=64), nullable=True))
    op.add_column('jobs', sa.Column('team_size', sa.String(length=128), nullable=True))
    op.add_column('jobs', sa.Column('technologies', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('jobs', sa.Column('culture_keywords', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('jobs', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('jobs', sa.Column('job_categories', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('jobs', sa.Column('independent_contractor_friendly', sa.Boolean(), nullable=True))
    op.add_column('jobs', sa.Column('parsed_salary_currency', sa.String(length=16), nullable=True))
    op.add_column('jobs', sa.Column('parsed_salary_min', sa.Float(), nullable=True))
    op.add_column('jobs', sa.Column('parsed_salary_max', sa.Float(), nullable=True))
    op.add_column('jobs', sa.Column('compensation_basis', sa.String(length=64), nullable=True))
    op.add_column('jobs', sa.Column('location_restrictions', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('jobs', sa.Column('exclusive_location_requirement', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove LLM-parsed job fields
    op.drop_column('jobs', 'exclusive_location_requirement')
    op.drop_column('jobs', 'location_restrictions')
    op.drop_column('jobs', 'compensation_basis')
    op.drop_column('jobs', 'parsed_salary_max')
    op.drop_column('jobs', 'parsed_salary_min')
    op.drop_column('jobs', 'parsed_salary_currency')
    op.drop_column('jobs', 'independent_contractor_friendly')
    op.drop_column('jobs', 'job_categories')
    op.drop_column('jobs', 'summary')
    op.drop_column('jobs', 'culture_keywords')
    op.drop_column('jobs', 'technologies')
    op.drop_column('jobs', 'team_size')
    op.drop_column('jobs', 'work_arrangement')
    op.drop_column('jobs', 'benefits')
    op.drop_column('jobs', 'responsibilities')
    op.drop_column('jobs', 'preferred_education')
    op.drop_column('jobs', 'required_education')
    op.drop_column('jobs', 'required_years_experience')
    op.drop_column('jobs', 'preferred_skills')
    op.drop_column('jobs', 'required_skills')
