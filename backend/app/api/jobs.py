from __future__ import annotations

import math
from datetime import date

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
    min_employee_size: int | None = Query(
        default=None,
        ge=0,
        description="Minimum company employee size (from company_size_on_linkedin, company_size_min, or company_size_max)",
    ),
    max_employee_size: int | None = Query(
        default=None,
        ge=0,
        description="Maximum company employee size (from company_size_on_linkedin, company_size_min, or company_size_max)",
    ),
    min_applicants_count: int | None = Query(
        default=None,
        ge=0,
        description="Minimum number of applicants",
    ),
    max_applicants_count: int | None = Query(
        default=None,
        ge=0,
        description="Maximum number of applicants",
    ),
    date_posted_from: date | None = Query(
        default=None,
        description="Filter jobs posted on or after this date (YYYY-MM-DD)",
    ),
    date_posted_to: date | None = Query(
        default=None,
        description="Filter jobs posted on or before this date (YYYY-MM-DD)",
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
        
        # Applicants count filters
        if min_applicants_count is not None:
            filters.append(Job.applicants_count >= min_applicants_count)
        if max_applicants_count is not None:
            filters.append(Job.applicants_count <= max_applicants_count)
        
        # Date posted filters
        if date_posted_from is not None:
            filters.append(Job.date_posted >= date_posted_from)
        if date_posted_to is not None:
            filters.append(Job.date_posted <= date_posted_to)
        
        # Company filters - need to join with Company table
        company_filters_needed = (
            has_own_products is not None
            or is_recruiting_company is not None
            or min_employee_size is not None
            or max_employee_size is not None
        )
        
        # Always join Company to get employee size data for display
        # Use inner join if filtering by company fields, outer join otherwise
        if company_filters_needed:
            query = query.join(Company, Job.company_id == Company.id)
            if has_own_products is not None:
                filters.append(Company.has_own_products == has_own_products)
            if is_recruiting_company is not None:
                filters.append(Company.is_recruiting_company == is_recruiting_company)
            
            # Employee size filtering - check against company_size_on_linkedin, company_size_min, or company_size_max
            if min_employee_size is not None or max_employee_size is not None:
                employee_size_filters = []
                # Use company_size_on_linkedin as primary, fallback to company_size_min/max
                # For filtering: check if company size overlaps with the requested range
                if min_employee_size is not None:
                    # Company size should be >= min_employee_size
                    # Check: company_size_on_linkedin >= min OR (company_size_max >= min if company_size_on_linkedin is NULL)
                    employee_size_filters.append(
                        or_(
                            Company.company_size_on_linkedin >= min_employee_size,
                            and_(
                                Company.company_size_on_linkedin.is_(None),
                                Company.company_size_max >= min_employee_size,
                            ),
                            and_(
                                Company.company_size_on_linkedin.is_(None),
                                Company.company_size_max.is_(None),
                                Company.company_size_min >= min_employee_size,
                            ),
                        )
                    )
                if max_employee_size is not None:
                    # Company size should be <= max_employee_size
                    # Check: company_size_on_linkedin <= max OR (company_size_min <= max if company_size_on_linkedin is NULL)
                    employee_size_filters.append(
                        or_(
                            Company.company_size_on_linkedin <= max_employee_size,
                            and_(
                                Company.company_size_on_linkedin.is_(None),
                                Company.company_size_min <= max_employee_size,
                            ),
                            and_(
                                Company.company_size_on_linkedin.is_(None),
                                Company.company_size_min.is_(None),
                                Company.company_size_max <= max_employee_size,
                            ),
                        )
                    )
                if employee_size_filters:
                    filters.append(and_(*employee_size_filters))
        else:
            # Outer join to include company data for display, but don't filter out jobs without companies
            query = query.outerjoin(Company, Job.company_id == Company.id)
        
        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count
        total = query.with_entities(func.count(Job.id)).scalar() or 0
        offset = (page - 1) * page_size

        # Get paginated results - Company is already joined (inner or outer)
        jobs = (
            query
            .options(joinedload(Job.company))
            .order_by(
                Job.date_posted.desc().nulls_last(),
                Job.created_at.desc(),
            )
            .offset(offset)
            .limit(page_size)
            .all()
        )

        # Map jobs to response, including company employee size fields
        jobs_response = []
        for job in jobs:
            job_dict = JobListItemResponse.model_validate(job).model_dump()
            if job.company:
                job_dict["company_size_min"] = job.company.company_size_min
                job_dict["company_size_max"] = job.company.company_size_max
                job_dict["company_size_on_linkedin"] = job.company.company_size_on_linkedin
            jobs_response.append(JobListItemResponse(**job_dict))
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
