from __future__ import annotations

import math
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.db import get_db
from app.models.blocked_company import BlockedCompany
from app.models.company import Company
from app.models.job import Job
from app.models.seen_job import SeenJob
from app.models.user import User
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
    # DSPy-parsed filters
    is_python_main: bool | None = Query(
        default=None,
        description="Filter for jobs where Python is the main language",
    ),
    contract_feasible: bool | None = Query(
        default=None,
        description="Filter for jobs that are contract feasible",
    ),
    relocate_required: bool | None = Query(
        default=False,
        description="Filter for jobs that require relocation (default: False to exclude relocate-required jobs)",
    ),
    accepts_non_us: bool | None = Query(
        default=None,
        description="Filter for jobs that accept non-US candidates",
    ),
    screening_required: bool | None = Query(
        default=None,
        description="Filter for jobs that require screening",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
        
        # DSPy-parsed filters
        if is_python_main is not None:
            filters.append(Job.is_python_main == is_python_main)
        if contract_feasible is not None:
            filters.append(Job.contract_feasible == contract_feasible)
        if relocate_required is not None:
            if relocate_required is False:
                # Exclude jobs that require relocation (include False and None)
                filters.append(or_(Job.relocate_required == False, Job.relocate_required.is_(None)))
            else:
                # Include only jobs that require relocation
                filters.append(Job.relocate_required == True)
        if accepts_non_us is not None:
            filters.append(Job.accepts_non_us == accepts_non_us)
        if screening_required is not None:
            filters.append(Job.screening_required == screening_required)
        
        # Company filters - need to join with Company table
        company_filters_needed = (
            has_own_products is not None
            or is_recruiting_company is not None
        )
        
        # Always join Company to get employee size data for display
        # Use inner join if filtering by company fields, outer join otherwise
        if company_filters_needed:
            query = query.join(Company, Job.company_id == Company.id)
            if has_own_products is not None:
                filters.append(Company.has_own_products == has_own_products)
            if is_recruiting_company is not None:
                filters.append(Company.is_recruiting_company == is_recruiting_company)
        else:
            # Outer join to include company data for display, but don't filter out jobs without companies
            query = query.outerjoin(Company, Job.company_id == Company.id)
        
        # Filter out jobs from blocked companies
        # LEFT JOIN blocked_companies to check if company is blocked by current user
        # Only filter if job has a company_id (not NULL)
        query = query.outerjoin(
            BlockedCompany,
            and_(
                BlockedCompany.company_id == Job.company_id,
                BlockedCompany.user_id == current_user.id,
            ),
        )
        # Exclude jobs where blocked_company exists (company is blocked)
        # But include jobs where company_id is NULL (no company to block)
        filters.append(
            or_(
                BlockedCompany.id.is_(None),  # Company not blocked
                Job.company_id.is_(None),  # Job has no company
            )
        )
        
        # Filter out seen jobs
        # LEFT JOIN seen_jobs to check if job has been seen by current user
        query = query.outerjoin(
            SeenJob,
            and_(
                SeenJob.job_id == Job.id,
                SeenJob.user_id == current_user.id,
            ),
        )
        # Exclude jobs where seen_job exists (job has been seen)
        filters.append(SeenJob.id.is_(None))  # Job not seen
        
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
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobDetailResponse:
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
