from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    linkedin_url = Column(String(512), nullable=False, unique=True, index=True)
    linkedin_internal_id = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    website = Column(String(512), nullable=True)
    industry = Column(String(255), nullable=True)
    company_size_min = Column(Integer, nullable=True)
    company_size_max = Column(Integer, nullable=True)
    company_size_on_linkedin = Column(Integer, nullable=True)
    hq_country = Column(String(128), nullable=True)
    hq_city = Column(String(128), nullable=True)
    hq_state = Column(String(128), nullable=True)
    hq_postal_code = Column(String(64), nullable=True)
    company_type = Column(String(128), nullable=True)
    founded_year = Column(Integer, nullable=True)
    tagline = Column(String(255), nullable=True)
    universal_name_id = Column(String(255), nullable=True)
    profile_pic_url = Column(String(1024), nullable=True)
    background_cover_image_url = Column(String(1024), nullable=True)
    specialities = Column(JSONB, nullable=True)
    locations = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    # updated_at only auto-updates when SQLAlchemy ORM flushes this model; raw SQL must set it explicitly.
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    jobs = relationship(
        "Job",
        back_populates="company",
        passive_deletes=True,
    )
