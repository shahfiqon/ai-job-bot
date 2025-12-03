from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class TailoredResumeResponse(BaseModel):
    """Schema for tailored resume response."""
    id: int
    user_id: int
    job_id: int
    tailored_resume_json: str
    pdf_path: str | None = None
    pdf_generated: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class TailoredResumeListItemResponse(BaseModel):
    """Schema for tailored resume list item with basic job info."""
    id: int
    user_id: int
    job_id: int
    tailored_resume_json: str
    pdf_path: str | None = None
    pdf_generated: bool = False
    created_at: datetime
    updated_at: datetime
    job_title: str | None = None
    company_name: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class TailoredResumeListResponse(BaseModel):
    """Schema for paginated tailored resumes list."""
    tailored_resumes: list[TailoredResumeListItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class TailoredResumeUpdate(BaseModel):
    """Schema for updating a tailored resume."""
    tailored_resume_json: str = Field(..., description="Tailored resume content in JSON format")

    @field_validator("tailored_resume_json")
    @classmethod
    def validate_json(cls, v: str) -> str:
        """Validate that tailored_resume_json is valid JSON."""
        if not v or not v.strip():
            raise ValueError("tailored_resume_json cannot be empty")
        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        return v

