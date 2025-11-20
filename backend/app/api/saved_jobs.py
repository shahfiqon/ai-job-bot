from __future__ import annotations

import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.db import get_db
from app.models.job import Job
from app.models.saved_job import SavedJob
from app.models.user import User
from app.schemas import (
    JobDetailResponse,
    SavedJobCheckResponse,
    SavedJobCreate,
    SavedJobListResponse,
    SavedJobResponse,
    SavedJobUpdate,
)

router = APIRouter(prefix="/api/saved-jobs", tags=["saved-jobs"])


@router.post("", response_model=SavedJobResponse, status_code=201)
def save_job(
    saved_job_data: SavedJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedJobResponse:
    """Save a job for the current user."""
    try:
        # Check if job exists
        job = db.query(Job).filter(Job.id == saved_job_data.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if already saved
        existing = (
            db.query(SavedJob)
            .filter(
                SavedJob.user_id == current_user.id,
                SavedJob.job_id == saved_job_data.job_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400, detail="Job is already saved by this user"
            )

        # Create saved job
        saved_job = SavedJob(
            user_id=current_user.id,
            job_id=saved_job_data.job_id,
            status=saved_job_data.status,
            notes=saved_job_data.notes,
        )
        db.add(saved_job)
        db.commit()
        db.refresh(saved_job)

        # Load job details
        saved_job = (
            db.query(SavedJob)
            .options(joinedload(SavedJob.job).joinedload(Job.company))
            .filter(SavedJob.id == saved_job.id)
            .first()
        )

        # Convert to response
        job_detail = JobDetailResponse.model_validate(saved_job.job)
        return SavedJobResponse(
            id=saved_job.id,
            user_id=saved_job.user_id,
            job_id=saved_job.job_id,
            status=saved_job.status,
            notes=saved_job.notes,
            created_at=saved_job.created_at,
            updated_at=saved_job.updated_at,
            job=job_detail,
        )
    except HTTPException:
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to save job") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error while saving job"
        ) from exc


@router.get("", response_model=SavedJobListResponse)
def list_saved_jobs(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page",
    ),
    status: Literal["saved", "applied", "interview", "declined"] | None = Query(
        default=None,
        description="Filter by status",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedJobListResponse:
    """List saved jobs for the current user with pagination and optional status filter."""
    try:
        query = (
            db.query(SavedJob)
            .options(joinedload(SavedJob.job).joinedload(Job.company))
            .filter(SavedJob.user_id == current_user.id)
        )

        # Apply status filter if provided
        if status:
            query = query.filter(SavedJob.status == status)

        # Get total count
        total = query.count()
        offset = (page - 1) * page_size

        # Get paginated results
        saved_jobs = (
            query.order_by(SavedJob.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        # Convert to response
        saved_jobs_response = []
        for saved_job in saved_jobs:
            job_detail = JobDetailResponse.model_validate(saved_job.job)
            saved_jobs_response.append(
                SavedJobResponse(
                    id=saved_job.id,
                    user_id=saved_job.user_id,
                    job_id=saved_job.job_id,
                    status=saved_job.status,
                    notes=saved_job.notes,
                    created_at=saved_job.created_at,
                    updated_at=saved_job.updated_at,
                    job=job_detail,
                )
            )

        total_pages = math.ceil(total / page_size) if total else 0

        return SavedJobListResponse(
            saved_jobs=saved_jobs_response,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500, detail="Database error while fetching saved jobs"
        ) from exc


@router.get("/{saved_job_id}", response_model=SavedJobResponse)
def get_saved_job(
    saved_job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedJobResponse:
    """Get a specific saved job by ID."""
    try:
        saved_job = (
            db.query(SavedJob)
            .options(joinedload(SavedJob.job).joinedload(Job.company))
            .filter(
                SavedJob.id == saved_job_id,
                SavedJob.user_id == current_user.id,
            )
            .first()
        )

        if not saved_job:
            raise HTTPException(
                status_code=404, detail="Saved job not found"
            )

        job_detail = JobDetailResponse.model_validate(saved_job.job)
        return SavedJobResponse(
            id=saved_job.id,
            user_id=saved_job.user_id,
            job_id=saved_job.job_id,
            status=saved_job.status,
            notes=saved_job.notes,
            created_at=saved_job.created_at,
            updated_at=saved_job.updated_at,
            job=job_detail,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500, detail="Database error while fetching saved job"
        ) from exc


@router.patch("/{saved_job_id}", response_model=SavedJobResponse)
def update_saved_job(
    saved_job_id: int,
    saved_job_update: SavedJobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedJobResponse:
    """Update a saved job's status and/or notes."""
    try:
        saved_job = (
            db.query(SavedJob)
            .filter(
                SavedJob.id == saved_job_id,
                SavedJob.user_id == current_user.id,
            )
            .first()
        )

        if not saved_job:
            raise HTTPException(
                status_code=404, detail="Saved job not found"
            )

        # Update fields if provided
        if saved_job_update.status is not None:
            saved_job.status = saved_job_update.status
        if saved_job_update.notes is not None:
            saved_job.notes = saved_job_update.notes

        db.commit()
        db.refresh(saved_job)

        # Reload with job details
        saved_job = (
            db.query(SavedJob)
            .options(joinedload(SavedJob.job).joinedload(Job.company))
            .filter(SavedJob.id == saved_job.id)
            .first()
        )

        job_detail = JobDetailResponse.model_validate(saved_job.job)
        return SavedJobResponse(
            id=saved_job.id,
            user_id=saved_job.user_id,
            job_id=saved_job.job_id,
            status=saved_job.status,
            notes=saved_job.notes,
            created_at=saved_job.created_at,
            updated_at=saved_job.updated_at,
            job=job_detail,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error while updating saved job"
        ) from exc


@router.delete("/{saved_job_id}", status_code=204)
def delete_saved_job(
    saved_job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove a saved job."""
    try:
        saved_job = (
            db.query(SavedJob)
            .filter(
                SavedJob.id == saved_job_id,
                SavedJob.user_id == current_user.id,
            )
            .first()
        )

        if not saved_job:
            raise HTTPException(
                status_code=404, detail="Saved job not found"
            )

        db.delete(saved_job)
        db.commit()
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error while deleting saved job"
        ) from exc


@router.get("/jobs/{job_id}/saved", response_model=SavedJobCheckResponse)
def check_job_saved(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedJobCheckResponse:
    """Check if a job is saved by the current user."""
    try:
        saved_job = (
            db.query(SavedJob)
            .filter(
                SavedJob.user_id == current_user.id,
                SavedJob.job_id == job_id,
            )
            .first()
        )

        if saved_job:
            return SavedJobCheckResponse(
                is_saved=True,
                saved_job_id=saved_job.id,
                status=saved_job.status,
            )
        else:
            return SavedJobCheckResponse(
                is_saved=False,
                saved_job_id=None,
                status=None,
            )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500, detail="Database error while checking saved job"
        ) from exc

