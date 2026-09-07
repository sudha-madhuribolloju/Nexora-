"""
Assignments router — CRUD, submission, and grading endpoints.
"""
import uuid
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.assignment_service import AssignmentService
from app.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse, AssignmentListResponse,
    SubmissionCreate, SubmissionGrade, SubmissionResponse, SubmissionListResponse,
    GenerateAssignmentRequest, GenerateAssignmentResponse
)

router = APIRouter()


@router.get("/", response_model=AssignmentListResponse, summary="List assignments")
async def list_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    course_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve a paginated list of assignments, optionally filtered by course.
    """
    total, assignments = await AssignmentService.list_assignments(db, skip, limit, course_id)
    return AssignmentListResponse(total=total, skip=skip, limit=limit, data=assignments)


@router.post("/", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED, summary="Create an assignment")
async def create_assignment(
    data: AssignmentCreate,
    teacher_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new assignment for a course.
    """
    return await AssignmentService.create_assignment(db, data, teacher_id)


@router.post("/generate", response_model=GenerateAssignmentResponse, summary="Generate assignment outline & rubric")
async def generate_assignment_ai(
    request: GenerateAssignmentRequest
) -> Any:
    """
    Generate an assignment task outline and grading rubric using AI LLM orchestration.
    """
    from app.services.ai_service import AIService
    reply = await AIService.generate_assignment(topic=request.topic)
    return GenerateAssignmentResponse(reply=reply)


@router.get("/{assignment_id}", response_model=AssignmentResponse, summary="Get assignment by ID")
async def get_assignment(
    assignment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve a specific assignment by its ID.
    """
    return await AssignmentService.get_assignment(db, assignment_id)


@router.put("/{assignment_id}", response_model=AssignmentResponse, summary="Update an assignment")
async def update_assignment(
    assignment_id: uuid.UUID,
    data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update an existing assignment's details or status.
    """
    return await AssignmentService.update_assignment(db, assignment_id, data)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an assignment")
async def delete_assignment(
    assignment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Permanently delete an assignment and all its submissions.
    """
    await AssignmentService.delete_assignment(db, assignment_id)


@router.post("/{assignment_id}/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED, summary="Submit assignment")
async def submit_assignment(
    assignment_id: uuid.UUID,
    data: SubmissionCreate,
    student_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Submit an assignment for a student.
    """
    return await AssignmentService.submit_assignment(db, assignment_id, student_id, data)


@router.get("/{assignment_id}/submissions", response_model=SubmissionListResponse, summary="List submissions")
async def list_submissions(
    assignment_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all student submissions for a specific assignment.
    """
    total, submissions = await AssignmentService.list_submissions(db, assignment_id, skip, limit)
    return SubmissionListResponse(total=total, skip=skip, limit=limit, data=submissions)


@router.put("/{assignment_id}/submissions/{submission_id}/grade", response_model=SubmissionResponse, summary="Grade a submission")
async def grade_submission(
    assignment_id: uuid.UUID,
    submission_id: uuid.UUID,
    data: SubmissionGrade,
    teacher_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Grade a student's assignment submission.
    """
    return await AssignmentService.grade_submission(db, assignment_id, submission_id, data, teacher_id)
