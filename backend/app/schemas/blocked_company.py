from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.schemas.company import CompanyResponse


class BlockedCompanyCreate(BaseModel):
    """Schema for creating a blocked company."""
    company_id: int


class BlockedCompanyResponse(BaseModel):
    """Schema for blocked company response."""
    id: int
    user_id: int
    company_id: int
    created_at: datetime
    company: CompanyResponse

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class BlockedCompanyListItemResponse(BaseModel):
    """Schema for blocked company list item (without full company details)."""
    id: int
    user_id: int
    company_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class BlockedCompanyListResponse(BaseModel):
    """Schema for paginated blocked companies list."""
    blocked_companies: list[BlockedCompanyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)








