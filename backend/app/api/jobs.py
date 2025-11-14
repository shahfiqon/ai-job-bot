from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.models.company import Company
from app.models.job import Job
from app.schemas import JobDetailResponse, JobListItemResponse, JobListResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get(
    "/",
    response_model=JobListResponse,
)
def list_jobs(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page",
    ),
    job_categories: str | None = Query(
        default=None,
        description="Comma-separated list of job categories to filter by",
    ),
    technologies: str | None = Query(
        default=None,
        description="Comma-separated list of technologies to filter by (partial match)",
    ),
    required_skills: str | None = Query(
        default=None,
        description="Comma-separated list of required skills to filter by (partial match)",
    ),
    work_arrangement: str | None = Query(
        default=None,
        description="Work arrangement filter (Remote, Hybrid, On-site)",
    ),
    min_years_experience: int | None = Query(
        default=None,
        ge=0,
        description="Minimum years of experience required",
    ),
    independent_contractor_friendly: bool | None = Query(
        default=None,
        description="Filter for independent contractor friendly positions",
    ),
    has_own_products: bool | None = Query(
        default=None,
        description="Filter by whether the company has its own products",
    ),
    is_recruiting_company: bool | None = Query(
        default=None,
        description="Filter by whether the company is a recruiting company",
    ),
    db: Session = Depends(get_db),
) -> JobListResponse:
    """Return a paginated list of jobs ordered by most recent posting with optional filters."""
    try:
        # Build base query
        query = db.query(Job)
        
        # Apply filters
        filters = []
        
        if job_categories:
            categories_list = [cat.strip() for cat in job_categories.split(",") if cat.strip()]
            if categories_list:
                # Check if any of the requested categories exist in the job_categories JSONB array
                category_filters = [
                    Job.job_categories.contains([category]) for category in categories_list
                ]
                filters.append(or_(*category_filters))
        
        if technologies:
            tech_list = [tech.strip() for tech in technologies.split(",") if tech.strip()]
            if tech_list:
                # Check if any of the requested technologies exist in the technologies JSONB array
                tech_filters = [
                    Job.technologies.contains([tech]) for tech in tech_list
                ]
                filters.append(or_(*tech_filters))
        
        if required_skills:
            skills_list = [skill.strip() for skill in required_skills.split(",") if skill.strip()]
            if skills_list:
                # Check if any of the requested skills exist in required_skills JSONB array
                skill_filters = [
                    Job.required_skills.contains([skill]) for skill in skills_list
                ]
                filters.append(or_(*skill_filters))
        
        if work_arrangement:
            filters.append(Job.work_arrangement == work_arrangement)
        
        if min_years_experience is not None:
            filters.append(Job.required_years_experience >= min_years_experience)
        
        if independent_contractor_friendly is not None:
            filters.append(Job.independent_contractor_friendly == independent_contractor_friendly)
        
        # Company filters - need to join with Company table
        if has_own_products is not None or is_recruiting_company is not None:
            query = query.join(Company, Job.company_id == Company.id)
            if has_own_products is not None:
                filters.append(Company.has_own_products == has_own_products)
            if is_recruiting_company is not None:
                filters.append(Company.is_recruiting_company == is_recruiting_company)
        
        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count
        total = query.with_entities(func.count(Job.id)).scalar() or 0
        offset = (page - 1) * page_size

        # Get paginated results
        jobs = (
            query
            .order_by(
                Job.date_posted.desc().nulls_last(),
                Job.created_at.desc(),
            )
            .offset(offset)
            .limit(page_size)
            .all()
        )

        jobs_response = [JobListItemResponse.model_validate(job) for job in jobs]
        total_pages = math.ceil(total / page_size) if total else 0

        return JobListResponse(
            jobs=jobs_response,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch jobs",
        ) from exc


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
)
def get_job(job_id: int, db: Session = Depends(get_db)) -> JobDetailResponse:
    """Return detailed information for a job, including company data."""
    try:
        job = (
            db.query(Job)
            .options(joinedload(Job.company))
            .filter(Job.id == job_id)
            .first()
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch job",
        ) from exc

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job with id {job_id} not found",
        )

    return JobDetailResponse.model_validate(job)
