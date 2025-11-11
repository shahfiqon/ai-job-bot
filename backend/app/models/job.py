from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_url = Column(String(1024), nullable=False, unique=True, index=True)
    job_url_direct = Column(String(1024), nullable=True)
    title = Column(String(512), nullable=False)
    company_name = Column(String(255), nullable=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description = Column(Text, nullable=True)
    company_url = Column(String(1024), nullable=True)
    company_url_direct = Column(String(1024), nullable=True)
    location_city = Column(String(255), nullable=True)
    location_state = Column(String(255), nullable=True)
    location_country = Column(String(255), nullable=True)
    compensation_min = Column(Float, nullable=True)
    compensation_max = Column(Float, nullable=True)
    compensation_currency = Column(String(16), nullable=True, server_default="USD")
    compensation_interval = Column(String(64), nullable=True)
    job_type = Column(JSONB, nullable=True)
    date_posted = Column(Date, nullable=True, index=True)
    is_remote = Column(Boolean, nullable=True)
    listing_type = Column(String(128), nullable=True)
    job_level = Column(String(128), nullable=True)
    job_function = Column(String(128), nullable=True)
    company_industry = Column(String(255), nullable=True)
    company_headquarters = Column(String(255), nullable=True)
    company_employees_count = Column(String(128), nullable=True)
    emails = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    # updated_at relies on ORM-managed onupdate hooks; raw SQL/bulk writes must update this column themselves.
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    company = relationship("Company", back_populates="jobs")
