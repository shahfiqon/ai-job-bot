from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.db import get_db
from app.models.blocked_company import BlockedCompany
from app.models.company import Company
from app.models.user import User
from app.schemas import (
    BlockedCompanyCreate,
    BlockedCompanyListResponse,
    BlockedCompanyResponse,
    CompanyResponse,
)

router = APIRouter(prefix="/api/blocked-companies", tags=["blocked-companies"])


@router.post("", response_model=BlockedCompanyResponse, status_code=201)
def block_company(
    blocked_company_data: BlockedCompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BlockedCompanyResponse:
    """Block a company for the current user."""
    try:
        # Check if company exists
        company = db.query(Company).filter(Company.id == blocked_company_data.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Check if already blocked
        existing = (
            db.query(BlockedCompany)
            .filter(
                BlockedCompany.user_id == current_user.id,
                BlockedCompany.company_id == blocked_company_data.company_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400, detail="Company is already blocked by this user"
            )

        # Create blocked company
        blocked_company = BlockedCompany(
            user_id=current_user.id,
            company_id=blocked_company_data.company_id,
        )
        db.add(blocked_company)
        db.commit()
        db.refresh(blocked_company)

        # Load company details
        blocked_company = (
            db.query(BlockedCompany)
            .options(joinedload(BlockedCompany.company))
            .filter(BlockedCompany.id == blocked_company.id)
            .first()
        )

        # Convert to response
        company_detail = CompanyResponse.model_validate(blocked_company.company)
        return BlockedCompanyResponse(
            id=blocked_company.id,
            user_id=blocked_company.user_id,
            company_id=blocked_company.company_id,
            created_at=blocked_company.created_at,
            company=company_detail,
        )
    except HTTPException:
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to block company") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error while blocking company"
        ) from exc


@router.get("", response_model=BlockedCompanyListResponse)
def list_blocked_companies(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BlockedCompanyListResponse:
    """List blocked companies for the current user with pagination."""
    try:
        query = (
            db.query(BlockedCompany)
            .options(joinedload(BlockedCompany.company))
            .filter(BlockedCompany.user_id == current_user.id)
        )

        # Get total count
        total = query.count()
        offset = (page - 1) * page_size

        # Get paginated results
        blocked_companies = (
            query.order_by(BlockedCompany.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        # Convert to response
        blocked_companies_response = []
        for blocked_company in blocked_companies:
            company_detail = CompanyResponse.model_validate(blocked_company.company)
            blocked_companies_response.append(
                BlockedCompanyResponse(
                    id=blocked_company.id,
                    user_id=blocked_company.user_id,
                    company_id=blocked_company.company_id,
                    created_at=blocked_company.created_at,
                    company=company_detail,
                )
            )

        total_pages = math.ceil(total / page_size) if total else 0

        return BlockedCompanyListResponse(
            blocked_companies=blocked_companies_response,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500, detail="Database error while fetching blocked companies"
        ) from exc


@router.delete("/{company_id}", status_code=204)
def unblock_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Unblock a company for the current user."""
    try:
        blocked_company = (
            db.query(BlockedCompany)
            .filter(
                BlockedCompany.user_id == current_user.id,
                BlockedCompany.company_id == company_id,
            )
            .first()
        )

        if not blocked_company:
            raise HTTPException(
                status_code=404, detail="Blocked company not found"
            )

        db.delete(blocked_company)
        db.commit()
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error while unblocking company"
        ) from exc

