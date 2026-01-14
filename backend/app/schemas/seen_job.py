from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer


class SeenJobResponse(BaseModel):
    """Schema for seen job response."""
    id: int
    user_id: int
    job_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class MarkAllAsSeenResponse(BaseModel):
    """Schema for mark all as seen response."""
    message: str
    jobs_marked: int
