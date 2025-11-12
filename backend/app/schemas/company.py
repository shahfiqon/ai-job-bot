from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer


class CompanyResponse(BaseModel):
    id: int
    linkedin_url: str
    linkedin_internal_id: str | None = None
    name: str
    description: str | None = None
    website: str | None = None
    industry: str | None = None
    company_size_min: int | None = None
    company_size_max: int | None = None
    company_size_on_linkedin: int | None = None
    hq_country: str | None = None
    hq_city: str | None = None
    hq_state: str | None = None
    hq_postal_code: str | None = None
    company_type: str | None = None
    founded_year: int | None = None
    tagline: str | None = None
    universal_name_id: str | None = None
    profile_pic_url: str | None = None
    background_cover_image_url: str | None = None
    specialities: list[str] | None = None
    locations: list[dict[str, Any]] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()

