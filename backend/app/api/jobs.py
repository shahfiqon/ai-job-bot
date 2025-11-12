from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
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
    db: Session = Depends(get_db),
) -> JobListResponse:
    """Return a paginated list of jobs ordered by most recent posting."""
    try:
        total = db.query(func.count(Job.id)).scalar() or 0
        offset = (page - 1) * page_size

        jobs = (
            db.query(Job)
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
