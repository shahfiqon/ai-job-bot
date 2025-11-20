from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.schemas.job import JobDetailResponse

JobStatus = Literal["saved", "applied", "interview", "declined"]


class SavedJobCreate(BaseModel):
    """Schema for creating a saved job."""
    job_id: int
    status: JobStatus = Field(default="saved")
    notes: str | None = None


class SavedJobUpdate(BaseModel):
    """Schema for updating a saved job."""
    status: JobStatus | None = None
    notes: str | None = None


class SavedJobResponse(BaseModel):
    """Schema for saved job response."""
    id: int
    user_id: int
    job_id: int
    status: JobStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    job: JobDetailResponse

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class SavedJobListItemResponse(BaseModel):
    """Schema for saved job list item (without full job details)."""
    id: int
    user_id: int
    job_id: int
    status: JobStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class SavedJobListResponse(BaseModel):
    """Schema for paginated saved jobs list."""
    saved_jobs: list[SavedJobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class SavedJobCheckResponse(BaseModel):
    """Schema for checking if a job is saved."""
    is_saved: bool
    saved_job_id: int | None = None
    status: JobStatus | None = None

