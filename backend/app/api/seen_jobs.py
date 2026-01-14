from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import exists, insert, literal, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models.job import Job
from app.models.seen_job import SeenJob
from app.models.user import User
from app.schemas import MarkAllAsSeenResponse

router = APIRouter(prefix="/api/seen-jobs", tags=["seen-jobs"])


@router.post("/mark-all-as-seen", response_model=MarkAllAsSeenResponse)
def mark_all_as_seen(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MarkAllAsSeenResponse:
    """Mark all unseen jobs as seen for the current user."""
    try:
        # Use INSERT ... SELECT to insert all unseen jobs in a single atomic operation
        # This is Option 3 - the fastest approach
        # Select all job IDs that don't exist in seen_jobs for this user
        # The EXISTS clause correlates Job.id with SeenJob.job_id
        unseen_jobs_query = (
            select(
                literal(current_user.id).label('user_id'),
                Job.id.label('job_id')
            )
            .where(
                ~exists(
                    select(SeenJob.job_id)
                    .where(
                        SeenJob.user_id == current_user.id,
                        SeenJob.job_id == Job.id
                    )
                )
            )
        )
        
        result = db.execute(
            insert(SeenJob).from_select(
                ['user_id', 'job_id'],
                unseen_jobs_query
            )
        )
        
        db.commit()
        
        # Get the number of rows inserted
        jobs_marked = result.rowcount if result.rowcount is not None else 0
        
        return MarkAllAsSeenResponse(
            message="All unseen jobs have been marked as seen",
            jobs_marked=jobs_marked,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to mark jobs as seen",
        ) from exc
