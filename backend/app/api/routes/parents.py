import uuid
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, status, Query, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.parent_service import ParentService
from app.schemas.parent import ParentResponse, ParentCreate, ParentUpdate
from app.utils.helpers import format_response

router = APIRouter()


class ProgressSummaryRequest(BaseModel):
    student_name: str = Field("Alex Mercer", description="Student full name")
    gpa: float = Field(3.85, ge=0.0, le=4.0)
    attendance_pct: float = Field(96.5, ge=0.0, le=100.0)
    recent_quiz_score: float = Field(92.0, ge=0.0, le=100.0)


@router.get("/dashboard/stats", summary="Get Parent Dashboard Statistics")
async def get_parent_dashboard_stats(
    parent_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve statistics for the parent portal dashboard.
    """
    effective_parent_id = parent_id or current_user.id
    stats = await ParentService.get_dashboard_stats(db, effective_parent_id)
    return format_response(status="success", message="Parent stats retrieved", data=stats)


@router.post("/progress-summary", summary="Generate AI Student Progress Summary")
async def generate_progress_summary(
    payload: ProgressSummaryRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Generate an AI progress summary for parents using Gemini AI engine.
    """
    summary_data = await ParentService.generate_progress_summary(
        student_name=payload.student_name,
        gpa=payload.gpa,
        attendance_pct=payload.attendance_pct,
        recent_quiz_score=payload.recent_quiz_score
    )
    return format_response(status="success", message="AI progress summary generated", data=summary_data)


@router.get("/", response_model=Any)
async def get_parents(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    return format_response(status="success", message="Get parents list", data={"parents": []})


@router.get("/{parent_id}", response_model=Any)
async def get_parent(
    parent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    return format_response(status="success", message="Get parent details", data={"parent_id": str(parent_id)})
