from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    resume_json: str | None = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None


class ResumeUpdate(BaseModel):
    resume_json: str | None = Field(None, description="Resume content in JSON format")

    @field_validator("resume_json")
    @classmethod
    def validate_json(cls, v: str | None) -> str | None:
        """Validate that resume_json is valid JSON if provided."""
        if v is not None and v.strip():
            try:
                json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}")
        return v


class ResumeResponse(BaseModel):
    resume_json: str | None = None

    class Config:
        from_attributes = True

