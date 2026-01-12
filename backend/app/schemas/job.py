from __future__ import annotations

from datetime import date, datetime
from math import ceil
from typing import Sequence

from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.company import CompanyResponse


class JobBaseResponse(BaseModel):
    id: int
    job_url: str | None = None
    job_url_direct: str | None = None
    title: str
    company_name: str | None = None
    company_id: int | None = None
    company_url: str | None = None
    company_url_direct: str | None = None
    location_city: str | None = None
    location_state: str | None = None
    location_country: str | None = None
    compensation_min: float | None = None
    compensation_max: float | None = None
    compensation_currency: str | None = None
    compensation_interval: str | None = None
    job_type: list[str] | None = None
    date_posted: date | None = None
    is_remote: bool | None = None
    listing_type: str | None = None
    job_level: str | None = None
    job_function: str | None = None
    company_industry: str | None = None
    company_headquarters: str | None = None
    company_employees_count: str | None = None
    applicants_count: int | None = None
    # Company employee size fields (from Company model)
    company_size_min: int | None = None
    company_size_max: int | None = None
    company_size_on_linkedin: int | None = None
    emails: list[str] | None = None
    
    # LLM-parsed fields from job description
    required_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    required_years_experience: int | None = None
    required_education: str | None = None
    preferred_education: str | None = None
    responsibilities: list[str] | None = None
    benefits: list[str] | None = None
    work_arrangement: str | None = None
    team_size: str | None = None
    technologies: list[str] | None = None
    culture_keywords: list[str] | None = None
    summary: str | None = None
    job_categories: list[str] | None = None
    independent_contractor_friendly: bool | None = None
    parsed_salary_currency: str | None = None
    parsed_salary_min: float | None = None
    parsed_salary_max: float | None = None
    compensation_basis: str | None = None
    location_restrictions: list[str] | None = None
    exclusive_location_requirement: bool | None = None
    
    # DSPy-parsed fields from job description
    is_python_main: bool | None = None
    contract_feasible: bool | None = None
    relocate_required: bool | None = None
    specific_locations: list[str] | None = None
    accepts_non_us: bool | None = None
    screening_required: bool | None = None
    
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("date_posted", when_used="json")
    def serialize_date(self, value: date | None) -> str | None:
        return value.isoformat() if value else None


class JobListItemResponse(JobBaseResponse):
    pass


class JobResponse(JobBaseResponse):
    description: str | None = None


class JobDetailResponse(JobResponse):
    company: CompanyResponse | None = None


class JobListResponse(BaseModel):
    jobs: list[JobListItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_results(
        cls,
        jobs: Sequence[JobListItemResponse],
        total: int,
        page: int,
        page_size: int,
    ) -> "JobListResponse":
        total_pages = ceil(total / page_size) if total else 0
        return cls(
            jobs=list(jobs),
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
