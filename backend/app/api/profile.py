from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models.user import User
from app.schemas import ResumeResponse, ResumeUpdate

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/resume", response_model=ResumeResponse)
def get_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    """Get current user's resume JSON."""
    try:
        return ResumeResponse(resume_json=current_user.resume_json)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching resume",
        ) from exc


@router.put("/resume", response_model=ResumeResponse)
def update_resume(
    resume_update: ResumeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    """Update current user's resume JSON."""
    try:
        current_user.resume_json = resume_update.resume_json
        db.commit()
        db.refresh(current_user)
        return ResumeResponse(resume_json=current_user.resume_json)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating resume",
        ) from exc


