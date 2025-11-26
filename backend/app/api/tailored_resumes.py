from __future__ import annotations

import json
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.db import get_db
from app.models.company import Company
from app.models.job import Job
from app.models.tailored_resume import TailoredResume
from app.models.user import User
from app.schemas import (
    TailoredResumeListItemResponse,
    TailoredResumeListResponse,
    TailoredResumeResponse,
    TailoredResumeUpdate,
)
from app.utils.resume_tailor import tailor_resume_for_job

router = APIRouter(prefix="/api/tailored-resumes", tags=["tailored-resumes"])


@router.post("/generate/{job_id}", response_model=TailoredResumeResponse, status_code=201)
def generate_tailored_resume(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TailoredResumeResponse:
    """Generate a tailored resume for a specific job."""
    try:
        # Validate user has base resume
        if not current_user.resume_json:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No base resume found. Please upload your resume first.",
            )

        # Fetch job and company details
        job = (
            db.query(Job)
            .options(joinedload(Job.company))
            .filter(Job.id == job_id)
            .first()
        )
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )

        # Parse base resume
        try:
            base_resume_dict = json.loads(current_user.resume_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resume JSON format: {exc}",
            ) from exc

        # Generate tailored resume using utility
        company = job.company
        tailored_resume_dict = tailor_resume_for_job(
            resume_dict=base_resume_dict,
            job=job,
            company=company,
        )

        # Convert to JSON string
        tailored_resume_json = json.dumps(tailored_resume_dict, indent=2)

        # Check if tailored resume already exists (for overwrite)
        existing = (
            db.query(TailoredResume)
            .filter(
                TailoredResume.user_id == current_user.id,
                TailoredResume.job_id == job_id,
            )
            .first()
        )

        if existing:
            # Update existing tailored resume
            existing.tailored_resume_json = tailored_resume_json
            db.commit()
            db.refresh(existing)
            return TailoredResumeResponse(
                id=existing.id,
                user_id=existing.user_id,
                job_id=existing.job_id,
                tailored_resume_json=existing.tailored_resume_json,
                created_at=existing.created_at,
                updated_at=existing.updated_at,
            )
        else:
            # Create new tailored resume
            tailored_resume = TailoredResume(
                user_id=current_user.id,
                job_id=job_id,
                tailored_resume_json=tailored_resume_json,
            )
            db.add(tailored_resume)
            db.commit()
            db.refresh(tailored_resume)
            return TailoredResumeResponse(
                id=tailored_resume.id,
                user_id=tailored_resume.user_id,
                job_id=tailored_resume.job_id,
                tailored_resume_json=tailored_resume.tailored_resume_json,
                created_at=tailored_resume.created_at,
                updated_at=tailored_resume.updated_at,
            )

    except HTTPException:
        raise
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Resume tailoring error: {exc}",
        ) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to save tailored resume",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while generating tailored resume",
        ) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error while generating tailored resume: {exc}",
        ) from exc


@router.get("/{job_id}", response_model=TailoredResumeResponse)
def get_tailored_resume(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TailoredResumeResponse:
    """Get tailored resume for a specific job."""
    try:
        tailored_resume = (
            db.query(TailoredResume)
            .filter(
                TailoredResume.user_id == current_user.id,
                TailoredResume.job_id == job_id,
            )
            .first()
        )

        if not tailored_resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tailored resume not found for this job",
            )

        return TailoredResumeResponse(
            id=tailored_resume.id,
            user_id=tailored_resume.user_id,
            job_id=tailored_resume.job_id,
            tailored_resume_json=tailored_resume.tailored_resume_json,
            created_at=tailored_resume.created_at,
            updated_at=tailored_resume.updated_at,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching tailored resume",
        ) from exc


@router.get("", response_model=TailoredResumeListResponse)
def list_tailored_resumes(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TailoredResumeListResponse:
    """List all tailored resumes for the current user with pagination."""
    try:
        query = (
            db.query(TailoredResume)
            .options(joinedload(TailoredResume.job))
            .filter(TailoredResume.user_id == current_user.id)
        )

        # Get total count
        total = query.count()
        offset = (page - 1) * page_size

        # Get paginated results
        tailored_resumes = (
            query.order_by(TailoredResume.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        # Convert to response
        tailored_resumes_response = []
        for tailored_resume in tailored_resumes:
            job = tailored_resume.job
            tailored_resumes_response.append(
                TailoredResumeListItemResponse(
                    id=tailored_resume.id,
                    user_id=tailored_resume.user_id,
                    job_id=tailored_resume.job_id,
                    tailored_resume_json=tailored_resume.tailored_resume_json,
                    created_at=tailored_resume.created_at,
                    updated_at=tailored_resume.updated_at,
                    job_title=job.title if job else None,
                    company_name=job.company_name if job else None,
                )
            )

        total_pages = math.ceil(total / page_size) if total else 0

        return TailoredResumeListResponse(
            tailored_resumes=tailored_resumes_response,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching tailored resumes",
        ) from exc


@router.put("/{job_id}", response_model=TailoredResumeResponse)
def update_tailored_resume(
    job_id: int,
    tailored_resume_update: TailoredResumeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TailoredResumeResponse:
    """Update tailored resume for a specific job."""
    try:
        tailored_resume = (
            db.query(TailoredResume)
            .filter(
                TailoredResume.user_id == current_user.id,
                TailoredResume.job_id == job_id,
            )
            .first()
        )

        if not tailored_resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tailored resume not found for this job",
            )

        # Update the tailored resume JSON
        tailored_resume.tailored_resume_json = tailored_resume_update.tailored_resume_json
        db.commit()
        db.refresh(tailored_resume)

        return TailoredResumeResponse(
            id=tailored_resume.id,
            user_id=tailored_resume.user_id,
            job_id=tailored_resume.job_id,
            tailored_resume_json=tailored_resume.tailored_resume_json,
            created_at=tailored_resume.created_at,
            updated_at=tailored_resume.updated_at,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating tailored resume",
        ) from exc

