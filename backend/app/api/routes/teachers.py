import uuid
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, status, Query, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.teacher_service import TeacherService
from app.schemas.teacher import TeacherResponse, TeacherCreate, TeacherUpdate
from app.utils.helpers import format_response

router = APIRouter()


class GenerateQuizRequest(BaseModel):
    topic: str = Field(..., description="Quiz topic")
    num_questions: int = Field(5, ge=1, le=20)
    difficulty: str = Field("medium", description="easy, medium, or hard")


class GenerateLessonPlanRequest(BaseModel):
    subject: str = Field(..., description="Subject name")
    topic: str = Field(..., description="Lesson topic")
    grade_level: str = Field("Grade 10", description="Target grade level")
    duration_mins: int = Field(60, ge=15, le=180)


class GenerateSummaryRequest(BaseModel):
    text_or_topic: str = Field(..., description="Text content or topic to summarize")


@router.get("/dashboard/stats", summary="Get Teacher Dashboard Statistics")
async def get_dashboard_stats(
    teacher_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve statistics for the teacher dashboard.
    """
    effective_teacher_id = teacher_id or current_user.id
    stats = await TeacherService.get_dashboard_stats(db, effective_teacher_id)
    return format_response(status="success", message="Dashboard stats retrieved", data=stats)


@router.post("/quizzes/generate", summary="Generate AI Quiz")
async def generate_ai_quiz(
    payload: GenerateQuizRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Generate structured AI quiz questions using Gemini AI engine.
    """
    quiz_data = await TeacherService.generate_ai_quiz(
        topic=payload.topic,
        num_questions=payload.num_questions,
        difficulty=payload.difficulty
    )
    return format_response(status="success", message="AI Quiz generated successfully", data=quiz_data)


@router.post("/lesson-plans/generate", summary="Generate AI Lesson Plan")
async def generate_lesson_plan(
    payload: GenerateLessonPlanRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Generate comprehensive teacher lesson plan using Gemini AI engine.
    """
    plan_data = await TeacherService.generate_lesson_plan(
        subject=payload.subject,
        topic=payload.topic,
        grade_level=payload.grade_level,
        duration_mins=payload.duration_mins
    )
    return format_response(status="success", message="AI Lesson Plan generated successfully", data=plan_data)


@router.post("/summaries/generate", summary="Generate AI Summary")
async def generate_summary(
    payload: GenerateSummaryRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Generate concise academic summary using Gemini AI engine.
    """
    summary_data = await TeacherService.generate_summary(payload.text_or_topic)
    return format_response(status="success", message="Summary generated successfully", data=summary_data)


@router.get("/", response_model=Any)
async def get_teachers(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    try:
        result = await db.execute(
            select(User).where(User.is_deleted == False)
        )
        all_users = result.scalars().all()
        teachers = [
            {
                "id": str(u.id),
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "fullName": f"{u.first_name or ''} {u.last_name or ''}".strip() or u.email,
                "role": u.role,
                "department": getattr(u, "department", "General Academics"),
                "voice_print_id": getattr(u, "voice_print_id", "Not registered")
            }
            for u in all_users if u.role and ("teacher" in u.role.lower() or "admin" in u.role.lower())
        ]
        return format_response(status="success", message="Get teachers list", data={"teachers": teachers})
    except Exception as e:
        logger.warning(f"Notice querying teachers: {e}")
        return format_response(status="success", message="Get teachers list", data={"teachers": []})


@router.get("/{teacher_id}", response_model=Any)
async def get_teacher(
    teacher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    return format_response(status="success", message="Get teacher details", data={"teacher_id": str(teacher_id)})
