"""initial migration with companies and jobs tables

Revision ID: fea0bcc1a1eb
Revises: 
Create Date: 2025-11-11 09:13:14.066039

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'fea0bcc1a1eb'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("linkedin_url", sa.String(length=512), nullable=False),
        sa.Column("linkedin_internal_id", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.String(length=512), nullable=True),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("company_size_min", sa.Integer(), nullable=True),
        sa.Column("company_size_max", sa.Integer(), nullable=True),
        sa.Column("company_size_on_linkedin", sa.Integer(), nullable=True),
        sa.Column("hq_country", sa.String(length=128), nullable=True),
        sa.Column("hq_city", sa.String(length=128), nullable=True),
        sa.Column("hq_state", sa.String(length=128), nullable=True),
        sa.Column("hq_postal_code", sa.String(length=64), nullable=True),
        sa.Column("company_type", sa.String(length=128), nullable=True),
        sa.Column("founded_year", sa.Integer(), nullable=True),
        sa.Column("tagline", sa.String(length=255), nullable=True),
        sa.Column("universal_name_id", sa.String(length=255), nullable=True),
        sa.Column("profile_pic_url", sa.String(length=1024), nullable=True),
        sa.Column("background_cover_image_url", sa.String(length=1024), nullable=True),
        sa.Column("specialities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("locations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_companies_id"), "companies", ["id"], unique=False)
    op.create_index(
        op.f("ix_companies_linkedin_url"),
        "companies",
        ["linkedin_url"],
        unique=True,
    )
    op.create_index(op.f("ix_companies_name"), "companies", ["name"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_url", sa.String(length=1024), nullable=False),
        sa.Column("job_url_direct", sa.String(length=1024), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("company_url", sa.String(length=1024), nullable=True),
        sa.Column("company_url_direct", sa.String(length=1024), nullable=True),
        sa.Column("location_city", sa.String(length=255), nullable=True),
        sa.Column("location_state", sa.String(length=255), nullable=True),
        sa.Column("location_country", sa.String(length=255), nullable=True),
        sa.Column("compensation_min", sa.Float(), nullable=True),
        sa.Column("compensation_max", sa.Float(), nullable=True),
        sa.Column(
            "compensation_currency",
            sa.String(length=16),
            server_default=sa.text("'USD'"),
            nullable=True,
        ),
        sa.Column("compensation_interval", sa.String(length=64), nullable=True),
        sa.Column("job_type", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("date_posted", sa.Date(), nullable=True),
        sa.Column("is_remote", sa.Boolean(), nullable=True),
        sa.Column("listing_type", sa.String(length=128), nullable=True),
        sa.Column("job_level", sa.String(length=128), nullable=True),
        sa.Column("job_function", sa.String(length=128), nullable=True),
        sa.Column("company_industry", sa.String(length=255), nullable=True),
        sa.Column("company_headquarters", sa.String(length=255), nullable=True),
        sa.Column("company_employees_count", sa.String(length=128), nullable=True),
        sa.Column("emails", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_jobs_id"), "jobs", ["id"], unique=False)
    op.create_index(op.f("ix_jobs_job_url"), "jobs", ["job_url"], unique=True)
    op.create_index(op.f("ix_jobs_company_id"), "jobs", ["company_id"], unique=False)
    op.create_index(op.f("ix_jobs_date_posted"), "jobs", ["date_posted"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_jobs_date_posted"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_company_id"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_job_url"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_id"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_companies_name"), table_name="companies")
    op.drop_index(op.f("ix_companies_linkedin_url"), table_name="companies")
    op.drop_index(op.f("ix_companies_id"), table_name="companies")
    op.drop_table("companies")
