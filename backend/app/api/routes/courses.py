"""
Courses router — full CRUD + enrollment management.
"""
import uuid
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.course_service import CourseService
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse,
    EnrollmentCreate, EnrollmentResponse,
)

router = APIRouter()


@router.get("/", response_model=CourseListResponse, summary="List all courses")
async def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    teacher_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve a paginated list of courses. Optionally filter by active status or teacher.
    """
    total, courses = await CourseService.list_courses(db, skip, limit, is_active, teacher_id)
    return CourseListResponse(total=total, skip=skip, limit=limit, data=courses)


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED, summary="Create a course")
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new course.
    """
    return await CourseService.create_course(db, data)


@router.get("/{course_id}", response_model=CourseResponse, summary="Get course by ID")
async def get_course(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get details of a specific course.
    """
    return await CourseService.get_course(db, course_id)


@router.put("/{course_id}", response_model=CourseResponse, summary="Update a course")
async def update_course(
    course_id: uuid.UUID,
    data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update an existing course's details.
    """
    return await CourseService.update_course(db, course_id, data)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a course")
async def delete_course(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Permanently delete a course and all related data.
    """
    await CourseService.delete_course(db, course_id)


@router.post("/{course_id}/enroll", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED, summary="Enroll a student")
async def enroll_student(
    course_id: uuid.UUID,
    data: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Enroll a student into the specified course.
    """
    return await CourseService.enroll_student(db, course_id, data)


@router.delete("/{course_id}/enroll/{student_id}", status_code=status.HTTP_200_OK, summary="Unenroll a student")
async def unenroll_student(
    course_id: uuid.UUID,
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Unenroll a student from the specified course (soft delete).
    """
    await CourseService.unenroll_student(db, course_id, student_id)
    return {"status": "success", "message": "Student unenrolled successfully"}


@router.get("/{course_id}/students", summary="List enrolled students")
async def get_course_students(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all students enrolled in the specified course.
    """
    enrollments = await CourseService.get_enrolled_students(db, course_id)
    return {"status": "success", "data": [{"student_id": str(e.student_id), "created_at": e.created_at} for e in enrollments]}
