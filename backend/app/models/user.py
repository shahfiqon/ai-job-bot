from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    resume_json = Column(Text, nullable=True)

    saved_jobs = relationship("SavedJob", back_populates="user", cascade="all, delete-orphan")
    blocked_companies = relationship("BlockedCompany", back_populates="user", cascade="all, delete-orphan")
    tailored_resumes = relationship("TailoredResume", back_populates="user", cascade="all, delete-orphan")
    seen_jobs = relationship("SeenJob", back_populates="user", cascade="all, delete-orphan")

