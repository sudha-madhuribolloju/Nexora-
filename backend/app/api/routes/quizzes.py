"""
Quizzes router — CRUD, questions, attempts, and results.
"""
import uuid
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.quiz_service import QuizService
from app.schemas.quiz import (
    QuizCreate, QuizUpdate, QuizResponse, QuizListResponse,
    QuizQuestionCreate, QuizQuestionResponse,
    QuizAttemptResponse, QuizAttemptSubmit, QuizResultResponse,
    GenerateQuizRequest, GenerateQuizResponse
)

router = APIRouter()


@router.get("/", response_model=QuizListResponse, summary="List quizzes")
async def list_quizzes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    course_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve a paginated list of quizzes, optionally filtered by course.
    """
    total, quizzes = await QuizService.list_quizzes(db, skip, limit, course_id)
    return QuizListResponse(total=total, skip=skip, limit=limit, data=quizzes)


@router.post("/", response_model=QuizResponse, status_code=status.HTTP_201_CREATED, summary="Create a quiz")
async def create_quiz(
    data: QuizCreate,
    teacher_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new quiz for a course.
    """
    return await QuizService.create_quiz(db, data, teacher_id)


@router.post("/generate", response_model=GenerateQuizResponse, summary="Generate interactive staged quiz")
async def generate_quiz_ai(
    request: GenerateQuizRequest
) -> Any:
    """
    Generate an interactive multiple-choice quiz using AI LLM orchestration.
    """
    from app.services.ai_service import AIService
    quiz_questions = await AIService.generate_quiz(
        topic=request.topic,
        difficulty=request.difficulty or "Intermediate",
        question_count=request.questionCount or 5
    )
    return GenerateQuizResponse(quiz=quiz_questions)


@router.get("/{quiz_id}", response_model=QuizResponse, summary="Get quiz by ID")
async def get_quiz(
    quiz_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve a specific quiz with its metadata.
    """
    return await QuizService.get_quiz(db, quiz_id)


@router.put("/{quiz_id}", response_model=QuizResponse, summary="Update a quiz")
async def update_quiz(
    quiz_id: uuid.UUID,
    data: QuizUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update quiz settings, timing, or status.
    """
    return await QuizService.update_quiz(db, quiz_id, data)


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a quiz")
async def delete_quiz(
    quiz_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Permanently delete a quiz and all associated data.
    """
    await QuizService.delete_quiz(db, quiz_id)


@router.post("/{quiz_id}/questions", response_model=QuizQuestionResponse, status_code=status.HTTP_201_CREATED, summary="Add a question")
async def add_question(
    quiz_id: uuid.UUID,
    data: QuizQuestionCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a new question (MCQ, True/False, Short Answer, Essay) to a quiz.
    """
    return await QuizService.add_question(db, quiz_id, data)


@router.post("/{quiz_id}/attempt", response_model=QuizAttemptResponse, status_code=status.HTTP_201_CREATED, summary="Start a quiz attempt")
async def start_attempt(
    quiz_id: uuid.UUID,
    student_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Start a new quiz attempt. Validates attempt limits and availability window.
    """
    return await QuizService.start_attempt(db, quiz_id, student_id)


@router.put("/{quiz_id}/attempt/{attempt_id}/submit", response_model=QuizAttemptResponse, summary="Submit a quiz attempt")
async def submit_attempt(
    quiz_id: uuid.UUID,
    attempt_id: uuid.UUID,
    data: QuizAttemptSubmit,
    student_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Submit answers for a quiz attempt. Auto-grades MCQ and True/False questions.
    """
    return await QuizService.submit_attempt(db, quiz_id, attempt_id, student_id, data)


@router.get("/{quiz_id}/results", response_model=QuizResultResponse, summary="Quiz results summary")
async def get_results(
    quiz_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get aggregated results for a quiz: average score, pass rate, highest/lowest scores.
    """
    return await QuizService.get_results(db, quiz_id)
