import uuid
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, status, Query, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.student_service import StudentService
from app.schemas.student import StudentResponse, StudentCreate, StudentUpdate
from app.utils.helpers import format_response

router = APIRouter()


class HomeworkHelpRequest(BaseModel):
    question: str = Field(..., description="Homework question prompt")
    subject: Optional[str] = Field("Physics", description="Academic subject")


@router.get("/dashboard/stats", summary="Get Student Dashboard Statistics")
async def get_student_dashboard_stats(
    student_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve statistics for the student dashboard.
    """
    effective_student_id = student_id or current_user.id
    stats = await StudentService.get_dashboard_stats(db, effective_student_id)
    return format_response(status="success", message="Student stats retrieved", data=stats)


@router.post("/homework-help", summary="AI Homework Assistance")
async def homework_help(
    payload: HomeworkHelpRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Provide step-by-step AI homework explanation using Gemini AI engine.
    """
    help_data = await StudentService.provide_homework_assistance(
        question=payload.question,
        subject=payload.subject
    )
    return format_response(status="success", message="Homework assistance generated", data=help_data)


@router.post("/study-recommendations", summary="AI Study Recommendations")
async def study_recommendations(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Generate personalized AI study recommendations.
    """
    rec_data = await StudentService.generate_study_recommendations(current_user.id)
    return format_response(status="success", message="Study recommendations generated", data=rec_data)


@router.get("/", response_model=Any)
async def get_students(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    return format_response(status="success", message="Get students list", data={"students": []})


@router.get("/{student_id}", response_model=Any)
async def get_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    return format_response(status="success", message="Get student details", data={"student_id": str(student_id)})
